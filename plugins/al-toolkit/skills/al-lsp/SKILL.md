---
name: al-lsp
description: >-
  Use the AL Language Server (`al-lsp` MCP server or `../../scripts/al-lsp-mcp.cmd --cli`)
  for semantic Business Central AL code intelligence: go-to-definition, find-references
  (`TransferFields` and procedure callers without comment/string false positives), hover
  type/doc inspection, document/workspace symbol search, signature help, and non-destructive
  rename preview. Use when analyzing, implementing, reviewing, or debugging `.al` files.
---

# AL Language Server Intelligence (al-lsp)

Use the `al-lsp` MCP server (backed by Microsoft's `altool launchlspserver` via
`scripts/al-lsp.cmd`) for exact, compiler-backed semantic navigation on `.al` files.
Prefer these tools over text grep when resolving AL symbols, tracing callers, or
checking `TransferFields` field usages.

## When to use `al-lsp` vs `al` MCP vs `al-graph.cmd`

| Need | Best tool |
|---|---|
| Exact symbol definition, callers/references in source, hover signature/docs, file outline, call-site parameter help, rename preview | **`al-lsp` MCP** (this skill) or `../../scripts/al-lsp-mcp.cmd --cli` |
| Cross-package symbol search in `.alpackages` / environment, compile diagnostics, next object ID, symbol download, tests | **`al` MCP** (`al_symbolsearch`, `al_compile`, `al_getnextobjectid`, `al_run_tests`) |
| Multi-app call graph traversal across extracted folders | **`../../scripts/al-graph.cmd`** |

## Available tools (`al-lsp` MCP server)

In Antigravity, invoke these tools on MCP server `al-lsp` (e.g. via `call_mcp_tool`).
All `line` and `character` coordinates are **1-based** (`>= 1`), and all returned
locations use **1-based** `startLine`, `startCharacter`, `endLine`, `endCharacter`,
`filePath`, and source-line `preview`.

| Tool | Required params | Optional params | Purpose |
|---|---|---|---|
| `al_lsp_definition` | `filePath`, `line`, `character` | `projectPath` | Jump to symbol declaration (`textDocument/definition`) |
| `al_lsp_references` | `filePath`, `line`, `character` | `includeDeclaration` (default `true`), `projectPath` | Find all semantic references (`textDocument/references`) |
| `al_lsp_hover` | `filePath`, `line`, `character` | `projectPath` | Inspect type signature and XML doc comments (`textDocument/hover`) |
| `al_lsp_document_symbols` | `filePath` | `projectPath` | List hierarchical symbols in one `.al` file (`textDocument/documentSymbol`) |
| `al_lsp_workspace_symbols` | `query` | `projectPath` | Search symbols across the workspace (`workspace/symbol`) |
| `al_lsp_signature_help` | `filePath`, `line`, `character` | `projectPath` | Inspect overload signatures & active parameter (`textDocument/signatureHelp`) |
| `al_lsp_rename_preview` | `filePath`, `line`, `character`, `newName` | `projectPath` | Preview rename edits without modifying files on disk (`textDocument/rename`) |

### `projectPath` resolution

If `projectPath` is omitted, the bridge walks up from `filePath` to the nearest
folder containing `*.code-workspace` or `app.json` (falling back to `AL_PROJECT_DIR`
or the current working directory). In an App + Test workspace where `app/` has its
own `app.json` and the parent folder holds `*.code-workspace`, pass `projectPath`
pointing to the workspace root so references span both apps.

## Core workflows

### 1. Symbol resolution
- To locate an object or procedure by name first, call `al_lsp_workspace_symbols`
  with `query` (and `projectPath` if needed).
- To inspect a file's structure without reading hundreds of lines, call
  `al_lsp_document_symbols` on `filePath` to get every object, field, key, trigger,
  and procedure with exact 1-based line numbers.
