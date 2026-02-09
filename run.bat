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

REM Ejecutar el script Python
python run.py

pause
