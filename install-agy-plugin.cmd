@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-agy-plugin.ps1" %*
exit /b %errorlevel%
