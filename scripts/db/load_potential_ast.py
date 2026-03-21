# scripts/db/load_potential_ast.py
# Loads potential assists JSON files into the player_stats table.

import sqlite3
import json
import unicodedata
from pathlib import Path

DB_PATH = Path("db/nba.db")
PAST_DIR = Path("data/raw/potential_ast")


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Ensure column exists
try:
    cur.execute("ALTER TABLE player_stats ADD COLUMN potential_ast INTEGER")
except Exception:
    pass

# Build name lookup: ascii name -> DB name (with accents)
cur.execute('SELECT DISTINCT player_name FROM player_stats')
name_map = {}
for (db_name,) in cur.fetchall():
    name_map[strip_accents(db_name).lower()] = db_name

updated = 0
for file in sorted(PAST_DIR.glob("past_*.json")):
    game_date = file.stem.replace("past_", "")

    with open(file, "r", encoding="utf-8") as f:
        players = json.load(f)

    for p in players:
        api_name = p["player_name"]
        db_name = name_map.get(strip_accents(api_name).lower(), api_name)
        cur.execute("""
            UPDATE player_stats
            SET potential_ast=?
            WHERE player_name=? AND potential_ast IS NULL
              AND game_id IN (SELECT game_id FROM games WHERE game_date=?)
        """, (p["potential_ast"], db_name, game_date))
        updated += cur.rowcount

conn.commit()
conn.close()

print(f"Potential assists loaded: {updated} rows updated")
