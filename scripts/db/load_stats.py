# scripts/load_stats.py

import sqlite3
import json
from pathlib import Path

DB_PATH = Path("db/nba.db")
BOXSCORES_DIR = Path("data/raw/boxscores")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Ensure columns exist (migration for older DBs)
for stmt in (
    "ALTER TABLE player_stats ADD COLUMN team_id INTEGER",
    "ALTER TABLE player_stats ADD COLUMN team_tricode TEXT",
    "ALTER TABLE player_stats ADD COLUMN ftm INTEGER",
    "ALTER TABLE player_stats ADD COLUMN fta INTEGER",
    "ALTER TABLE player_stats ADD COLUMN reb_chances_off INTEGER",
    "ALTER TABLE player_stats ADD COLUMN reb_chances_def INTEGER",
    "ALTER TABLE player_stats ADD COLUMN reb_chances INTEGER",
    "ALTER TABLE player_stats ADD COLUMN secondary_ast INTEGER",
    "ALTER TABLE player_stats ADD COLUMN potential_ast INTEGER",
    "ALTER TABLE player_stats ADD COLUMN usage_pct REAL",
):
    try:
        cur.execute(stmt)
    except Exception:
        pass

insert_sql = """
INSERT OR IGNORE INTO player_stats (
    game_id,
    player_id,
    player_name,
    minutes,
    team_id,
    team_tricode,
    points,
    rebounds,
    assists,
    steals,
    blocks,
    fgm,
    fga,
    fg3m,
    fg3a,
    ftm,
    fta,
    turnovers,
    fouls
 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

for file in BOXSCORES_DIR.glob("boxscore_*.json"):
    game_id = file.stem.replace("boxscore_", "")

    with open(file, "r", encoding="utf-8") as f:
        players = json.load(f)

    for p in players:
        cur.execute(
            insert_sql,
            (
                game_id,
                p["personId"],
                f'{p["firstName"]} {p["familyName"]}',
                p.get("minutes"),                  # 👈 NUEVO
                p.get("teamId"),
                p.get("teamTricode"),
                p.get("points"),
                p.get("reboundsTotal"),
                p.get("assists"),
                p.get("steals"),
                p.get("blocks"),
                p.get("fieldGoalsMade"),
                p.get("fieldGoalsAttempted"),
                p.get("threePointersMade"),
                p.get("threePointersAttempted"),
                p.get("freeThrowsMade"),
                p.get("freeThrowsAttempted"),
                p.get("turnovers"),
                p.get("foulsPersonal"),
            ),
        )

conn.commit()
conn.close()

print("✅ Player stats cargadas correctamente")
