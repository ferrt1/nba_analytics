# scripts/fetch/fetch_tracking.py
# Fetches tracking (rebound chances, potential assists) and usage data
# for games that don't have it yet. Saves to data/raw/tracking/ as JSON.

from nba_api.stats.endpoints import boxscoreplayertrackv3, boxscoreusagev3
from pathlib import Path
import sqlite3
import json
import time
import random

DB_PATH = Path("db/nba.db")
TRACKING_DIR = Path("data/raw/tracking")
TRACKING_DIR.mkdir(parents=True, exist_ok=True)


def get_games_missing_tracking() -> list[str]:
    """Get game IDs that have player_stats but no tracking data."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT game_id FROM player_stats
        WHERE reb_chances IS NULL AND game_id LIKE '002%'
    """)
    gids = [r[0] for r in cur.fetchall()]
    conn.close()
    return gids


def fetch_tracking(game_id: str) -> dict:
    """Fetch tracking + usage for a game. Returns {player_name: {stats}}."""
    result = {}

    try:
        track = boxscoreplayertrackv3.BoxScorePlayerTrackV3(
            game_id=game_id, timeout=60
        )
        data = track.get_dict()
        bp = data.get("boxScorePlayerTrack", {})
        for side in ("homeTeam", "awayTeam"):
            for p in bp.get(side, {}).get("players", []):
                name = f"{p.get('firstName', '')} {p.get('familyName', '')}".strip()
                s = p.get("statistics", {})
                result[name] = {
                    "reb_chances_off": s.get("reboundChancesOffensive"),
                    "reb_chances_def": s.get("reboundChancesDefensive"),
                    "reb_chances": s.get("reboundChancesTotal"),
                    "secondary_ast": s.get("secondaryAssists"),
                }
    except Exception as e:
        print(f"  Tracking error {game_id}: {e}")

    try:
        usage = boxscoreusagev3.BoxScoreUsageV3(game_id=game_id, timeout=60)
        data = usage.get_dict()
        bu = data.get("boxScoreUsage", {})
        for side in ("homeTeam", "awayTeam"):
            for p in bu.get(side, {}).get("players", []):
                name = f"{p.get('firstName', '')} {p.get('familyName', '')}".strip()
                s = p.get("statistics", {})
                usg = s.get("usagePercentage")
                if usg is not None:
                    usg = round(usg * 100, 1)
                if name not in result:
                    result[name] = {}
                result[name]["usage_pct"] = usg
    except Exception as e:
        print(f"  Usage error {game_id}: {e}")

    return result


def main():
    gids = get_games_missing_tracking()
    print(f"Games missing tracking data: {len(gids)}")

    for i, gid in enumerate(sorted(gids)):
        out_file = TRACKING_DIR / f"tracking_{gid}.json"
        if out_file.exists():
            continue

        print(f"  [{i+1}/{len(gids)}] Fetching tracking for {gid}")
        tracking = fetch_tracking(gid)

        if tracking:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(tracking, f, indent=2, ensure_ascii=False)

        time.sleep(random.uniform(1, 3))

    print("Done fetching tracking data")


if __name__ == "__main__":
    main()
