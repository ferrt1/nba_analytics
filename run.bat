@echo off
REM NBA Analytics Launcher - Windows Batch Script
REM Ejecuta el launcher de Python

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║          🏀 NBA ANALYTICS LAUNCHER 🏀                    ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM Cambiar al directorio del proyecto
cd /d "%~dp0"

REM Activar el entorno virtual si existe
if exist ".venv\Scripts\activate.bat" (
    echo Activando entorno virtual .venv...
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo Activando entorno virtual venv...
    call venv\Scripts\activate.bat
) else (
    echo ADVERTENCIA: No se encontro entorno virtual. Usando Python del sistema.
)

REM Ejecutar el script Python
python run.py

pause
