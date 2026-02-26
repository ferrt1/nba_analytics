"""
Fetches NBA player props from The Odds API and caches them locally.
Cache TTL: 60 minutes — avoids burning API credits on repeated runs.
Free tier: 500 requests/month (~8 games × 1 req each + 1 events = ~9/day).
"""

import json
import os
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")

API_KEY  = os.getenv("ODDS_API_KEY", "")
BASE_URL = "https://api.the-odds-api.com/v4"
CACHE_FILE = Path(__file__).parent.parent.parent / "data" / "raw" / "odds_cache.json"
CACHE_TTL_MINUTES = 60

MARKET_TO_STAT = {
    "player_points":                    "points",
    "player_rebounds":                  "rebounds",
    "player_assists":                   "assists",
    "player_threes":                    "fg3m",
    "player_blocks":                    "blocks",
    "player_steals":                    "steals",
    "player_points_rebounds_assists":   "pra",
}
MARKETS = ",".join(MARKET_TO_STAT.keys())


def _cache_is_fresh():
    if not CACHE_FILE.exists():
        return False
    try:
        with open(CACHE_FILE) as f:
            cached = json.load(f)
        cached_at = datetime.fromisoformat(cached.get("fetched_at", "2000-01-01"))
        age = (datetime.now() - cached_at).total_seconds() / 60
        return age < CACHE_TTL_MINUTES
    except Exception:
        return False


def fetch_odds():
    if not API_KEY:
        print("⚠️  ODDS_API_KEY no configurada en .env — saltando fetch de props")
        return

    if _cache_is_fresh():
        print("Odds cache is fresh, skipping API fetch")
        return

    print("Fetching NBA events from The Odds API...")
    try:
        resp = requests.get(
            f"{BASE_URL}/sports/basketball_nba/events",
            params={"apiKey": API_KEY},
            timeout=30,
        )
        resp.raise_for_status()
        events = resp.json()
    except Exception as e:
        print(f"Error fetching events: {e}")
        return

    print(f"Found {len(events)} events, fetching player props...")
    all_props = []

    for event in events:
        event_id  = event.get("id", "")
        home_team = event.get("home_team", "")
        away_team = event.get("away_team", "")

        try:
            odds_resp = requests.get(
                f"{BASE_URL}/sports/basketball_nba/events/{event_id}/odds",
                params={
                    "apiKey":      API_KEY,
                    "regions":     "us",
                    "markets":     MARKETS,
                    "oddsFormat":  "american",
                },
                timeout=30,
            )
            odds_resp.raise_for_status()
            event_odds = odds_resp.json()
        except Exception as e:
            print(f"  Error props for {away_team} @ {home_team}: {e}")
            continue

        # Collect props — first bookmaker wins for each (player, stat) pair
        seen = set()
        for bm in event_odds.get("bookmakers", []):
            for market in bm.get("markets", []):
                stat = MARKET_TO_STAT.get(market.get("key", ""))
                if not stat:
                    continue

                players: dict = {}
                for outcome in market.get("outcomes", []):
                    pname = outcome.get("description", "")
                    side  = outcome.get("name")
                    point = outcome.get("point")
                    price = outcome.get("price")
                    if pname not in players:
                        players[pname] = {"line": None, "over": None, "under": None}
                    if side == "Over":
                        players[pname]["line"] = point
                        players[pname]["over"] = price
                    elif side == "Under":
                        players[pname]["under"] = price

                for pname, data in players.items():
                    key = (pname, stat)
                    if key in seen:
                        continue
                    seen.add(key)
                    all_props.append({
                        "player":     pname,
                        "stat":       stat,
                        "line":       data["line"],
                        "over_odds":  data["over"],
                        "under_odds": data["under"],
                        "home_team":  home_team,
                        "away_team":  away_team,
                    })

        count = sum(1 for p in all_props if p["home_team"] == home_team)
        print(f"  {away_team} @ {home_team}: {count} props")

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump({"fetched_at": datetime.now().isoformat(), "props": all_props}, f)
    print(f"Cached {len(all_props)} player props")


if __name__ == "__main__":
    fetch_odds()
