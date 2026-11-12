@echo off
setlocal enabledelayedexpansion
rem ---------------------------------------------------------------------------
rem Compiles an AL project with alc.exe - the build fallback used when the `al`
rem MCP server is not connected. Bundled with the plugin so every machine has a
rem real build path without depending on any personally-installed skill.
rem
rem Usage:
rem   al-build.cmd [projectDir] [outAppFile]
rem     projectDir  - defaults to the current directory
rem     outAppFile  - optional; when omitted alc.exe names the .app itself
rem                   (workspace mode: an output FOLDER for every project's .app)
rem
rem Workspace mode: when projectDir holds a *.code-workspace, the toolchain has
rem `altool workspace compile`, and a shared symbol cache exists
rem (AL_PACKAGECACHE or <projectDir>\.alpackages - workspace compile takes one
rem cache for all projects), every project in the workspace is compiled in one
rem run. Otherwise alc.exe compiles projectDir alone (needs app.json there).
rem
rem Optional overrides:
rem   AL_BIN            - folder containing alc.exe
rem   AL_EXTENSIONS_DIR - VS Code extensions root
rem   (toolchain resolution: see find-al-bin.cmd - .NET tool or VS Code extension)
rem   AL_PACKAGECACHE   - symbol folder (default: <projectDir>\.alpackages)
rem   AL_ANALYZERS      - semicolon list of cops, e.g. CodeCop;PerTenantExtensionCop
rem                       (valid: CodeCop, AppSourceCop, PerTenantExtensionCop, UICop)
rem   AL_RULESET        - ruleset file passed as /ruleset:
rem
rem Exit code 0 = build succeeded; non-zero = alc.exe reported errors.
rem ---------------------------------------------------------------------------

set "ALBIN="
for /f "delims=" %%B in ('call "%~dp0find-al-bin.cmd" alc.exe') do set "ALBIN=%%B"
if not defined ALBIN (
  echo [al-build] Cannot build - alc.exe was not found. 1>&2
  exit /b 1
)

set "PROJECT=%~1"
if not defined PROJECT set "PROJECT=%CD%"
set "OUTAPP=%~2"

set "WSFILE="
for %%W in ("%PROJECT%\*.code-workspace") do if not defined WSFILE set "WSFILE=%%~fW"
set "WSCACHE=%AL_PACKAGECACHE%"
if not defined WSCACHE set "WSCACHE=%PROJECT%\.alpackages"
if not defined WSFILE goto alcmode
if not exist "%WSCACHE%\" goto alcmode
if not exist "%ALBIN%\altool.exe" goto alcmode
"%ALBIN%\altool.exe" workspace compile --help >nul 2>&1
if errorlevel 1 goto alcmode
goto workspacemode

:alcmode
if defined WSFILE if not exist "%WSCACHE%\" echo [al-build] Found "%WSFILE%" but no shared symbol cache at "%WSCACHE%" - set AL_PACKAGECACHE to build the whole workspace. 1>&2
if not exist "%PROJECT%\app.json" (
  echo [al-build] No app.json in "%PROJECT%" - not an AL project folder. 1>&2
  exit /b 1
)

set "PKGCACHE=%AL_PACKAGECACHE%"
if not defined PKGCACHE set "PKGCACHE=%PROJECT%\.alpackages"
if not exist "%PKGCACHE%\" (
  echo [al-build] Warning: no symbol cache at "%PKGCACHE%" - download symbols first. 1>&2
)
set "PKGARG=/packagecachepath:"%PKGCACHE%""

rem Map friendly cop names onto the analyzer DLLs shipped with the toolchain:
rem next to alc.exe (.NET tool, AL 18+ extension) or bin\Analyzers (older bin\win32).
set "ANALYZERARGS="
if defined AL_ANALYZERS (
  for %%A in ("%AL_ANALYZERS:;=" "%") do (
    set "COP=%%~A"
    set "COPDLL="
    if not "!COP!"=="" (
      if exist "%ALBIN%\Microsoft.Dynamics.Nav.!COP!.dll" set "COPDLL=%ALBIN%\Microsoft.Dynamics.Nav.!COP!.dll"
      if not defined COPDLL if exist "%ALBIN%\..\Analyzers\Microsoft.Dynamics.Nav.!COP!.dll" set "COPDLL=%ALBIN%\..\Analyzers\Microsoft.Dynamics.Nav.!COP!.dll"
      if defined COPDLL (
        set "ANALYZERARGS=!ANALYZERARGS! /analyzer:"!COPDLL!""
      ) else (
        echo [al-build] Warning: analyzer "!COP!" not found - skipped. 1>&2
      )
    )
  )
)

