from flask import Flask, render_template, request
import sqlite3
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.tools.nba_daily import get_today_games

app = Flask(__name__)
DB_PATH = "db/nba.db"



def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    return render_template(
        "index.html",
        today_games=get_today_games()
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
        return render_template(
            "index.html",
            error="Jugador no encontrado",
            today_games=get_today_games()
        )
    # determine player's current team (from latest player_stats) and map to full team name via games
    cur.execute("""
        SELECT team_tricode
        FROM player_stats
        WHERE player_name = ? AND team_tricode IS NOT NULL
        ORDER BY id DESC
        LIMIT 1
    """, (row["player_name"],))
    trow = cur.fetchone()
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

    return render_template(
        "index.html",
        player=row["player_name"],
        player_team=player_team,
        today_games=get_today_games()
    )


@app.route("/api/player_stats")
def player_stats_api():
    player = request.args.get("player")
    stat = request.args.get("stat", "points")
    limit = request.args.get("limit", "10")

    conn = get_db()
    cur = conn.cursor()

    stat_sql = {
        "points": "ps.points",
        "rebounds": "ps.rebounds",
        "assists": "ps.assists",
        "pra": "(ps.points + ps.rebounds + ps.assists)",
        "minutes": "ps.minutes",
        "steals": "ps.steals",
        "blocks": "ps.blocks",
        "fgm": "ps.fgm",
        "fga": "ps.fga",
        "fg3m": "ps.fg3m",
        "fg3a": "ps.fg3a",
        "turnovers": "ps.turnovers",
        "fouls": "ps.fouls"
    }[stat]

    # H2H special: determine opponent using today's schedule when possible
    if limit == "h2h":
        opponent = None
        player_team = None

        # try to get player's current team tricode from most recent stats
        cur.execute("""
            SELECT team_tricode, game_id
            FROM player_stats
            WHERE player_name = ? AND team_tricode IS NOT NULL
            ORDER BY id DESC
            LIMIT 1
        """, (player,))
        row = cur.fetchone()
        if row:
            player_team = row[0]

        # check today's games (live from API) for opponent
        try:
            today_games = get_today_games()
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
                    g.home_team || ' vs ' || g.away_team AS matchup,
                    {stat_sql} AS value
                FROM player_stats ps
                JOIN games g ON ps.game_id = g.game_id
                WHERE ps.player_name = ? AND (
                    (g.home_tricode = ? AND g.away_tricode = ?) OR
                    (g.away_tricode = ? AND g.home_tricode = ?)
                )
                ORDER BY g.game_date DESC
                LIMIT ?
            """, (player, player_team, opponent, player_team, opponent, h2h_limit))
            rows = cur.fetchall()
        else:
            # fallback: return last 10 games normally
            cur.execute(f"""
                SELECT
                    g.game_date,
                    g.home_team || ' vs ' || g.away_team AS matchup,
                    {stat_sql} AS value
                FROM player_stats ps
                JOIN games g ON ps.game_id = g.game_id
                WHERE ps.player_name = ?
                ORDER BY g.game_date DESC
                LIMIT 10
            """, (player,))
            rows = cur.fetchall()
    else:
        cur.execute(f"""
            SELECT
                g.game_date,
                g.home_team || ' vs ' || g.away_team AS matchup,
                {stat_sql} AS value
            FROM player_stats ps
            JOIN games g ON ps.game_id = g.game_id
            WHERE ps.player_name = ?
            ORDER BY g.game_date DESC
            LIMIT ?
        """, (player, int(limit)))

        rows = cur.fetchall()
    conn.close()

    labels_out = [r["matchup"] for r in rows][::-1]
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
        "avg": avg
    }


@app.route("/api/team_players")
def team_players_api():
    player = request.args.get("player")
    
    conn = get_db()
    cur = conn.cursor()
    
    # Get the player's team
    cur.execute("""
        SELECT DISTINCT team_tricode
        FROM player_stats
        WHERE player_name = ? AND team_tricode IS NOT NULL
        ORDER BY id DESC
        LIMIT 1
    """, (player,))
    trow = cur.fetchone()
    
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


if __name__ == "__main__":
    app.run(debug=True)
