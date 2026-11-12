---
name: al-profiler
description: >-
  Profile a slow Business Central session (CPU samples, SQL and HTTP time, session memory) and explain where the time goes in AL. Use when the user says a page, posting, report, or process is slow in BC and wants to know why, or has .alcpuprofile files to analyze. Opt-in: needs the al-profiling MCP server added by the user.
---

# AL Performance Profiling (al-profiler)

Explain why a Business Central session is slow from real profiles. Read-only toward code:
report the hot spots and hand fixes to **al-developer**. This skill is outside the
analyst → developer → reviewer pipeline; those skills never call it.

## Prerequisite — the `al-profiling` MCP server
Load its tools with ToolSearch
(`select:schedule_profiling,stop_schedule_and_get_profiles,get_profile_for_activity,analyze_profiles_in_folder`).
If they don't exist, stop and tell the user to add the server once (README section
"Opt-in: snapshot debugging and profiling"):

```powershell
claude mcp add al-profiling -e AL_ENV_TYPE=Sandbox -e AL_ENV_NAME=<environment> -- "<plugin root>\scripts\al-diag-mcp.cmd" profiling
```

Profiles the user already has (`.alcpuprofile` or a `.zip` of them) need no environment:
`analyze_profiles_in_folder` reads the proxy's local `user` folder.

## Before arming — confirm with the user
- **Environment** (`AL_ENV_TYPE` / `AL_ENV_NAME`); for **Production**, explicit consent
  for this session.
- **Session ID** of the slow session (the user can see it in Business Central).
- **Window** — default 300 s, max 3600 s; keep it as short as the repro allows.

## Workflow
1. `schedule_profiling` with `targetSessionId`. Keep `scheduleId` and the session ID.
2. Relay the returned next step verbatim: the user exercises the slow scenario during the
   window. Don't poll; note when the window ends.
3. After the window (or when the user says so), `stop_schedule_and_get_profiles` with
   the session ID and `scheduleId`. **Always collect** — also when the repro went wrong —
   so the schedule is disabled.
4. Analyze with **Python** (`python`, standard library: `base64`, `zipfile`, `json`):
   decode the archive, aggregate self/total time per call frame, and read the activity
   overview (durations, SQL count/time, HTTP count/time). Never load raw profile JSON
   into context. Use `get_profile_for_activity` to drill into one activity.
5. Judge the hot AL code against `${CLAUDE_PLUGIN_ROOT}/references/al-rules.md`
   (SetLoadFields, filters before FindSet, CalcSums, subscriber cost) and Microsoft's
   BC performance patterns (https://github.com/microsoft/BCQuality). Report session
   memory (`totalMemoryUsed`) in KiB/MiB/GiB when present.

## Data handling
- Profiles are saved locally (default `%TEMP%\bc-profiling`) and can contain business
  data. Don't copy them into the repository; tell the user where they are and that the
  proxy never deletes the `user` folder.

## Output
```markdown
# Profile: <scenario>
## Environment — type/name, session, window, activities captured
## Where the time goes — top functions (self/total ms), SQL and HTTP share, memory
## Root causes — each hot spot → AL pattern at fault (object, procedure)
## Fix direction — ordered by expected gain, for al-developer (no code here)
## Schedule closed — stop_schedule_and_get_profiles called: yes/no
```
