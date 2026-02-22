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

def cleanup_old_game_files():
    """Elimina archivos de games de temporadas anteriores y snapshots diarios viejos."""
    data_dir = PROJECT_DIR / "data" / "raw"
    removed = 0
    # Borrar archivos con timestamp de ambas temporadas (los fijos no tienen _ después del año)
    for f in data_dir.glob("games_2024_25_*.json"):
        f.unlink()
        removed += 1
    for f in data_dir.glob("games_2025_26_*.json"):
        f.unlink()
        removed += 1
    # Borrar snapshots diarios generados por nba_daily (games_YYYY-MM-DD.json)
    for f in data_dir.glob("games_20??-??-??.json"):
        f.unlink()
        removed += 1
    if removed:
        print(f"🗑️  Eliminados {removed} archivos de games obsoletos")


def main():
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║          🏀 NBA ANALYTICS LAUNCHER 🏀                    ║
    ╚═══════════════════════════════════════════════════════════╝
    """)

    # Paso 1: Limpiar archivos viejos
    cleanup_old_game_files()

    # Paso 2: Descargar lista de partidos
    print("📅 Actualizando partidos 2024-25 y 2025-26...")
    games_cmd = f"{sys.executable} scripts/fetch/fetch_games.py"
    if not run_command(games_cmd, "Descarga de partidos 2025-26"):
        print("⚠️  Continuando sin actualizar lista de partidos...")

    # Paso 3: Insertar partidos en la DB
    if not run_command(f"{sys.executable} scripts/db/load_games.py", "Carga de partidos en DB"):
        print("⚠️  Continuando sin actualizar games en DB...")

    # Paso 4: Descargar boxscores
    print("📥 Descargando boxscores...")
    fetch_cmd = f"{sys.executable} scripts/fetch/fetch_boxscore.py"
    if not run_command(fetch_cmd, "Descarga de boxscores"):
        print("⚠️  Continuando sin actualizar boxscores...")

    # Paso 5: Insertar stats en la DB
    if not run_command(f"{sys.executable} scripts/db/load_stats.py", "Carga de stats en DB"):
        print("⚠️  Continuando sin actualizar stats en DB...")

    # Iniciar servidor Flask
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
