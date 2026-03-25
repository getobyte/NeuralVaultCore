@echo off
REM NeuralVaultCore Windows Service Helper
REM Usage: nvc-service.bat start|stop|status

SET NVC_DIR=%~dp0..
SET PYTHON=python

if "%1"=="start" (
    start /B "" %PYTHON% "%NVC_DIR%\nvc.py" daemon start
    echo NVC daemon started.
    goto :eof
)
if "%1"=="stop" (
    %PYTHON% "%NVC_DIR%\nvc.py" daemon stop
    echo NVC daemon stopped.
    goto :eof
)
if "%1"=="status" (
    %PYTHON% "%NVC_DIR%\nvc.py" daemon status
    goto :eof
)
echo Usage: nvc-service.bat start^|stop^|status
