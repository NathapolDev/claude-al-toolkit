@echo off
setlocal
rem ---------------------------------------------------------------------------
rem Launches the AL MCP server from the installed AL Language extension.
rem Path resolution is delegated to find-al-bin.cmd, which searches several
rem VS Code extension roots and honours the AL_BIN / AL_EXTENSIONS_DIR
rem overrides - so this works on machines with non-default VS Code layouts.
rem
rem Optional overrides:
rem   AL_BIN            - folder containing altool.exe
rem   AL_EXTENSIONS_DIR - VS Code extensions root
rem   AL_PROJECT_DIR    - AL project passed to altool (default: current dir)
rem ---------------------------------------------------------------------------

set "ALBIN="
for /f "delims=" %%B in ('call "%~dp0find-al-bin.cmd" altool.exe') do set "ALBIN=%%B"
if not defined ALBIN (
  echo [al-mcp] AL MCP server cannot start - altool.exe was not found. 1>&2
  exit /b 1
)

rem Codex launches from the installed plugin root. Defer workspace selection to
rem al_addproject unless AL_PROJECT_DIR is explicitly configured.
set "ALPROJECT=%AL_PROJECT_DIR%"
if not defined ALPROJECT if /i not "%~1"=="--defer-project" set "ALPROJECT=%CD%"
if not defined ALPROJECT (
  "%ALBIN%\altool.exe" launchmcpserver --transport stdio
  exit /b
)

"%ALBIN%\altool.exe" launchmcpserver --transport stdio "%ALPROJECT%"
