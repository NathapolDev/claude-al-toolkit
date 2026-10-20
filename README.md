# al-toolkit

A Claude Code plugin marketplace for Microsoft Dynamics 365 Business Central AL
development. It gives Claude Code a real AL toolchain plus a three-stage skill pipeline
that takes a requirement from analysis → implementation → review, with a verified compile
at every stage that produces code.

| Component | What it does |
|---|---|
| **`al` MCP server** | Launches Microsoft's AL MCP server (`altool.exe launchmcpserver`) from the standalone AL Development Tools .NET tool or the AL Language VS Code extension. Gives Claude `al_compile`, `al_getdiagnostics`, `al_symbolsearch`, `al_downloadsymbols`, `al_build`, `al_publish`, `al_run_tests`. Resolves the toolchain at every launch, so tool/extension updates never break it. |
| **`al-build.cmd`** | Bundled `alc.exe` build fallback, used when the MCP server isn't connected — so every machine has a real build path. |
| **`al-analyst`** skill | Analyze a requirement → Solution Design comparing options. Read-only, writes no code. |
| **`al-developer`** skill | Implement AL code, build until zero diagnostics. |
| **`al-reviewer`** skill | Review AL code, independently re-verify the build, Approve / Request Changes. Read-only, edits nothing. |
| **`references/al-rules.md`** | Canonical AL house rules all three skills defer to. |

---

## 1. Prerequisites (every machine)

The AL toolchain is **not** shipped inside this plugin — `altool.exe` and `alc.exe` are
Microsoft's binaries. Each machine needs:

