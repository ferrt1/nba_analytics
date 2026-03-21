from flask import Flask, render_template, request, jsonify
import sqlite3
import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.tools.nba_daily import get_today_games

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'db', 'nba.db')

import time
import threading
from datetime import date

TODAY_GAMES_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'today_games.json')
_games_cache = {"data": [], "ts": 0, "fetching": False}

def _load_today_games_file():
    """Load today's games from JSON file (instant, no API call)."""
    try:
        if os.path.exists(TODAY_GAMES_PATH):
            with open(TODAY_GAMES_PATH, 'r') as f:
                data = json.load(f)
            if data.get("date") == str(date.today()):
                return data.get("games", [])
    except Exception:
        pass
    return None

def get_today_games_cached():
    now = time.time()
    if now - _games_cache["ts"] > 1800:
        # Try file first (instant, no network needed)
        file_games = _load_today_games_file()
        if file_games is not None:
            _games_cache["data"] = file_games
            _games_cache["ts"] = now
            return _games_cache["data"]
        # Fallback to NBA API in background (for localhost)
        if not _games_cache["fetching"]:
            _games_cache["fetching"] = True
            def _fetch():
                try:
                    _games_cache["data"] = get_today_games()
                except Exception:
                    _games_cache["data"] = []
                _games_cache["ts"] = time.time()
                _games_cache["fetching"] = False
            threading.Thread(target=_fetch, daemon=True).start()
    return _games_cache["data"]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    today_games = get_today_games_cached()
    return render_template(
        "index.html",
        today_games=today_games
    )


