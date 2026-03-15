"""
Fetches NBA player props from Pinnacle's public API (no API key needed).
Cache TTL: 60 minutes — avoids unnecessary requests.
Only 2 requests per run (matchups + markets).
"""

import json
import re
import requests
from pathlib import Path
from datetime import datetime

BASE_URL = "https://guest.api.arcadia.pinnacle.com/0.1"
LEAGUE_ID = 487  # NBA
CACHE_FILE = Path(__file__).parent.parent.parent / "data" / "raw" / "odds_cache.json"
CACHE_TTL_MINUTES = 60

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

# Map Pinnacle units to our stat keys
UNITS_TO_STAT = {
    "Points":                "points",
    "Rebounds":              "rebounds",
    "Assists":               "assists",
    "ThreePointFieldGoals":  "fg3m",
    "Blocks":                "blocks",
    "Steals":                "steals",
    "PointsReboundsAssist":  "pra",
    "PointsReboundsAssists": "pra",
}


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
    if _cache_is_fresh():
        print("Odds cache is fresh, skipping fetch")
        return

    print("Fetching NBA matchups from Pinnacle...")

    # 1. Get all matchups (games + player props)
    try:
        resp = requests.get(
            f"{BASE_URL}/leagues/{LEAGUE_ID}/matchups",
            headers=HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        matchups = resp.json()
    except Exception as e:
        print(f"Error fetching matchups: {e}")
        return

    # 2. Get all markets (lines + odds)
    try:
        resp = requests.get(
            f"{BASE_URL}/leagues/{LEAGUE_ID}/markets/straight",
            headers=HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        markets = resp.json()
    except Exception as e:
        print(f"Error fetching markets: {e}")
        return

    # Index markets by matchupId
    markets_by_matchup = {}
    for m in markets:
        mid = m.get("matchupId")
        if mid and m.get("type") == "total":
            markets_by_matchup[mid] = m

    # Build parent game info (team names)
    games = {}
    for item in matchups:
        if item.get("type") == "matchup":
            parent = item.get("parent") or item
            pid = parent.get("id") or item.get("parentId") or item.get("id")
            participants = parent.get("participants") or item.get("participants", [])
            home = away = ""
            for p in participants:
                if p.get("alignment") == "home":
                    home = p.get("name", "")
                elif p.get("alignment") == "away":
                    away = p.get("name", "")
            if home and away:
                games[pid] = {"home": home, "away": away}

    # Also extract game info from special items' parent field
    for item in matchups:
        if item.get("type") == "special" and item.get("parent"):
            parent = item["parent"]
            pid = parent.get("id")
            if pid and pid not in games:
                participants = parent.get("participants", [])
                home = away = ""
                for p in participants:
                    if p.get("alignment") == "home":
                        home = p.get("name", "")
                    elif p.get("alignment") == "away":
                        away = p.get("name", "")
                if home and away:
                    games[pid] = {"home": home, "away": away}

    # Extract player props
    all_props = []
    for item in matchups:
        if item.get("type") != "special":
            continue
        special = item.get("special", {})
        if special.get("category") != "Player Props":
            continue

        stat = UNITS_TO_STAT.get(item.get("units", ""))
        if not stat:
            continue

        # Parse player name from description: "LeBron James (Points)"
        desc = special.get("description", "")
        match = re.match(r"^(.+?)\s*\(", desc)
        if not match:
            continue
        player_name = match.group(1).strip()

        # Get Over/Under participant IDs
        over_id = under_id = None
        for p in item.get("participants", []):
            if p.get("name") == "Over":
                over_id = p.get("id")
            elif p.get("name") == "Under":
                under_id = p.get("id")

        # Find market for this prop
        market = markets_by_matchup.get(item.get("id"))
        if not market:
            continue

        line = None
        over_odds = None
        under_odds = None
        for price in market.get("prices", []):
            if price.get("participantId") == over_id:
                line = price.get("points")
                over_odds = price.get("price")
            elif price.get("participantId") == under_id:
                under_odds = price.get("price")

        if line is None:
            continue

        # Get team names from parent game
        parent_id = item.get("parentId")
        game = games.get(parent_id, {})

        all_props.append({
            "player":     player_name,
            "stat":       stat,
            "line":       line,
            "over_odds":  over_odds,
            "under_odds": under_odds,
            "home_team":  game.get("home", ""),
            "away_team":  game.get("away", ""),
        })

    # Count props per game for logging
    game_counts = {}
    for p in all_props:
        key = f"{p['away_team']} @ {p['home_team']}"
        game_counts[key] = game_counts.get(key, 0) + 1
    for matchup, count in sorted(game_counts.items()):
        print(f"  {matchup}: {count} props")

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump({"fetched_at": datetime.now().isoformat(), "props": all_props}, f)
    print(f"Cached {len(all_props)} player props")


if __name__ == "__main__":
    fetch_odds()