- **Windows.** The launchers are `.cmd`.
- **One AL toolchain** — either works; the .NET tool needs no VS Code:
  - **AL Development Tools .NET tool** (recommended):
    `dotnet tool install -g Microsoft.Dynamics.BusinessCentral.Development.Tools`
    (add `--prerelease` for the newest beta). Needs the .NET 10 **or** .NET 8 ASP.NET Core
    runtime; the resolver picks the build whose runtime is installed.
  - **VS Code** with the **AL Language** extension (`ms-dynamics-smb.al-*`, normally under
    `%USERPROFILE%\.vscode\extensions`; binaries in `bin\` on AL 18+, `bin\win32` before).
- **Claude Code**, started from inside the AL project folder — `altool` needs a project
  path to resolve symbols against.

Without either toolchain, neither the `al` MCP server nor `al-build.cmd` can run. The
three skills still work, but they will report the build as **NOT VERIFIED** rather than
assume the code compiles.

### Non-default VS Code locations

Both scripts resolve the toolchain through `scripts/find-al-bin.cmd`, which searches in
order: `%AL_BIN%` → `%AL_EXTENSIONS_DIR%` → AL Development Tools .NET global tool →
`%VSCODE_EXTENSIONS%` → VS Code stable / Insiders / Server / OSS user extension roots →
portable and Program Files installs. Within a root, the newest `ms-dynamics-smb.al-*`
folder wins.

If a machine keeps extensions somewhere unusual, set one environment variable — no script
edits needed:

```powershell
# point straight at the folder holding altool.exe / alc.exe
setx AL_BIN "D:\tools\al\bin"

# or point at the extensions root and let the script pick the newest AL version
setx AL_EXTENSIONS_DIR "D:\vscode-extensions"
```

| Variable | Purpose | Default |
|---|---|---|
| `AL_BIN` | Folder containing `altool.exe` / `alc.exe` | auto-resolved |
| `AL_EXTENSIONS_DIR` | VS Code extensions root | auto-resolved |
| `AL_PROJECT_DIR` | Project handed to the MCP server | folder Claude Code started in |
| `AL_PACKAGECACHE` | Symbol folder for `al-build.cmd` | `<project>\.alpackages` |
| `AL_ANALYZERS` | Semicolon list of cops for `al-build.cmd` | none |

---

## 2. Install

### Option A — from a git repository (recommended)

1. Push this folder to a private git repo (GitHub, Azure DevOps, GitLab, …).
2. On the target machine, inside Claude Code:

```
/plugin marketplace add <git-url-or-owner/repo>
/plugin install al-toolkit@al-toolkit-marketplace
/reload-plugins
```

### Option B — from a local folder or network share

Copy the whole `claude-al-toolkit` folder to the target machine (USB, share, `robocopy`),
then:

```
/plugin marketplace add "\\server\share\claude-al-toolkit"
/plugin install al-toolkit@al-toolkit-marketplace
/reload-plugins
```

A local path also works for testing before distributing:

```
/plugin marketplace add "C:\BPC BC Project\claude-al-toolkit"
```

### Verify the install

```
claude mcp list          # must list `al`
```

Then in Claude Code, `/al-toolkit:al-analyst` should appear. If `al_*` tools are missing,
check that the AL Language extension is installed and that Claude Code was started from
the AL project folder.

---

## 3. Using the skills

The three skills are a deliberate pipeline — each one's output is the next one's input:

```
requirement ──▶ al-analyst ──▶ Solution Design ──▶ al-developer ──▶ code + green build ──▶ al-reviewer ──▶ Approve / Request Changes
                                                        ▲                                              │
                                                        └──────────── fix list on Request Changes ─────┘
```

Invoke a skill in either way:

- **Explicitly** — `/al-toolkit:al-analyst <your requirement>`
- **Implicitly** — just describe the task. Each skill's frontmatter `description` makes
  Claude pick the right one from natural language, in Thai or English.

Skip stages when it makes sense: a one-line fix doesn't need an analysis pass. But
`al-developer` will note in its summary when the analyst stage was skipped.

### 3.1 `al-analyst` — analyze before coding

**Use when:** you have a requirement and don't yet know how to build it. "How should I
implement X", "analyze this requirement", "what's the best way to add Y".

```
/al-toolkit:al-analyst Add an approval workflow to the Purchase Order card so orders
above 100,000 THB need a manager's approval before release.
```

**What it does:** restates the requirement → explores your codebase and `app.json`
(dependencies, `idRanges`, `target`, runtime version) → finds real extension points,
verified with `al_symbolsearch` and Microsoft Learn (never guessed) → compares **at least
two options** → recommends one → surfaces risks.

It works down a decision framework that prefers the least base-app impact:
setup/configuration → event subscriber → table/page extension → new codeunit → new object →
modifying the base app (avoid).

**You get:** a Markdown Solution Design — Requirement Summary, Affected Objects table,
Extension Points Found (with how each was verified), Options A/B with pros/cons/upgrade
impact, Recommended Approach with proposed object names and IDs inside `idRanges`, Risks &
Open Questions (DataClassification, permission sets, upgrade code), and an ordered handoff
plan.

**It will not:** write production AL, or modify any project file. If the requirement is
ambiguous it asks specific questions first.

### 3.2 `al-developer` — implement and build green

**Use when:** you're ready to write code. "Implement this", "write the codeunit", "add
this field", "fix this AL error".

```
/al-toolkit:al-developer Implement the recommended Option B from the analysis above.
```

**What it does:** verifies feasibility **before** writing — confirms objects, fields,
methods and event signatures actually exist via `al_symbolsearch` (symbols, not text
grep), checks `app.json` dependencies, `idRanges` and runtime version. If the planned
approach turns out infeasible it says why, picks the best fallback and explains the
change. Then it writes code against the house standard and runs a real build loop:
`al_downloadsymbols` → `al_compile` (with the cops matching `app.json` `target`) →
`al_getdiagnostics` → fix → repeat until zero errors.

**You get:** the code, plus a summary — approach used, feasibility confirmation, files
changed table, key code decisions, **build result** (which tool, PASS/FAIL, zero errors
confirmed), test gaps, and focus areas for review.

**Notes:**
- Tests are written **only when you ask**. Test gaps are always listed so you can decide.
- If no real build can be run, it will not report the task as done.
- It never publishes to production.

### 3.3 `al-reviewer` — audit and verify

**Use when:** code is written and you want it checked. "Review this code", "check my AL
before I merge", "is this codeunit safe".

```
/al-toolkit:al-reviewer Review the changes in src/PurchaseApproval/.
```

**What it does:** checks requirement coverage, reads the changed code against a nine-part
checklist (requirement, coding standard, architecture, performance, event quality,
compliance/security, data & UX correctness, upgrade safety, build & tests), and — this is
the point — **re-runs the build itself** rather than trusting the developer's report. If it
cannot run any build, it marks the build check NOT VERIFIED instead of assuming.

**You get:** a verdict (✅ Approve / 🔁 Request Changes) with issues graded 🔴 Blocker /
🟠 Major / 🟡 Minor / 🟢 Suggestion, each with `file:line`, the reason, and a suggested fix
— plus an ordered fix list when changes are requested.

**It will not:** edit code. Code that doesn't compile is an immediate 🔴 Blocker.

### House rules

All three skills defer to `references/al-rules.md` as the single source of truth: AL code
style, naming, data access & performance, error handling, events, APIs, tests, upgrade
code, and the AL community "Vibe Coding Rules". Change a rule there and all three stages
pick it up.

---

## 4. Building without the MCP server

`al-build.cmd` is the fallback the skills use, and you can run it directly:

```
plugins\al-toolkit\scripts\al-build.cmd "C:\path\to\AlProject"
plugins\al-toolkit\scripts\al-build.cmd "C:\path\to\AlProject" "C:\out\My.app"
```

With code analysis:

```powershell
$env:AL_ANALYZERS = "CodeCop;PerTenantExtensionCop"   # AppSource: CodeCop;AppSourceCop
plugins\al-toolkit\scripts\al-build.cmd "C:\path\to\AlProject"
```

It prints the compiler diagnostics, then `BUILD OK` (exit 0) or `BUILD FAILED` (exit 1).

> **Why the wrapper exists:** `alc.exe` exits 0 even when compilation fails. Never call
> `alc.exe` directly and trust its exit code — `al-build.cmd` grades the output for you.

---

## 5. Updating

After changing skills or rules here:

1. Bump `version` in `plugins/al-toolkit/.claude-plugin/plugin.json`.
2. Push / re-copy the marketplace folder.
3. On each installed machine:

```
/plugin marketplace update al-toolkit-marketplace
/plugin update al-toolkit@al-toolkit-marketplace
```

---

## 6. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `claude mcp list` doesn't show `al` | AL Language extension missing, or in a non-default location — set `AL_BIN` / `AL_EXTENSIONS_DIR`. |
| `al_*` tools "not found" | They're deferred; Claude loads them via ToolSearch on demand. If they never load, the MCP server isn't connected. |
| `[find-al-bin] Could not find altool.exe` | Install the AL Language extension, or set `AL_BIN` to the folder holding the executables. |
| `error AL1021: The package cache path has not been specified` | No `.alpackages` in the project — download symbols first (`al_downloadsymbols`, or AL: Download Symbols in VS Code). |
| `error AL1022: … could not be found in the package cache` | Symbols are missing or stale for the `application` / `platform` version in `app.json`. |
| Skills load but every build is "NOT VERIFIED" | Claude Code wasn't started inside the AL project folder, or no symbols are present. |

Contributor notes — repo layout, invariants, and how to verify changes — are in
[`CLAUDE.md`](CLAUDE.md).
