@echo off
chcp 936 >nul
cd /d "%~dp0"

net session >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Administrator rights required.
    echo Right-click this file and choose "Run as administrator".
    pause
    exit /b 1
)

echo ============================================================
echo   Flash HELLO firmware to BR23 internal Flash
echo   app.bin = locally built AC695N SDK hello world
echo   No TF card format, no fonts, no index.
echo ============================================================
echo.

REM -tonorflash and -format all match the known-good Asuka flash command.
REM -format all clears the previous firmware's VM area; cross-firmware VM data
REM is incompatible and can hang the app on boot. Uboot area (0x0-0x1000) is
REM never erased, so reflash capability is NOT affected.
isd_download.exe -tonorflash -dev br23 -boot 0x12000 -div8 -wait 300 -uboot uboot.boot -app app.bin -res tone.cfg cfg_tool.bin eq_cfg_hw.bin -format all -key key.txt -reboot 2500
set RC=%ERRORLEVEL%

echo.
if "%RC%"=="0" goto OK
echo [ERROR] downloader exited with code %RC%
goto END
:OK
echo [INFO] downloader exited normally.
echo Expected log: ERASE MODE : NONE / download complete / rebooting.
:END
pause
exit /b %RC%
