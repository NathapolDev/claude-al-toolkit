@echo off
setlocal
rem ---------------------------------------------------------------------------
rem Launches the AL LSP MCP bridge (al-lsp-mcp.py), exposing AL Language Server
rem semantic code intelligence as MCP tools over stdio (or via --cli).
rem
rem stdout belongs to the MCP stdio protocol (or --cli JSON output): every
rem message from this script goes to stderr.
rem ---------------------------------------------------------------------------

where python >nul 2>&1
if errorlevel 1 goto nopython

python -u "%~dp0al-lsp-mcp.py" %*
exit /b %errorlevel%

:nopython
echo [al-lsp-mcp] python was not found on PATH. Install Python 3 and ensure python.exe is on PATH. 1>&2
exit /b 1
