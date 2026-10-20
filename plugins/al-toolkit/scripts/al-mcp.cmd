@echo off
setlocal
rem ---------------------------------------------------------------------------
rem Launches the AL MCP server (altool launchmcpserver) from the AL Development
rem Tools .NET global tool or the AL Language VS Code extension. Path
rem resolution is delegated to find-al-bin.cmd, which honours the AL_BIN /
rem AL_EXTENSIONS_DIR overrides - so this works with or without VS Code.
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

rem altool requires at least one project path; default to the directory Claude
rem Code was started in (the current AL project).
set "ALPROJECT=%AL_PROJECT_DIR%"
if not defined ALPROJECT set "ALPROJECT=%CD%"

"%ALBIN%\altool.exe" launchmcpserver --transport stdio "%ALPROJECT%"