@app.route("/player")
def player():
    query_name = request.args.get("name")

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT player_name
        FROM player_stats
        WHERE player_name LIKE ?
        LIMIT 1
    """, (f"%{query_name}%",))

    row = cur.fetchone()
    

    if not row:
        today_games = get_today_games_cached()
        return render_template(
            "index.html",
            error="Jugador no encontrado",
            today_games=today_games
        )
    # determine player's current team — only real NBA tricodes (excludes All-Star game)
    cur.execute("""
        SELECT team_tricode
        FROM player_stats
        WHERE player_name = ? AND team_tricode IS NOT NULL
        ORDER BY id DESC
    """, (row["player_name"],))
    trow = next((r for r in cur.fetchall() if r[0] in NBA_TRICODES), None)
    player_team = None
    if trow:
        tricode = trow[0]
        # find a game record that uses this tricode to get a full team name
        cur.execute("""
            SELECT home_team, away_team, home_tricode, away_tricode
            FROM games
            WHERE home_tricode = ? OR away_tricode = ?
            ORDER BY game_date DESC
            LIMIT 1
        """, (tricode, tricode))
        grow = cur.fetchone()
        if grow:
            if grow[2] == tricode:
                player_team = grow[0]
            else:
                player_team = grow[1]

    conn.close()

    today_games = get_today_games_cached()
    return render_template(
        "index.html",
        player=row["player_name"],
        player_team=player_team,
        today_games=today_games
    )


@app.route("/api/player_stats")
def player_stats_api():
    player = request.args.get("player")
    stat = request.args.get("stat", "points")
    try:
        limit = request.args.get("limit", "10")
        if limit != "h2h":
            int(limit)  # validate it's a number
    except ValueError:
        return jsonify({"error": "Invalid limit"}), 400
    with_player = request.args.get("with_player", "")
    without_player = request.args.get("without_player", "")
    min_minutes = request.args.get("min_minutes", "")
    max_minutes = request.args.get("max_minutes", "")

    conn = get_db()
    cur = conn.cursor()

    stat_sql_map = {
        "points": "ps.points",
        "rebounds": "ps.rebounds",
        "assists": "ps.assists",
        "pra": "(ps.points + ps.rebounds + ps.assists)",
        "pa": "(ps.points + ps.assists)",
        "pr": "(ps.points + ps.rebounds)",
        "ra": "(ps.rebounds + ps.assists)",
        "sb": "(ps.steals + ps.blocks)",
        "minutes": "ps.minutes",
        "steals": "ps.steals",
        "blocks": "ps.blocks",
        "fgm": "ps.fgm",
        "fga": "ps.fga",
        "fg3m": "ps.fg3m",
        "fg3a": "ps.fg3a",
        "ftm": "ps.ftm",
        "fta": "ps.fta",
        "turnovers": "ps.turnovers",
        "fouls": "ps.fouls",
        "reb_chances": "ps.reb_chances",
        "potential_ast": "ps.potential_ast",
        "usage_pct": "ps.usage_pct",
    }
    stat_sql = stat_sql_map.get(stat)
    if not stat_sql:
        return jsonify({"error": "Invalid stat"}), 400

    # Teammate filter (with/without)
    teammate_filter = ""
    teammate_params = []
    if with_player:
        teammate_filter = "AND ps.game_id IN (SELECT game_id FROM player_stats WHERE player_name = ?)"
        teammate_params = [with_player]
    elif without_player:
        teammate_filter = "AND ps.game_id NOT IN (SELECT game_id FROM player_stats WHERE player_name = ?)"
        teammate_params = [without_player]

    # Minutes range filter
    minutes_filter = ""
    minutes_params = []
    if min_minutes:
        minutes_filter += " AND CAST(SUBSTR(ps.minutes, 1, INSTR(ps.minutes || ':', ':') - 1) AS INTEGER) >= ?"
        minutes_params.append(int(min_minutes))
    if max_minutes:
        minutes_filter += " AND CAST(SUBSTR(ps.minutes, 1, INSTR(ps.minutes || ':', ':') - 1) AS INTEGER) <= ?"
        minutes_params.append(int(max_minutes))

    # H2H special: determine opponent using today's schedule when possible
    if limit == "h2h":
        opponent = None
        player_team = None

        # try to get player's current team tricode — only real NBA tricodes (excludes All-Star)
        cur.execute("""
            SELECT team_tricode, game_id
            FROM player_stats
            WHERE player_name = ? AND team_tricode IS NOT NULL
            ORDER BY id DESC
        """, (player,))
        row = next((r for r in cur.fetchall() if r[0] in NBA_TRICODES), None)
        if row:
            player_team = row[0]

        # check today's games (cached) for opponent
        today_games = get_today_games_cached()
        try:
            if player_team and today_games:
                for g in today_games:
                    if g.get("home_tricode") == player_team:
                        opponent = g.get("away_tricode")
                        break
                    if g.get("away_tricode") == player_team:
                        opponent = g.get("home_tricode")
                        break
        except Exception:
            opponent = None

        # If we have an opponent, fetch last 10 vs that opponent
        if opponent and player_team:
            h2h_limit = 10
            cur.execute(f"""
                SELECT
                    g.game_date,
                    COALESCE(g.away_tricode, g.away_team) AS away_tri,
                    COALESCE(g.home_tricode, g.home_team) AS home_tri,
                    ps.team_tricode AS player_tri,
                    {stat_sql} AS value
                FROM player_stats ps
                JOIN games g ON ps.game_id = g.game_id
                WHERE ps.player_name = ? AND g.season NOT LIKE '3%'
                  AND ps.minutes NOT IN ('0:00', '0', '') AND (
                    (g.home_tricode = ? AND g.away_tricode = ?) OR
                    (g.away_tricode = ? AND g.home_tricode = ?)
                ) {teammate_filter} {minutes_filter}
                ORDER BY g.game_date DESC
                LIMIT ?
            """, (player, player_team, opponent, player_team, opponent, *teammate_params, *minutes_params, h2h_limit))
            rows = cur.fetchall()
        else:
            # fallback: return last 10 games normally
            cur.execute(f"""
                SELECT
                    g.game_date,
                    COALESCE(g.away_tricode, g.away_team) AS away_tri,
                    COALESCE(g.home_tricode, g.home_team) AS home_tri,
                    ps.team_tricode AS player_tri,
                    {stat_sql} AS value
                FROM player_stats ps
                JOIN games g ON ps.game_id = g.game_id
                WHERE ps.player_name = ? AND g.season NOT LIKE '3%'
                  AND ps.minutes NOT IN ('0:00', '0', '') {teammate_filter} {minutes_filter}
                ORDER BY g.game_date DESC
                LIMIT 10
            """, (player, *teammate_params, *minutes_params))
            rows = cur.fetchall()
    else:
        cur.execute(f"""
            SELECT
                g.game_date,
                COALESCE(g.away_tricode, g.away_team) AS away_tri,
                    COALESCE(g.home_tricode, g.home_team) AS home_tri,
                    ps.team_tricode AS player_tri,
                {stat_sql} AS value
            FROM player_stats ps
            JOIN games g ON ps.game_id = g.game_id
            WHERE ps.player_name = ? AND g.season NOT LIKE '3%'
              AND ps.minutes NOT IN ('0:00', '0', '') {teammate_filter} {minutes_filter}
            ORDER BY g.game_date DESC
            LIMIT ?
        """, (player, *teammate_params, *minutes_params, int(limit)))

        rows = cur.fetchall()
    conn.close()

    # Build labels: opponent tricode only
    # Build tooltip info: "vs OPP" (home) or "en OPP" (away)
    labels_out = []
    tooltip_labels = []
    for r in rows:
        player_tri = r["player_tri"]
        home_tri = r["home_tri"]
        away_tri = r["away_tri"]
        if player_tri == home_tri:
            opponent = away_tri
            tooltip_labels.append(f"vs {opponent}")
        else:
            opponent = home_tri
            tooltip_labels.append(f"en {opponent}")
        labels_out.append(opponent)
    labels_out = labels_out[::-1]
    tooltip_labels = tooltip_labels[::-1]
    dates_out = [r["game_date"] for r in rows][::-1]

    # convert values and handle minutes specially (MM:SS -> decimal minutes)
    def parse_minutes(s):
        if s is None:
            return None
        try:
            if isinstance(s, (int, float)):
                return float(s)
            parts = str(s).split(":")
            if len(parts) == 2:
                mm = int(parts[0])
                ss = int(parts[1])
                return round(mm + ss / 60.0, 2)
            return float(s)
        except Exception:
            return None

    raw_values = [r["value"] for r in rows][::-1]
    if stat == "minutes":
        values_out = [parse_minutes(v) for v in raw_values]
    else:
        vals = []
        for v in raw_values:
            if v is None:
                vals.append(None)
                continue
            try:
                if isinstance(v, (int, float)):
                    vals.append(v)
                else:
                    vals.append(float(v))
            except Exception:
                vals.append(None)
        values_out = vals

    # compute average of numeric values
    nums = [v for v in values_out if isinstance(v, (int, float))]
    avg = round(sum(nums) / len(nums), 2) if nums else 0

    return {
        "labels": labels_out,
        "values": values_out,
        "dates": dates_out,
        "tooltip_labels": tooltip_labels,
        "avg": avg
    }


@app.route("/api/player_minutes_range")
def player_minutes_range_api():
    player = request.args.get("player", "")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT ps.minutes
        FROM player_stats ps
        JOIN games g ON ps.game_id = g.game_id
        WHERE ps.player_name = ? AND g.season NOT LIKE '3%%'
          AND ps.minutes NOT IN ('0:00', '0', '')
        ORDER BY g.game_date DESC
        LIMIT 82
    """, (player,))
    rows = cur.fetchall()
    conn.close()

    mins = []
    for r in rows:
        try:
            val = str(r["minutes"])
            parts = val.split(":")
            mins.append(int(parts[0]) if len(parts) >= 1 else 0)
        except Exception:
            pass

    if not mins:
        return {"min": 0, "max": 48, "avg": 0}

    return {"min": min(mins), "max": max(mins), "avg": round(sum(mins) / len(mins))}


