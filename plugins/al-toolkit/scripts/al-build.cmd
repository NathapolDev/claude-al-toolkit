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
rem
rem Optional overrides:
rem   AL_BIN            - folder containing alc.exe
rem   AL_EXTENSIONS_DIR - VS Code extensions root
rem   AL_PACKAGECACHE   - symbol folder (default: <projectDir>\.alpackages)
rem   AL_ANALYZERS      - semicolon list of cops, e.g. CodeCop;PerTenantExtensionCop
rem                       (valid: CodeCop, AppSourceCop, PerTenantExtensionCop, UICop)
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
if not exist "%PROJECT%\app.json" (
  echo [al-build] No app.json in "%PROJECT%" - not an AL project folder. 1>&2
  exit /b 1
)

set "OUTAPP=%~2"

set "PKGCACHE=%AL_PACKAGECACHE%"
if not defined PKGCACHE set "PKGCACHE=%PROJECT%\.alpackages"
if not exist "%PKGCACHE%\" (
  echo [al-build] Warning: no symbol cache at "%PKGCACHE%" - download symbols first. 1>&2
)
set "PKGARG=/packagecachepath:"%PKGCACHE%""

rem Map friendly cop names onto the analyzer DLLs shipped with the extension.
set "ANALYZERARGS="
if defined AL_ANALYZERS (
  for %%A in ("%AL_ANALYZERS:;=" "%") do (
    set "COP=%%~A"
    if not "!COP!"=="" (
      if exist "%ALBIN%\Microsoft.Dynamics.Nav.!COP!.dll" (
        set "ANALYZERARGS=!ANALYZERARGS! /analyzer:"%ALBIN%\Microsoft.Dynamics.Nav.!COP!.dll""
      ) else if exist "%ALBIN%\..\Analyzers\Microsoft.Dynamics.Nav.!COP!.dll" (
        set "ANALYZERARGS=!ANALYZERARGS! /analyzer:"%ALBIN%\..\Analyzers\Microsoft.Dynamics.Nav.!COP!.dll""
      ) else (
        echo [al-build] Warning: analyzer "!COP!" not found - skipped. 1>&2
      )
    )
  )
)

set "OUTARG="
if defined OUTAPP set "OUTARG=/out:"%OUTAPP%""

echo [al-build] alc.exe from "%ALBIN%"
set "ALLOG=%TEMP%\al-build-%RANDOM%%RANDOM%.log"
"%ALBIN%\alc.exe" /project:"%PROJECT%" %PKGARG% %OUTARG%%ANALYZERARGS% > "%ALLOG%" 2>&1
set "ALCOMPILEREXIT=%ERRORLEVEL%"
type "%ALLOG%"
if not "%ALCOMPILEREXIT%"=="0" (
  del "%ALLOG%" >nul 2>&1
  echo [al-build] BUILD FAILED - compiler exited with %ALCOMPILEREXIT%. 1>&2
  exit /b 1
)

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
