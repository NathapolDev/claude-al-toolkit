@echo off
setlocal enabledelayedexpansion
rem ---------------------------------------------------------------------------
rem Resolves a DOTNET_ROOT for an AL toolchain executable when the machine-wide
rem .NET install lacks the runtime it needs (AL Language 18+ targets net10.0).
rem
rem Usage:
rem   for /f "delims=" %%R in ('call "%~dp0find-dotnet-root.cmd" "%ALBIN%\altool.exe"') do set "DOTNET_ROOT=%%R"
rem
rem Reads <exe>.runtimeconfig.json for the target major version and framework
rem (Microsoft.AspNetCore.App if listed, else Microsoft.NETCore.App). Prints
rem nothing when DOTNET_ROOT is already set or %ProgramFiles%\dotnet has that
rem framework. Otherwise prints the newest matching runtime the VS Code .NET
rem Install Tool downloaded (the AL extension pulls one in), or warns on stderr.
rem Always exits 0 - the executable reports the definitive error itself.
rem ---------------------------------------------------------------------------

if defined DOTNET_ROOT exit /b 0

set "CFG=%~dpn1.runtimeconfig.json"
if not exist "%CFG%" exit /b 0

set "TFM="
for /f "tokens=2 delims=:, " %%T in ('findstr /c:"\"tfm\"" "%CFG%"') do set "TFM=%%~T"
if not defined TFM exit /b 0
rem net10.0 -> 10
set "TFM=!TFM:net=!"
for /f "delims=." %%M in ("!TFM!") do set "MAJOR=%%M"

set "FW=Microsoft.NETCore.App"
findstr /c:"Microsoft.AspNetCore.App" "%CFG%" >nul && set "FW=Microsoft.AspNetCore.App"

dir /b /ad "%ProgramFiles%\dotnet\shared\%FW%\!MAJOR!.*" >nul 2>&1 && exit /b 0

set "VSDOTNET=%APPDATA%\Code\User\globalStorage\ms-dotnettools.vscode-dotnet-runtime\.dotnet"
set "FOUND="
for /f "delims=" %%R in ('dir /b /ad /o-n "%VSDOTNET%\!MAJOR!.*~x64*" 2^>nul') do (
  if not defined FOUND if exist "%VSDOTNET%\%%R\dotnet.exe" (
    dir /b /ad "%VSDOTNET%\%%R\shared\%FW%\!MAJOR!.*" >nul 2>&1 && set "FOUND=%VSDOTNET%\%%R"
  )
)

if not defined FOUND (
  echo [find-dotnet-root] %~nx1 needs %FW% !MAJOR!.x ^(x64^), which is not installed. 1>&2
  echo [find-dotnet-root] Install it: winget install Microsoft.DotNet.AspNetCore.!MAJOR! 1>&2
  exit /b 0
)

echo !FOUND!
exit /b 0
