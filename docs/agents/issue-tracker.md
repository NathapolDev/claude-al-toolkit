# Issue tracker: GitHub

Issues and specs for this repo live as GitHub issues. Use the `gh` CLI for operations.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`.
- **Read an issue**: `gh issue view <number> --comments`; include labels and comments.
- **List issues**: `gh issue list` with suitable `--state` and `--label` filters.
- **Comment or label**: use `gh issue comment` and `gh issue edit`.
- **Close**: `gh issue close <number> --comment "..."`.

Infer the repository from `git remote -v`; GitHub CLI does this in a clone.

## Pull requests as a request surface

**PRs as a request surface: no.** Keep this off unless maintainers choose to triage
external pull requests as requests.

When a skill asks to publish to the issue tracker, create a GitHub issue. When it asks
to fetch a ticket, run `gh issue view <number> --comments`. GitHub uses one number
space for issues and pull requests; for an ambiguous `#42`, check `gh pr view 42` and
then `gh issue view 42`.

## Wayfinding

For wayfinder work, use a parent issue labelled `wayfinder:map` and link child issues
with GitHub sub-issues or a task list. Use `wayfinder:<type>` for child labels.
Represent blockers with GitHub issue dependencies when available; otherwise add a
`Blocked by: #<number>` line. A child is unblocked when all referenced blockers close.