NBA_TRICODES = {
    'ATL','BOS','BKN','CHA','CHI','CLE','DAL','DEN','DET','GSW',
    'HOU','IND','LAC','LAL','MEM','MIA','MIL','MIN','NOP','NYK',
    'OKC','ORL','PHI','PHX','POR','SAC','SAS','TOR','UTA','WAS'
}

TEAM_NAME_TO_TRICODE = {
    "Atlanta Hawks": "ATL", "Boston Celtics": "BOS", "Brooklyn Nets": "BKN",
    "Charlotte Hornets": "CHA", "Chicago Bulls": "CHI", "Cleveland Cavaliers": "CLE",
    "Dallas Mavericks": "DAL", "Denver Nuggets": "DEN", "Detroit Pistons": "DET",
    "Golden State Warriors": "GSW", "Houston Rockets": "HOU", "Indiana Pacers": "IND",
    "Los Angeles Clippers": "LAC", "Los Angeles Lakers": "LAL", "Memphis Grizzlies": "MEM",
    "Miami Heat": "MIA", "Milwaukee Bucks": "MIL", "Minnesota Timberwolves": "MIN",
    "New Orleans Pelicans": "NOP", "New York Knicks": "NYK", "Oklahoma City Thunder": "OKC",
    "Orlando Magic": "ORL", "Philadelphia 76ers": "PHI", "Phoenix Suns": "PHX",
    "Portland Trail Blazers": "POR", "Sacramento Kings": "SAC", "San Antonio Spurs": "SAS",
    "Toronto Raptors": "TOR", "Utah Jazz": "UTA", "Washington Wizards": "WAS",
}

