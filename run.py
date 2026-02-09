#!/usr/bin/env python3
"""
NBA Analytics - Launcher
Descarga boxscores y abre la aplicación web automáticamente
"""

import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

# Obtener la ruta del proyecto
PROJECT_DIR = Path(__file__).parent.absolute()

def run_command(cmd, description):
    """Ejecuta un comando y muestra el progreso"""
    print(f"\n{'='*60}")
    print(f"📍 {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, shell=True, cwd=PROJECT_DIR, check=True)
        print(f"✅ {description} completado\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error en {description}: {e}\n")
        return False

def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║          🏀 NBA ANALYTICS LAUNCHER 🏀                    ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Paso 1: Descargar boxscores
    print("📥 Descargando boxscores...")
    fetch_cmd = f"{sys.executable} scripts/fetch/fetch_boxscore.py"
    if not run_command(fetch_cmd, "Descarga de boxscores"):
        print("⚠️  Continuando sin actualizar boxscores...")
    
    # Paso 2: Iniciar servidor Flask
    print("🚀 Iniciando servidor en http://localhost:5000")
    print("   Presiona Ctrl+C para detener el servidor\n")
    
    # Esperar un poco para que se inicie
    time.sleep(1)
    
    # Abrir navegador automáticamente
    try:
        print("🌐 Abriendo navegador...")
        webbrowser.open("http://localhost:5000")
    except Exception as e:
        print(f"⚠️  No se pudo abrir el navegador automáticamente: {e}")
        print("   Abre manualmente: http://localhost:5000")
    
    # Iniciar Flask
    app_cmd = f"{sys.executable} web/app.py"
    subprocess.run(app_cmd, shell=True, cwd=PROJECT_DIR)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Servidor detenido")
        sys.exit(0)
