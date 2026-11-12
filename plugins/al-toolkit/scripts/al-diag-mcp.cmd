@echo off
setlocal enabledelayedexpansion
rem ---------------------------------------------------------------------------
rem Launches one of Microsoft's opt-in diagnostics MCP proxies against a
rem Business Central environment:
rem   snapshot  -> altool launchsnapshotmcpproxy  (snapshot debugging)
rem   profiling -> altool launchprofilingmcpproxy (performance profiling)
rem
rem NOT registered in the plugin's .mcp.json: these proxies connect to an
rem environment and can capture business data, so each user adds them on
rem purpose (see README, "Opt-in: snapshot debugging and profiling").
rem
rem Usage (as an MCP server command):
rem   al-diag-mcp.cmd snapshot|profiling [extra altool options, e.g. on-prem
rem                   --server http://bc --serverinstance BC --port 7047]
rem
rem Required: AL_ENV_TYPE = Sandbox | Production | OnPrem. The proxies default
rem to Production, so this script refuses to start without an explicit type.
rem Cloud: AL_ENV_NAME (environment name). Optional: AL_TENANT.
rem stdout belongs to the MCP protocol: messages from this script go to stderr.
rem ---------------------------------------------------------------------------

set "MODE=%~1"
set "SUB="
if /i "%MODE%"=="snapshot" set "SUB=launchsnapshotmcpproxy"
if /i "%MODE%"=="profiling" set "SUB=launchprofilingmcpproxy"
if not defined SUB goto usage
if not defined AL_ENV_TYPE goto notype
if /i not "%AL_ENV_TYPE%"=="OnPrem" if not defined AL_ENV_NAME goto noname

set "ALBIN="
for /f "delims=" %%B in ('call "%~dp0find-al-bin.cmd" altool.exe') do set "ALBIN=%%B"
if not defined ALBIN goto noaltool
"%ALBIN%\altool.exe" %SUB% --help >nul 2>&1
if errorlevel 1 goto nocommand

set ARGS=--environmenttype %AL_ENV_TYPE%
if defined AL_ENV_NAME set ARGS=!ARGS! --environmentname "%AL_ENV_NAME%"
if defined AL_TENANT set ARGS=!ARGS! --tenant "%AL_TENANT%"
:collect
shift
if "%~1"=="" goto run
set ARGS=!ARGS! "%~1"
goto collect

:run
echo [al-diag-mcp] %SUB% for %AL_ENV_TYPE% "%AL_ENV_NAME%" 1>&2
"%ALBIN%\altool.exe" %SUB% !ARGS!
exit /b %errorlevel%

:usage
echo [al-diag-mcp] Usage: al-diag-mcp.cmd snapshot^|profiling [altool options] 1>&2
exit /b 1
:notype
echo [al-diag-mcp] Set AL_ENV_TYPE to Sandbox, Production, or OnPrem - refusing to fall back to the proxy's Production default. 1>&2
exit /b 1
:noname
echo [al-diag-mcp] Set AL_ENV_NAME to the Business Central environment name. 1>&2
exit /b 1
:noaltool
echo [al-diag-mcp] altool.exe was not found. 1>&2
exit /b 1
:nocommand
echo [al-diag-mcp] This AL toolchain has no "%SUB%" command - update the AL Development Tools or AL Language extension. 1>&2
exit /b 1
