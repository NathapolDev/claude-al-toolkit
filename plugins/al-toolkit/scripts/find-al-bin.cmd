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
rem   3. %VSCODE_EXTENSIONS%   - VS Code's own --extensions-dir env var
rem   4. VS Code stable / Insiders / Server / OSS user extension roots
rem   5. Portable / system-wide VS Code installs
rem Within a root, the newest installed ms-dynamics-smb.al-* folder wins, so
rem extension auto-updates never break the caller.
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

rem --- 2..5. Candidate VS Code extension roots ------------------------------
for %%R in (
  "%AL_EXTENSIONS_DIR%"
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
  if not defined FOUND if not "%%~R"=="" if exist "%%~R\" (
    for /f "delims=" %%D in ('dir /b /ad /o-d "%%~R\ms-dynamics-smb.al-*" 2^>nul') do (
      rem AL 18+ ships the toolchain flat in bin; AL 17 and older used bin\win32.
      if not defined FOUND if exist "%%~R\%%D\bin\!WANT!" set "FOUND=%%~R\%%D\bin"
      if not defined FOUND if exist "%%~R\%%D\bin\win32\!WANT!" set "FOUND=%%~R\%%D\bin\win32"
    )
  )
)

if not defined FOUND (
  echo [find-al-bin] Could not find %WANT%. Install the "AL Language" VS Code extension 1>&2
  echo [find-al-bin] ^(ms-dynamics-smb.al^), or set AL_BIN to the folder containing %WANT%, 1>&2
  echo [find-al-bin] or AL_EXTENSIONS_DIR to your VS Code extensions root. 1>&2
  exit /b 1
)

echo !FOUND!
exit /b 0
