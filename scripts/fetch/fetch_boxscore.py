# scripts/fetch_boxscore.py

from nba_api.stats.endpoints import boxscoretraditionalv3
from pathlib import Path
import json
import time
import math
import random


DATA_GAMES_DIR = Path("data/raw")
DATA_BOXSCORE_DIR = Path("data/raw/boxscores")

DATA_BOXSCORE_DIR.mkdir(parents=True, exist_ok=True)


def clean_nan(obj):
    if isinstance(obj, float) and math.isnan(obj):
        return None
    elif isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(i) for i in obj]
    else:
        return obj


def load_game_ids() -> set[str]:
    game_ids = set()

    for file in DATA_GAMES_DIR.glob("games_*.json"):
        with open(file, "r", encoding="utf-8") as f:
            games = json.load(f)

        for g in games:
            if g.get("WL") in ("W", "L"):
                game_ids.add(g["GAME_ID"])

    return game_ids


def fetch_boxscore(game_id: str, retries: int = 3) -> list[dict]:
    for attempt in range(1, retries + 1):
        try:
            print(f"📥 Boxscore GAME_ID={game_id} (intento {attempt})")

            boxscore = boxscoretraditionalv3.BoxScoreTraditionalV3(
                game_id=game_id,
                timeout=60,
            )

            df_players = boxscore.get_data_frames()[0]
            data = df_players.to_dict(orient="records")

            return clean_nan(data)

        except Exception as e:
            print(f"⚠️ Intento {attempt} falló: {e}")
            time.sleep(10 * attempt)

    raise RuntimeError(f"No se pudo descargar GAME_ID={game_id}")


def save_boxscore(game_id: str, players_stats: list[dict]) -> None:
    file_path = DATA_BOXSCORE_DIR / f"boxscore_{game_id}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(players_stats, f, indent=2, ensure_ascii=False)

    print(f"💾 Guardado {file_path}")


def main():
    game_ids = load_game_ids()
    print(f"🎯 Partidos finalizados encontrados: {len(game_ids)}")

    for game_id in sorted(game_ids):
        output_file = DATA_BOXSCORE_DIR / f"boxscore_{game_id}.json"

        if output_file.exists():
            continue

        try:
            players_stats = fetch_boxscore(game_id)
            
            if players_stats: # Solo guardar si funcionó
                save_boxscore(game_id, players_stats)
                # ⏳ 5. Pausa aleatoria para parecer humano
                time.sleep(random.uniform(3, 7))
            else:
                print(f"❌ Saltando GAME_ID {game_id} por exceso de errores.")

        except Exception as e:
            print(f"⚠️ Error inesperado en GAME_ID {game_id}: {e}")
            time.sleep(30) # Pausa larga si hay un error crítico

if __name__ == "__main__":
    main()
