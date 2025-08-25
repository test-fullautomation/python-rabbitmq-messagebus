@echo off
REM Define shortnames and corresponding python files
setlocal enabledelayedexpansion

REM Check for input
if "%~1"=="" (
    echo Usage: run_sample.bat [shortname] [args...]
    echo Example: run_sample.bat basic_async arg1 arg2
    echo Supported shortnames and files:
    for %%f in (*.py) do (
        set "fname=%%~nf"
        for /f "tokens=1,2 delims=_" %%a in ("!fname!") do (
            echo %%a_%%b: %%f
        )
    )
    exit /b 1
)

REM Match shortname to file
set "pyfile="
for %%f in (*.py) do (
    echo File name: %%~nf
    set "fname=%%~nf"
    for /f "tokens=1,2 delims=_" %%a in ("!fname!") do (
        set "shortname=%%a_%%b"
        echo Shortname: !shortname!
        if /I "!shortname!"=="%~1" (
            set "pyfile=%%~nf.py"
            echo selected !pyfile!
            goto :found
        )
    )
)

:found
REM Add more matches as needed

if "%pyfile%"=="" (
    echo Unknown shortname: %~1
    exit /b 1
)

"%RobotPythonPath%\python" %pyfile% %2 %3 %4 %5 %6 %7 %8 %9
REM "%RobotPythonPath%\python" basic_async_producer_consumer_sample.py %*