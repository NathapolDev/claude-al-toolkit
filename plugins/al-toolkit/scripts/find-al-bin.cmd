@echo off
setlocal enabledelayedexpansion
rem ---------------------------------------------------------------------------
rem Resolves the folder holding the AL Language toolchain executables
rem (altool.exe / alc.exe / almcp.exe / aldoc.exe) on THIS machine.
rem
rem Usage:
rem   for /f "delims=" %%B in ('call "%~dp0find-al-bin.cmd" alc.exe') do set "ALBIN=%%B"
rem
rem Prints the resolved bin folder to stdout and exits 0, or prints a diagnostic
rem to stderr and exits 1. Search order (first hit wins):
rem   1. %AL_BIN%              - explicit bin folder override
rem   2. %AL_EXTENSIONS_DIR%   - explicit VS Code extensions root override
rem   3. AL Development Tools .NET global tool
rem      (dotnet tool install -g Microsoft.Dynamics.BusinessCentral.Development.Tools)
rem      - no VS Code needed; picks the net10.0 / net8.0 build whose runtime exists
rem   4. %VSCODE_EXTENSIONS%   - VS Code's own --extensions-dir env var
rem   5. VS Code stable / Insiders / Server / OSS user extension roots
rem   6. Portable / system-wide VS Code installs
rem Within an extension root, the newest ms-dynamics-smb.al-* folder wins, so
rem extension auto-updates never break the caller. Extension layouts: AL 18+
rem ships binaries in bin\, older versions in bin\win32 - both are accepted.
rem ---------------------------------------------------------------------------

set "WANT=%~1"
if "%WANT%"=="" set "WANT=altool.exe"
set "FOUND="

rem --- 1. Explicit bin folder override -------------------------------------
if defined AL_BIN (
  if exist "%AL_BIN%\%WANT%" (
    echo %AL_BIN%
    exit /b 0
  )
  echo [find-al-bin] AL_BIN is set to "%AL_BIN%" but %WANT% is not in it - ignoring. 1>&2
)

rem --- 2. Explicit extensions root override --------------------------------
call :scanroot "%AL_EXTENSIONS_DIR%"

rem --- 3. .NET global tool -------------------------------------------------
if not defined FOUND call :dotnettool

rem --- 4..6. VS Code extension roots ---------------------------------------
for %%R in (
  "%VSCODE_EXTENSIONS%"
  "%USERPROFILE%\.vscode\extensions"
  "%USERPROFILE%\.vscode-insiders\extensions"
  "%USERPROFILE%\.vscode-server\extensions"
  "%USERPROFILE%\.vscode-oss\extensions"
  "%LOCALAPPDATA%\Programs\Microsoft VS Code\data\extensions"
  "%LOCALAPPDATA%\Programs\Microsoft VS Code Insiders\data\extensions"
  "%ProgramFiles%\Microsoft VS Code\data\extensions"
  "%ProgramFiles(x86)%\Microsoft VS Code\data\extensions"
) do (
  if not defined FOUND call :scanroot "%%~R"
)

if not defined FOUND (
  echo [find-al-bin] Could not find %WANT%. Install the AL Development Tools .NET tool 1>&2
  echo [find-al-bin] ^(dotnet tool install -g Microsoft.Dynamics.BusinessCentral.Development.Tools^) 1>&2
  echo [find-al-bin] or the "AL Language" VS Code extension ^(ms-dynamics-smb.al^), or set AL_BIN 1>&2
  echo [find-al-bin] to the folder containing %WANT%, or AL_EXTENSIONS_DIR to your VS Code extensions root. 1>&2
  exit /b 1
)

echo !FOUND!
exit /b 0

rem ---------------------------------------------------------------------------
rem :scanroot <extensionsRoot> - newest ms-dynamics-smb.al-* holding %WANT%
:scanroot
if defined FOUND exit /b 0
if "%~1"=="" exit /b 0
if not exist "%~1\" exit /b 0
for /f "delims=" %%D in ('dir /b /ad /o-d "%~1\ms-dynamics-smb.al-*" 2^>nul') do (
  if not defined FOUND if exist "%~1\%%D\bin\%WANT%" set "FOUND=%~1\%%D\bin"
  if not defined FOUND if exist "%~1\%%D\bin\win32\%WANT%" set "FOUND=%~1\%%D\bin\win32"
)
exit /b 0

rem ---------------------------------------------------------------------------
rem :dotnettool - global tool store; the package ships net10.0 and net8.0
rem builds, each needing its matching ASP.NET Core runtime, so only accept a
rem build whose runtime is installed.
:dotnettool
set "PKG=microsoft.dynamics.businesscentral.development.tools"
set "STORE=%USERPROFILE%\.dotnet\tools\.store\%PKG%"
if not exist "%STORE%\" exit /b 0
rem Guard first: piping from a missing dotnet aborts the whole batch.
where dotnet >nul 2>&1
if errorlevel 1 exit /b 0
set "RUNTIMES= "
for /f "tokens=2" %%R in ('dotnet --list-runtimes 2^>nul ^| findstr /b /c:"Microsoft.AspNetCore.App "') do set "RUNTIMES=!RUNTIMES!%%R "
for %%M in (10 8) do (
  if not defined FOUND if not "!RUNTIMES: %%M.=!"=="!RUNTIMES!" (
    for /f "delims=" %%V in ('dir /b /ad /o-d "%STORE%" 2^>nul') do (
      if not defined FOUND if exist "%STORE%\%%V\%PKG%\%%V\tools\net%%M.0\any\%WANT%" set "FOUND=%STORE%\%%V\%PKG%\%%V\tools\net%%M.0\any"
    )
  )
)
exit /b 0