set "OUTARG="
if defined OUTAPP set "OUTARG=/out:"%OUTAPP%""
if defined AL_RULESET (
  if exist "%AL_RULESET%" (
    set "OUTARG=%OUTARG% /ruleset:"%AL_RULESET%""
  ) else (
    echo [al-build] Warning: ruleset "%AL_RULESET%" not found - skipped. 1>&2
  )
)

echo [al-build] alc.exe from "%ALBIN%"
set "ALLOG=%TEMP%\al-build-%RANDOM%%RANDOM%.log"
"%ALBIN%\alc.exe" /project:"%PROJECT%" %PKGARG% %OUTARG%%ANALYZERARGS% > "%ALLOG%" 2>&1
type "%ALLOG%"

rem alc.exe exits 0 even when compilation fails, so grade the output ourselves.
findstr /r /c:"error [A-Z][A-Z]*[0-9][0-9]*:" "%ALLOG%" >nul
if not errorlevel 1 (
  del "%ALLOG%" >nul 2>&1
  echo [al-build] BUILD FAILED - see the AL errors above. 1>&2
  exit /b 1
)
del "%ALLOG%" >nul 2>&1
echo [al-build] BUILD OK - 0 errors.
exit /b 0

rem ---------------------------------------------------------------------------
:workspacemode
rem workspace compile takes one comma list of cop names; PerTenantExtensionCop
rem is called PTECop there.
set "COPS="
if defined AL_ANALYZERS (
  for %%A in ("%AL_ANALYZERS:;=" "%") do (
    set "COP=%%~A"
    if /i "!COP!"=="PerTenantExtensionCop" set "COP=PTECop"
    if not "!COP!"=="" (
      if defined COPS (set "COPS=!COPS!,!COP!") else (set "COPS=!COP!")
    )
  )
)
set WSARGS=--packagecachepath "%WSCACHE%"
if defined COPS set "WSARGS=!WSARGS! --analyzers !COPS!"
if defined OUTAPP set WSARGS=!WSARGS! --outfolder "%OUTAPP%"
if defined AL_RULESET if exist "%AL_RULESET%" set WSARGS=!WSARGS! --ruleset "%AL_RULESET%"
if defined AL_RULESET if not exist "%AL_RULESET%" echo [al-build] Warning: ruleset "%AL_RULESET%" not found - skipped. 1>&2

set "WSTMP=%TEMP%\al-build-ws-%RANDOM%%RANDOM%"
mkdir "%WSTMP%\logs" "%WSTMP%\errors" >nul 2>&1
echo [al-build] altool workspace compile "%WSFILE%" from "%ALBIN%"
"%ALBIN%\altool.exe" workspace compile "%WSFILE%" !WSARGS! --logdirectory "%WSTMP%\logs" --errorlogdirectory "%WSTMP%\errors"
set "WSEXIT=%errorlevel%"
rem Per-project compiler output, same diagnostic lines as the alc.exe path.
for %%L in ("%WSTMP%\logs\*.log") do type "%%~fL"

set "WSFAILED="
if not "%WSEXIT%"=="0" set "WSFAILED=1"
rem Match "severity" only at line start: "defaultSeverity": "Error" must not count.
findstr /r /c:"^ *\"severity\": \"Error\"" "%WSTMP%\errors\*.json" >nul 2>&1
if not errorlevel 1 set "WSFAILED=1"
rd /s /q "%WSTMP%" >nul 2>&1
if defined WSFAILED goto wsfailed
echo [al-build] BUILD OK - 0 errors.
exit /b 0
:wsfailed
echo [al-build] BUILD FAILED - see the AL errors above. 1>&2
exit /b 1
