# scripts/fetch/fetch_potential_ast.py
# Fetches real potential assists from leaguedashptstats endpoint.
# Saves one JSON per game date to data/raw/potential_ast/

from nba_api.stats.endpoints import leaguedashptstats
from pathlib import Path
import sqlite3
import json
import time
import random

DB_PATH = Path("db/nba.db")
OUT_DIR = Path("data/raw/potential_ast")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def get_dates_missing_potential_ast() -> list[str]:
    """Get game dates that have player_stats but no potential_ast data."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT g.game_date
        FROM player_stats ps
        JOIN games g ON ps.game_id = g.game_id
        WHERE ps.potential_ast IS NULL AND ps.game_id LIKE '002%'
        ORDER BY g.game_date DESC
    """)
    dates = [r[0] for r in cur.fetchall()]
    conn.close()
    return dates


def fetch_potential_ast_for_date(game_date: str) -> list[dict]:
    """Fetch potential assists for all players on a given date.
    game_date format: YYYY-MM-DD, API wants MM/DD/YYYY."""
    parts = game_date.split("-")
    api_date = f"{parts[1]}/{parts[2]}/{parts[0]}"

    stats = leaguedashptstats.LeagueDashPtStats(
        pt_measure_type="Passing",
        player_or_team="Player",
        per_mode_simple="Totals",
        season=get_season_for_date(game_date),
        season_type_all_star="Regular Season",
        date_from_nullable=api_date,
        date_to_nullable=api_date,
        timeout=60,
    )
    df = stats.get_data_frames()[0]
    results = []
    for _, row in df.iterrows():
        results.append({
            "player_name": row["PLAYER_NAME"],
            "potential_ast": int(row["POTENTIAL_AST"]),
        })
    return results


def get_season_for_date(game_date: str) -> str:
    """Determine NBA season string from game date."""
    year, month = int(game_date[:4]), int(game_date[5:7])
    if month >= 10:
        return f"{year}-{str(year + 1)[2:]}"
    else:
        return f"{year - 1}-{str(year)[2:]}"


def main():
    dates = get_dates_missing_potential_ast()
    print(f"Dates missing potential_ast: {len(dates)}")

    for i, d in enumerate(dates):
        out_file = OUT_DIR / f"past_{d}.json"
        if out_file.exists():
            continue

        print(f"  [{i+1}/{len(dates)}] Fetching potential_ast for {d}")
        try:
            data = fetch_potential_ast_for_date(d)
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"    Error: {e}")

        time.sleep(random.uniform(1, 3))

    print("Done fetching potential assists")


if __name__ == "__main__":
    main()
