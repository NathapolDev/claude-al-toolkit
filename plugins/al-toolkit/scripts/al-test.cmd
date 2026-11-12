@echo off
setlocal enabledelayedexpansion
rem ---------------------------------------------------------------------------
rem Runs AL tests with `altool runtests` - the test fallback used when the `al`
rem MCP server (al_run_tests) is not connected.
rem
rem Usage:
rem   al-test.cmd <projectDir> <codeunitId> [--testmethods A B ...] [runtests options]
rem   al-test.cmd <projectDir> --testgroups <file.json> [runtests options]
rem
rem Everything after <projectDir> is passed to `altool runtests` unchanged, plus
rem `--project <projectDir>` so launch.json supplies the connection. On-prem and
rem containers can use BC_SERVER_URL / BC_SERVER_INSTANCE / BC_SERVER_PORT /
rem BC_SERVER_USERNAME / BC_SERVER_PASSWORD instead (read by altool itself;
rem this script never prints them).
rem
rem Refuses to run against Production: when "Production" is passed, or when no
rem --environmenttype / --server / BC_SERVER_URL is given and launch.json is
rem missing or contains a Production configuration.
rem
rem stdout: the JSON result from runtests (data.passed / failed / skipped and
rem data.results[]; the row with an empty methodName is the codeunit summary).
rem Exit code: 0 = all tests passed; 1 = a test failed, the connection failed,
rem or the toolchain has no runtests command.
rem ---------------------------------------------------------------------------

set "PROJECT=%~1"
if not defined PROJECT (
  echo [al-test] Usage: al-test.cmd ^<projectDir^> ^<codeunitId^> [runtests options] 1>&2
  exit /b 1
)
if not exist "%PROJECT%\app.json" (
  echo [al-test] No app.json in "%PROJECT%" - not an AL project folder. 1>&2
  exit /b 1
)

set "ALBIN="
for /f "delims=" %%B in ('call "%~dp0find-al-bin.cmd" altool.exe') do set "ALBIN=%%B"
if not defined ALBIN (
  echo [al-test] Cannot run tests - altool.exe was not found. 1>&2
  exit /b 1
)
"%ALBIN%\altool.exe" runtests --help >nul 2>&1
if errorlevel 1 (
  echo [al-test] This AL toolchain has no "runtests" command - update the AL Development Tools or AL Language extension. 1>&2
  exit /b 1
)

set "REST="
set "TARGETED="
:collect
shift
if "%~1"=="" goto guard
if /i "%~1"=="Production" goto refuseprod
if /i "%~1"=="--environmenttype" set "TARGETED=1"
if /i "%~1"=="--server" set "TARGETED=1"
set REST=!REST! "%~1"
goto collect

rem Refusals exit at top level: `exit /b 1` inside a ( ) block loses its exit
rem code when the script is run directly instead of via `call`.
:guard
if defined BC_SERVER_URL set "TARGETED=1"
if defined TARGETED goto run
if not exist "%PROJECT%\.vscode\launch.json" goto refusenotarget
findstr /r /i /c:"\"environmentType\" *: *\"Production\"" "%PROJECT%\.vscode\launch.json" >nul
if not errorlevel 1 goto refuselaunch
goto run

:refuseprod
echo [al-test] Refusing to run tests against a Production environment. 1>&2
exit /b 1
:refusenotarget
echo [al-test] No .vscode\launch.json and no --environmenttype / --server - refusing to guess the target. 1>&2
exit /b 1
:refuselaunch
echo [al-test] launch.json has a Production configuration - pass --environmenttype Sandbox and --environmentname explicitly. 1>&2
exit /b 1

:run
echo [al-test] altool runtests from "%ALBIN%" 1>&2
"%ALBIN%\altool.exe" runtests !REST! --project "%PROJECT%"
exit /b %errorlevel%
