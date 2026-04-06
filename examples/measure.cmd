@echo off
setlocal enabledelayedexpansion
set "str=%~1"
set "len=0"
:loop
if not "!str!"=="" (
    set "str=!str:~1!"
    set /a len+=1
    goto loop
)
echo !len!