PROPS_STAT_SQL = {
    "points":   "ps.points",
    "rebounds": "ps.rebounds",
    "assists":  "ps.assists",
    "pra":      "(ps.points + ps.rebounds + ps.assists)",
    "pa":       "(ps.points + ps.assists)",
    "pr":       "(ps.points + ps.rebounds)",
    "ra":       "(ps.rebounds + ps.assists)",
    "fg3m":     "ps.fg3m",
    "fg3a":     "ps.fg3a",
    "fga":      "ps.fga",
    "ftm":      "ps.ftm",
    "fta":      "ps.fta",
    "blocks":   "ps.blocks",
    "steals":   "ps.steals",
    "sb":       "(ps.steals + ps.blocks)",
    "turnovers":"ps.turnovers",
    "fouls":    "ps.fouls",
}

ODDS_CACHE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'odds_cache.json')

@app.route("/api/player_search")
def player_search_api():
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify({"players": []})
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT player_name
        FROM player_stats
        WHERE player_name LIKE ? AND team_tricode IN (
            'ATL','BOS','BKN','CHA','CHI','CLE','DAL','DEN','DET','GSW',
            'HOU','IND','LAC','LAL','MEM','MIA','MIL','MIN','NOP','NYK',
            'OKC','ORL','PHI','PHX','POR','SAC','SAS','TOR','UTA','WAS'
        )
        ORDER BY player_name
        LIMIT 8
    """, (f"%{q}%",))
    players = list(dict.fromkeys(r[0] for r in cur.fetchall()))
    conn.close()
    return jsonify({"players": players})


@app.route("/api/team_players")
def team_players_api():
    player = request.args.get("player")

    conn = get_db()
    cur = conn.cursor()

    # Get the player's team — only consider real NBA tricodes (excludes All-Star game)
    cur.execute("""
        SELECT DISTINCT team_tricode
        FROM player_stats
        WHERE player_name = ? AND team_tricode IS NOT NULL
        ORDER BY id DESC
    """, (player,))
    trow = next((r for r in cur.fetchall() if r[0] in NBA_TRICODES), None)
    
    if not trow:
        conn.close()
        return {"players": []}
    
    team_tricode = trow[0]
    
    # Get all unique players from that team (most recent appearances)
    cur.execute("""
        SELECT DISTINCT ps.player_name
        FROM player_stats ps
        WHERE ps.team_tricode = ?
        GROUP BY ps.player_name
        ORDER BY MAX(ps.id) DESC
        LIMIT 15
    """, (team_tricode,))
    
    players = [row[0] for row in cur.fetchall()]
    conn.close()
    
    return {"players": players}


@app.route("/api/props")
def props_api():
    import unicodedata

    stat_filter = request.args.get("stat", "points")
    game_filter = request.args.get("game", "")      # "Away @ Home" or ""
    limit       = min(int(request.args.get("limit", "20")), 50)

    try:
        with open(ODDS_CACHE_PATH) as f:
            cache = json.load(f)
        props_raw = cache.get("props", [])
    except Exception:
        return jsonify({"props": [], "matchups": []})

    # Unique matchups for the frontend game-filter dropdown
    matchups = sorted({
        f"{p['away_team']} @ {p['home_team']}"
        for p in props_raw
        if p.get("away_team") and p.get("home_team")
    })

    if stat_filter not in PROPS_STAT_SQL:
        return jsonify({"props": [], "matchups": matchups})

    # Filter by stat first — reduces 725 → ~100 props
    filtered = [
        p for p in props_raw
        if p.get("stat") == stat_filter and p.get("line") is not None
    ]
    if game_filter:
        filtered = [
            p for p in filtered
            if f"{p.get('away_team','')} @ {p.get('home_team','')}" == game_filter
        ]
    if not filtered:
        return jsonify({"props": [], "matchups": matchups})

    expr = PROPS_STAT_SQL[stat_filter]
    conn = get_db()
    cur  = conn.cursor()

    def _norm(s):
        return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower().strip()

    def find_player(name):
        parts = name.strip().split()
        last  = parts[-1] if parts else name
        cur.execute(
            "SELECT DISTINCT player_name FROM player_stats WHERE player_name LIKE ? LIMIT 30",
            (f"%{last}%",)
        )
        norm_target = _norm(name)
        for (pname,) in cur.fetchall():
            if _norm(pname) == norm_target:
                return pname
        # Fallback: first + last partial
        if len(parts) >= 2:
            cur.execute(
                "SELECT DISTINCT player_name FROM player_stats "
                "WHERE player_name LIKE ? AND player_name LIKE ? LIMIT 1",
                (f"%{parts[0]}%", f"%{last}%")
            )
            row = cur.fetchone()
            if row:
                return row[0]
        return None

    def player_data(db_player, line, home_tc, away_tc):
        """One query, all stats computed in Python."""
        cur.execute(f"""
            SELECT g.season, g.home_tricode, g.away_tricode, ps.team_tricode,
                   CAST({expr} AS REAL) AS val
            FROM player_stats ps
            JOIN games g ON ps.game_id = g.game_id
            WHERE ps.player_name = ? AND g.season NOT LIKE '3%'
              AND ps.minutes NOT IN ('0:00', '0', '')
            ORDER BY g.game_date DESC LIMIT 100
        """, (db_player,))
        rows = [(s, htc, atc, ptc, v) for s, htc, atc, ptc, v in cur.fetchall() if v is not None]

        all_v   = [v for *_, v in rows]
        s2526   = [v for s, _, _, _, v in rows if s == "22025"]
        s2425   = [v for s, _, _, _, v in rows if s == "22024"]
        h2h_v   = [v for _, htc, atc, _, v in rows
                   if home_tc and away_tc and
                      ((htc == home_tc and atc == away_tc) or (htc == away_tc and atc == home_tc))]

        def rate(lst, lim=None):
            sub = lst[:lim] if lim else lst
            if not sub: return None
            return round(sum(1 for v in sub if v >= float(line)) / len(sub) * 100)

        stk = 0
        if all_v:
            d = 1 if all_v[0] >= float(line) else -1
            for v in all_v:
                if (v >= float(line)) == (d == 1): stk += d
                else: break

        return {
            "streak":     stk,
            "pct_season": rate(s2526),
            "pct_h2h":    rate(h2h_v),
            "pct_l5":     rate(all_v, 5),
            "pct_l10":    rate(all_v, 10),
            "pct_l20":    rate(all_v, 20),
            "pct_prev":   rate(s2425),
        }

    result  = []
    seen    = set()

    for prop in filtered:
        api_name = prop["player"]
        line     = prop["line"]
        dedup_key = (api_name, round(float(line) * 2))
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        db_player = find_player(api_name)
        if not db_player:
            continue

        home_tc = TEAM_NAME_TO_TRICODE.get(prop.get("home_team", ""))
        away_tc = TEAM_NAME_TO_TRICODE.get(prop.get("away_team", ""))
        stats   = player_data(db_player, line, home_tc, away_tc)

        result.append({
            "player":     db_player,
            "stat":       stat_filter,
            "line":       line,
            "over_odds":  prop.get("over_odds"),
            "under_odds": prop.get("under_odds"),
            "matchup":    f"{prop.get('away_team','?')} @ {prop.get('home_team','?')}",
            **stats,
        })

    # Sort by best season hit rate so the top picks appear first
    result.sort(key=lambda r: r.get("pct_season") if r.get("pct_season") is not None else -1, reverse=True)
    result = result[:limit]

    conn.close()
    return jsonify({"props": result, "matchups": matchups})


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
