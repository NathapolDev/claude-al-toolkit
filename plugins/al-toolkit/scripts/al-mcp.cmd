@echo off
setlocal enabledelayedexpansion
rem ---------------------------------------------------------------------------
rem Launches the AL MCP server (altool launchmcpserver) from the AL Development
rem Tools .NET global tool or the AL Language VS Code extension. Path
rem resolution is delegated to find-al-bin.cmd, which honours the AL_BIN /
rem AL_EXTENSIONS_DIR overrides - so this works with or without VS Code.
rem
rem stdout belongs to the MCP stdio protocol: every message from this script
rem goes to stderr.
rem
rem Optional overrides:
rem   AL_BIN            - folder containing altool.exe
rem   AL_EXTENSIONS_DIR - VS Code extensions root
rem   AL_PROJECT_DIR    - AL project passed to altool (default: current dir).
rem                       Skipped when it has no app.json; add projects later
rem                       with the al_addproject tool.
rem   AL_PACKAGECACHE   - symbol folder (--packagecachepath)
rem   AL_RULESET        - ruleset file (--ruleset); needs AL_ANALYZERS to matter
rem   AL_ANALYZERS      - semicolon list of cops, e.g. CodeCop;PerTenantExtensionCop
rem                       (passed as --codeanalyzers ${Cop}; the bare name is
rem                       silently ignored by altool)
rem   AL_MCP_LOGLEVEL   - Debug, Verbose, Normal, Warning, Error (--loglevel)
rem   AL_MCP_LOGFILE    - log file (--logfile); default is
rem                       %LOCALAPPDATA%\Microsoft\ALLanguageServer\almcp.log
rem ---------------------------------------------------------------------------

set "ALBIN="
for /f "delims=" %%B in ('call "%~dp0find-al-bin.cmd" altool.exe') do set "ALBIN=%%B"
if not defined ALBIN (
  echo [al-mcp] AL MCP server cannot start - altool.exe was not found. 1>&2
  exit /b 1
)

set "ALPROJECT=%AL_PROJECT_DIR%"
if not defined ALPROJECT set "ALPROJECT=%CD%"

rem The project must come BEFORE the options: --packagecachepath accepts
rem several values and would swallow a trailing project path, leaving the
rem server with no project loaded and no error.
set "ARGS="
if exist "%ALPROJECT%\app.json" (
  set ARGS="%ALPROJECT%"
) else (
  echo [al-mcp] "%ALPROJECT%" has no app.json - starting without a project; use al_addproject. 1>&2
)

set "ARGS=!ARGS! --transport stdio"
if defined AL_PACKAGECACHE set ARGS=!ARGS! --packagecachepath "%AL_PACKAGECACHE%"
if defined AL_RULESET set ARGS=!ARGS! --ruleset "%AL_RULESET%"
if defined AL_MCP_LOGLEVEL set ARGS=!ARGS! --loglevel %AL_MCP_LOGLEVEL%
if defined AL_MCP_LOGFILE set ARGS=!ARGS! --logfile "%AL_MCP_LOGFILE%"
if defined AL_ANALYZERS (
  for %%A in ("%AL_ANALYZERS:;=" "%") do (
    if not "%%~A"=="" set "ARGS=!ARGS! --codeanalyzers ${%%~A}"
  )
)

"%ALBIN%\altool.exe" launchmcpserver !ARGS!
