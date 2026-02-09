import json
import sqlite3
from pathlib import Path

DATA_DIR = Path("data/raw")
DB_PATH = Path("db/nba.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

seen_games = set()

for file in DATA_DIR.glob("games_*.json"):
    with open(file, "r", encoding="utf-8") as f:
        games = json.load(f)

    # Some files (snapshots created by scripts/tools/nba_daily.py) use a
    # different schema (lowercase keys like 'game_id'). Skip those files
    # since this loader expects NBA API export rows with 'GAME_ID'.
    if not isinstance(games, list) or len(games) == 0:
        print(f"⚠️ Skipping {file} (empty or unexpected format)")
        continue

    first = games[0]
    if "GAME_ID" not in first:
        print(f"⚠️ Skipping {file} (no GAME_ID key, probably a snapshot)")
        continue

    for g in games:
        game_id = g["GAME_ID"]

        if game_id in seen_games:
            continue

        seen_games.add(game_id)

        # Parse local / visitante desde MATCHUP
        if "vs." in g["MATCHUP"]:
            home_team = g["MATCHUP"].split(" vs. ")[0]
            away_team = g["MATCHUP"].split(" vs. ")[1]
        else:
            away_team = g["MATCHUP"].split(" @ ")[0]
            home_team = g["MATCHUP"].split(" @ ")[1]

        cursor.execute("""
        INSERT OR IGNORE INTO games
        (game_id, game_date, season, home_team, away_team)
        VALUES (?, ?, ?, ?, ?)
        """, (
            game_id,
            g["GAME_DATE"],
            g["SEASON_ID"],
            home_team,
            away_team
        ))

conn.commit()
conn.close()

print("✅ Juegos cargados en SQLite")
