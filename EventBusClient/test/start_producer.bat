@echo off
setlocal

REM Set PYTHONPATH to the parent directory of this file
set "PYTHONPATH=%~dp0.."

REM Run the python command
"%RobotPythonPath%\python" test.py producer