# scripts/fetch_games.py

from nba_api.stats.endpoints import leaguegamefinder
from pathlib import Path
import json
import math


SEASONS = ["2024-25", "2025-26"]

DATA_DIR = Path("data/raw")
DATA_DIR.mkdir(parents=True, exist_ok=True)

def clean_nan(obj):
    if isinstance(obj, float) and math.isnan(obj):
        return None
    elif isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(i) for i in obj]
    else:
        return obj

def fetch_games_for_season(season: str) -> list[dict]:
    print(f"📥 Descargando partidos temporada {season}...")

    gamefinder = leaguegamefinder.LeagueGameFinder(
        season_nullable=season,
        league_id_nullable="00"  # NBA
    )

    df = gamefinder.get_data_frames()[0]

    games = clean_nan(df.to_dict(orient="records"))

    print(f"✅ {len(games)} partidos obtenidos ({season})")
    return games


def save_games(season: str, games: list[dict]) -> None:
    season_safe = season.replace("-", "_")
    file_path = DATA_DIR / f"games_{season_safe}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(games, f, indent=2)

    print(f"💾 Guardado en {file_path}")


def main():
    for season in SEASONS:
        games = fetch_games_for_season(season)
        save_games(season, games)


if __name__ == "__main__":
    main()
