@echo off
setlocal enabledelayedexpansion
rem ---------------------------------------------------------------------------
rem Answers a call-graph question about AL code with `altool graph`:
rem extract every app under <dir> -> stitch -> query. The graph is built in
rem %TEMP% and deleted afterwards; nothing is written to the project.
rem
rem Usage:
rem   al-graph.cmd <dir> <graph query options>
rem     <dir>  an app folder (app.json) or a folder whose subfolders (one or two
rem            levels down) are app folders, e.g. an App + Test workspace root
rem
rem Examples:
rem   al-graph.cmd . --to "obj:My Codeunit#MyProcedure" --direction callers
rem   al-graph.cmd . --from "obj:My Codeunit" --depth 1
rem
rem Selectors use the object NAME, and obj:<Object>#<Procedure> for a procedure.
rem obj:<ID>, obj:<Object>.<Procedure> and bare procedure names match nothing
rem and report "0 node(s)" without an error - check the selector with --from
rem before reading 0 callers as "no callers".
rem
rem Exit code: altool's (0 when the query ran); 1 when nothing could be built.
rem ---------------------------------------------------------------------------

set "ROOT=%~f1"
if "%~1"=="" (
  echo [al-graph] Usage: al-graph.cmd ^<dir^> --to "obj:Object#Procedure" --direction callers 1>&2
  exit /b 1
)

set "ALBIN="
for /f "delims=" %%B in ('call "%~dp0find-al-bin.cmd" altool.exe') do set "ALBIN=%%B"
if not defined ALBIN goto noaltool
"%ALBIN%\altool.exe" graph extract --help >nul 2>&1
if errorlevel 1 goto nograph

set "QUERY="
:collect
shift
if "%~1"=="" goto build
set QUERY=!QUERY! "%~1"
goto collect

:build
set "GTMP=%TEMP%\al-graph-%RANDOM%%RANDOM%"
mkdir "%GTMP%\shards" >nul 2>&1
set "APPS=0"
if exist "%ROOT%\app.json" call :extract "%ROOT%"
for /d %%D in ("%ROOT%\*") do (
  if exist "%%~fD\app.json" call :extract "%%~fD"
  for /d %%E in ("%%~fD\*") do if exist "%%~fE\app.json" call :extract "%%~fE"
)
if "%APPS%"=="0" goto noapps

"%ALBIN%\altool.exe" graph stitch --shards "%GTMP%\shards" --out "%GTMP%\graph.jsonl" 1>&2
if errorlevel 1 goto stitchfailed
"%ALBIN%\altool.exe" graph query --graph "%GTMP%\graph.jsonl" !QUERY!
set "QEXIT=%errorlevel%"
rd /s /q "%GTMP%" >nul 2>&1
exit /b %QEXIT%

:extract
set /a APPS+=1
echo [al-graph] extracting %~1 1>&2
"%ALBIN%\altool.exe" graph extract --app "%~1" --out "%GTMP%\shards" >nul 2>&1
if errorlevel 1 echo [al-graph] Warning: could not extract "%~1" - its calls are missing from the graph. 1>&2
exit /b 0

:noaltool
echo [al-graph] altool.exe was not found. 1>&2
exit /b 1
:nograph
echo [al-graph] This AL toolchain has no "graph" command - update the AL Development Tools or AL Language extension. 1>&2
exit /b 1
:noapps
rd /s /q "%GTMP%" >nul 2>&1
echo [al-graph] No app.json found in "%ROOT%" or the two folder levels below it. 1>&2
exit /b 1
:stitchfailed
rd /s /q "%GTMP%" >nul 2>&1
echo [al-graph] graph stitch failed. 1>&2
exit /b 1
