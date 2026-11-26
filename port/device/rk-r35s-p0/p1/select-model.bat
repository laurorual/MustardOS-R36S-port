@echo off
rem SPDX-License-Identifier: MIT
rem MustardOS for R36S/R35S (unofficial port): choose your console model.
rem Double-click it on the card's boot partition. It writes model.txt next
rem to itself; the console applies it at its next start (it restarts once
rem by itself). EXPERIMENTAL: only the R36S-V12 Panel 0 / R35S is tested.
setlocal EnableDelayedExpansion
cd /d "%~dp0"
if not exist models.txt (
    echo models.txt not found: run this from the card's boot partition.
    pause
    exit /b 1
)
echo MustardOS for R36S/R35S: console model
echo.
if exist model.txt (
    set /p cur=<model.txt
    echo Current choice: !cur!
) else (
    echo Current choice: none ^(the console keeps its model^)
)
if exist model.txt.failed echo Note: the console did not accept the model in model.txt.failed.
if exist model.txt.unknown echo Note: the console did not know the model in model.txt.unknown.
echo.
set i=0
for /f "usebackq tokens=1,* delims=	" %%a in ("models.txt") do (
    set /a i+=1
    set "id!i!=%%a"
    set "name!i!=%%b"
    echo   !i!  %%b
)
echo.
set "n="
set /p n=Number of your model (Enter = cancel):
if "%n%"=="" (
    echo Nothing changed.
    pause
    exit /b 0
)
set "id=!id%n%!"
set "name=!name%n%!"
if "%id%"=="" (
    echo No model %n%. Nothing changed.
    pause
    exit /b 1
)
> model.txt echo %id%
if exist model.txt.failed del model.txt.failed
if exist model.txt.unknown del model.txt.unknown
echo.
echo Chosen: %name%
echo Eject the card, put it in slot 1 and power on. The console restarts
echo once by itself to apply it. If the screen stays black or wrong for
echo more than a minute, hold Power to turn it off and on again: it goes
echo back to the previous model by itself.
pause
