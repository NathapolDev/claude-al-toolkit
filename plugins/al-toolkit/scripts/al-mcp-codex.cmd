@echo off
setlocal
rem Start without a project. Skills load the selected workspace via al_addproject.
rem A shell environment change cannot update an already-running MCP process.
set "ALBIN="
for /f "delims=" %%B in ('call "%~dp0find-al-bin.cmd" altool.exe') do set "ALBIN=%%B"
if not defined ALBIN (
  echo [al-mcp] AL MCP server cannot start - altool.exe was not found. 1>&2
  exit /b 1
)
"%ALBIN%\altool.exe" launchmcpserver --transport stdio
exit /b %errorlevel%
