@echo off
cd /d D:\Games\Marcador
echo.
echo  === BOMBERMAN 4 ===
echo.
echo  Paso 1: Generando tabla de probabilidades...
python simulacion_tabla.py
if errorlevel 1 goto error
echo.
echo  Paso 2: Configurando jugadores...
python setup.py
echo.
echo  Paso 3: Iniciando detector...
python detector.py
pause
