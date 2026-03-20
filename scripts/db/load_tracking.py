# scripts/db/load_tracking.py
# Loads tracking JSON files into the player_stats table.

import sqlite3
import json
from pathlib import Path

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

updated = 0
for file in TRACKING_DIR.glob("tracking_*.json"):
    game_id = file.stem.replace("tracking_", "")

    with open(file, "r", encoding="utf-8") as f:
        tracking = json.load(f)

    for pname, stats in tracking.items():
        cur.execute("""
            UPDATE player_stats
            SET reb_chances_off=?, reb_chances_def=?, reb_chances=?,
                secondary_ast=?, potential_ast=?, usage_pct=?
            WHERE game_id=? AND player_name=? AND reb_chances IS NULL
        """, (
            stats.get("reb_chances_off"),
            stats.get("reb_chances_def"),
            stats.get("reb_chances"),
            stats.get("secondary_ast"),
            stats.get("potential_ast"),
            stats.get("usage_pct"),
            game_id, pname,
        ))
        updated += cur.rowcount

conn.commit()
conn.close()

print(f"✅ Tracking data loaded: {updated} rows updated")
