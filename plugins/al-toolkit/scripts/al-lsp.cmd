@echo off
setlocal enabledelayedexpansion
rem ---------------------------------------------------------------------------
rem Launches the AL language server (altool launchlspserver) for Claude Code's
rem LSP integration (.lsp.json). Toolchain resolution is delegated to
rem find-al-bin.cmd, like the MCP launcher.
rem
rem stdout belongs to the LSP protocol: every message from this script goes to
rem stderr.
rem
rem Project: AL_PROJECT_DIR, else CLAUDE_PROJECT_DIR (set by Claude Code), else
rem the current directory. A *.code-workspace there is passed as
rem --workspacefile (App + Test); otherwise the folder is passed when it holds
rem app.json; otherwise the server relies on the LSP initialize request.
rem
rem Optional overrides: AL_BIN, AL_EXTENSIONS_DIR, AL_PACKAGECACHE.
rem The server logs to ~/.al-mcp/almcp.log by default.
rem ---------------------------------------------------------------------------

set "ALBIN="
for /f "delims=" %%B in ('call "%~dp0find-al-bin.cmd" altool.exe') do set "ALBIN=%%B"
if not defined ALBIN (
  echo [al-lsp] AL language server cannot start - altool.exe was not found. 1>&2
  exit /b 1
)

set "ALPROJECT=%AL_PROJECT_DIR%"
if not defined ALPROJECT set "ALPROJECT=%CLAUDE_PROJECT_DIR%"
if not defined ALPROJECT set "ALPROJECT=%CD%"

rem As with launchmcpserver, the project goes BEFORE --packagecachepath,
rem which takes several values and would swallow a trailing path.
set "WSFILE="
for %%W in ("%ALPROJECT%\*.code-workspace") do if not defined WSFILE set "WSFILE=%%~fW"
set "ARGS="
if defined WSFILE (
  set ARGS=--workspacefile "!WSFILE!"
) else if exist "%ALPROJECT%\app.json" (
  set ARGS="%ALPROJECT%"
) else (
  echo [al-lsp] "%ALPROJECT%" has no app.json or .code-workspace - waiting for the client's workspace folders. 1>&2
)
if defined AL_PACKAGECACHE set ARGS=!ARGS! --packagecachepath "%AL_PACKAGECACHE%"

"%ALBIN%\altool.exe" launchlspserver !ARGS!