- From a usage site, call `al_lsp_definition` on the identifier's 1-based `line` and
  `character` to jump straight to its declaration (procedure, table field, enum, etc.).

### 2. Find references (`TransferFields` and procedure callers)
- **Procedure callers:** place `line`/`character` on a procedure name (at its
  declaration or any call site) and call `al_lsp_references` (`includeDeclaration: false`
  to list only callers, or `true` to include the declaration). Unlike text grep, LSP
  skips comments and string literals and handles quoted/unquoted AL identifiers accurately.
- **`TransferFields` impact checks:** call `al_lsp_references` on the table or table
  field you are adding or modifying to trace every assignment, `SetRange`, and
  `TransferFields` usage inside the workspace. Combine with `al_symbolsearch` for
  base-app posting/archiving flows (e.g. Sales Header/Line, Item Journal Line) outside
  workspace source.

### 3. Hover and signature inspection
- Call `al_lsp_hover` at a symbol usage or declaration to confirm its exact AL type,
  parameters, return type, and XML `<summary>` documentation (or `[Obsolete]` reason).
- Call `al_lsp_signature_help` inside the parentheses of a procedure call to check all
  overloads and parameter descriptions before editing arguments.

### 4. Non-destructive rename preview
- Call `al_lsp_rename_preview` with `newName` to inspect every file and 1-based range
  that would change. Nothing is written to disk (`applied: false`).

## CLI fallback (`al-lsp-mcp.cmd --cli`)

When the `al-lsp` MCP server is not connected, invoke the bundled CLI wrapper directly.
Resolve `../../scripts/al-lsp-mcp.cmd` relative to the directory containing this
`SKILL.md` file (or `${CLAUDE_PLUGIN_ROOT}/scripts/al-lsp-mcp.cmd` in Claude Code).

Syntax:

```powershell
../../scripts/al-lsp-mcp.cmd --cli <tool_name> "<json_args_or_file>"
```

Examples (PowerShell — escape inner `\"` when calling `.cmd`, or pass a JSON file path):

```powershell
# Go to definition
../../scripts/al-lsp-mcp.cmd --cli al_lsp_definition '{\"filePath\":\"src/SalesHelper.Codeunit.al\",\"line\":21,\"character\":26}'

# Find all references to a table field (TransferFields / usage check)
../../scripts/al-lsp-mcp.cmd --cli al_lsp_references '{\"filePath\":\"src/MyCustomerExt.TableExt.al\",\"line\":8,\"character\":20,\"includeDeclaration\":true}'

# Hover type and XML doc inspection
../../scripts/al-lsp-mcp.cmd --cli al_lsp_hover '{\"filePath\":\"src/SalesHelper.Codeunit.al\",\"line\":21,\"character\":26}'

# Workspace symbol search
../../scripts/al-lsp-mcp.cmd --cli al_lsp_workspace_symbols '{\"query\":\"BuildGreeting\",\"projectPath\":\"D:/Repos/MyAlApp\"}'

# Or pass a JSON file path (recommended when paths/args contain spaces or quotes)
../../scripts/al-lsp-mcp.cmd --cli al_lsp_references args.json
```

The CLI prints the JSON result to stdout and exits `0` on success or `1` on error
(errors go to stderr).

## Prerequisites & troubleshooting

- **AL toolchain:** requires `altool.exe` from Microsoft's AL Development Tools .NET
  global tool or the AL Language VS Code extension (resolved at launch time via
  `../../scripts/find-al-bin.cmd`).
- **Symbol cache:** for base-app / dependency symbol resolution, ensure `.alpackages`
  is populated in the project (or set `AL_PACKAGECACHE`). Without `.alpackages`, local
  workspace symbols still resolve, while external package references degrade.
- **File sync:** the bridge automatically reads files from disk (UTF-8 / UTF-8 BOM)
  and sends `textDocument/didOpen` or `textDocument/didChange` before every document
  request, so edits saved on disk are reflected immediately.
