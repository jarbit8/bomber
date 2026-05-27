@echo off
cd /d D:\Games\Marcador
echo.
echo  === BOMBERMAN 4 ===
echo.
python setup.py
if errorlevel 1 goto fin
echo.
python detector.py
:fin
pause
