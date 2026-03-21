# scripts/db/load_tracking.py
# Loads tracking JSON files into the player_stats table.

import sqlite3
import json
import unicodedata
from pathlib import Path


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

DB_PATH = Path("db/nba.db")
TRACKING_DIR = Path("data/raw/tracking")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Ensure columns exist (migration for older DBs)
for stmt in (
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

# Build name lookup: ascii name -> DB name (with accents)
cur.execute('SELECT DISTINCT player_name FROM player_stats')
name_map = {}
for (db_name,) in cur.fetchall():
    name_map[strip_accents(db_name)] = db_name

updated = 0
for file in TRACKING_DIR.glob("tracking_*.json"):
    game_id = file.stem.replace("tracking_", "")

    with open(file, "r", encoding="utf-8") as f:
        tracking = json.load(f)

    for pname, stats in tracking.items():
        db_name = name_map.get(pname, pname)
        cur.execute("""
            UPDATE player_stats
            SET reb_chances_off=?, reb_chances_def=?, reb_chances=?,
                secondary_ast=?, usage_pct=?
            WHERE game_id=? AND player_name=? AND reb_chances IS NULL
        """, (
            stats.get("reb_chances_off"),
            stats.get("reb_chances_def"),
            stats.get("reb_chances"),
            stats.get("secondary_ast"),
            stats.get("usage_pct"),
            game_id, db_name,
        ))
        updated += cur.rowcount

conn.commit()
conn.close()

print(f"✅ Tracking data loaded: {updated} rows updated")
