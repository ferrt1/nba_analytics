# scripts/init_db.py

import sqlite3
from pathlib import Path

DB_PATH = Path("db/nba.db")
DB_PATH.parent.mkdir(exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE games (
    game_id TEXT PRIMARY KEY,
    season TEXT,
    game_date TEXT,
    matchup TEXT,
    home_team TEXT,
    home_tricode TEXT,
    away_team TEXT
    ,away_tricode TEXT
)
""")

cur.execute("""
CREATE TABLE player_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    player_id INTEGER NOT NULL,
    player_name TEXT NOT NULL,

    minutes TEXT,        

    team_id INTEGER,
    team_tricode TEXT,

    points INTEGER,
    rebounds INTEGER,
    assists INTEGER,
    steals INTEGER,
    blocks INTEGER,

    fgm INTEGER,
    fga INTEGER,
    fg3m INTEGER,
    fg3a INTEGER,

    turnovers INTEGER,
    fouls INTEGER
)
""")

conn.commit()
conn.close()

print("✅ Base de datos creada correctamente")
