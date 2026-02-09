import sqlite3
import json
from pathlib import Path

DB = Path("db/nba.db")
BOX_DIR = Path("data/raw/boxscores")

conn = sqlite3.connect(DB)
cur = conn.cursor()

updated = 0

for f in BOX_DIR.glob("boxscore_*.json"):
    game_id = f.stem.replace("boxscore_", "")

    with open(f, "r", encoding="utf-8") as fh:
        players = json.load(fh)

    # build mapping of teamName -> tricode and teamCity -> tricode
    mapping_name = {}
    mapping_city = {}
    for p in players:
        tn = p.get("teamName")
        tc = p.get("teamCity")
        tr = p.get("teamTricode") or p.get("team_tricode")
        if tn and tr:
            mapping_name[tn.strip().lower()] = tr
        if tc and tr:
            mapping_city[tc.strip().lower()] = tr

    if not mapping_name and not mapping_city:
        continue

    # get existing home/away team names from games
    cur.execute("SELECT home_team, away_team, home_tricode, away_tricode FROM games WHERE game_id = ?", (game_id,))
    row = cur.fetchone()
    if not row:
        continue

    home_team, away_team, home_tr, away_tr = row

    new_home = home_tr
    new_away = away_tr

    # try match by teamName
    if home_team and home_team.strip().lower() in mapping_name:
        new_home = mapping_name[home_team.strip().lower()]
    elif home_team and home_team.strip().lower() in mapping_city:
        new_home = mapping_city[home_team.strip().lower()]

    if away_team and away_team.strip().lower() in mapping_name:
        new_away = mapping_name[away_team.strip().lower()]
    elif away_team and away_team.strip().lower() in mapping_city:
        new_away = mapping_city[away_team.strip().lower()]

    # if still missing but we have two distinct tricodes, assign remaining
    tricodes = set(mapping_name.values()) if mapping_name else set(mapping_city.values())
    if (not new_home or not new_away) and len(tricodes) == 2:
        # assign any not equal
        if not new_home:
            cand = [t for t in tricodes if t != new_away]
            if cand:
                new_home = cand[0]
        if not new_away:
            cand = [t for t in tricodes if t != new_home]
            if cand:
                new_away = cand[0]

    if new_home != home_tr or new_away != away_tr:
        cur.execute("UPDATE games SET home_tricode = ?, away_tricode = ? WHERE game_id = ?", (new_home, new_away, game_id))
        updated += 1

conn.commit()
conn.close()
print(f"Updated {updated} games tricodes")
