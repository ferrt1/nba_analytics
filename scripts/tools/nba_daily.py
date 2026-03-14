from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
import sqlite3
import json
import time
import math

from nba_api.stats.endpoints import scoreboardv3, boxscoretraditionalv3


def _convert_et_to_argentina(et_time_str: str, game_date: date) -> str:
    """Convert an ET time string (e.g., '7:00 pm ET' or '7:00 pm') to Argentina time.

    Uses system timezones via ZoneInfo so DST is handled correctly for the given game date.
    If parsing fails or no time is present, returns the original string (or empty string).
    """
    if not et_time_str:
        return ""

    import re

    # Try to extract time and am/pm
    m = re.search(r"(\d{1,2}:\d{2})\s*([ap]m)", et_time_str, flags=re.IGNORECASE)
    if not m:
        return et_time_str

    time_part = m.group(1)
    ampm = m.group(2).upper().replace('.', '')

    try:
        # Build a naive datetime with the provided game date
        dt_naive = datetime.strptime(f"{time_part} {ampm}", "%I:%M %p")
        dt = dt_naive.replace(year=game_date.year, month=game_date.month, day=game_date.day)

        # Assume ET == America/New_York
        dt_et = dt.replace(tzinfo=ZoneInfo("America/New_York"))
        dt_arg = dt_et.astimezone(ZoneInfo("America/Argentina/Buenos_Aires"))
        return dt_arg.strftime("%I:%M %p ART")
    except Exception:
        return et_time_str

DATA_DIR = Path("data/raw")
BOX_DIR = DATA_DIR / "boxscores"
DB_PATH = Path("db/nba.db")

DATA_DIR.mkdir(parents=True, exist_ok=True)
BOX_DIR.mkdir(parents=True, exist_ok=True)


def _clean_nan(obj):
    if isinstance(obj, float) and math.isnan(obj):
        return None
    elif isinstance(obj, dict):
        return {k: _clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_clean_nan(i) for i in obj]
    else:
        return obj


def get_games_on_date(d: date) -> list[dict]:
    game_date = d.strftime("%Y-%m-%d")
    sb = scoreboardv3.ScoreboardV3(game_date=game_date)
    data = sb.get_dict()
    games_list = data.get("scoreboard", {}).get("games", [])

    out = []
    for g in games_list:
        # Try common sources for the game time. scoreboard may put human-friendly string in gameStatusText
        raw_time = (g.get("gameStatusText") or g.get("gameTimeLocal") or g.get("gameEt") or "")
        arg_time = _convert_et_to_argentina(raw_time, d)

        out.append({
            "game_id": g.get("gameId"),
            "home_team": g.get("homeTeam", {}).get("teamName"),
            "away_team": g.get("awayTeam", {}).get("teamName"),
            "home_tricode": g.get("homeTeam", {}).get("teamTricode"),
            "away_tricode": g.get("awayTeam", {}).get("teamTricode"),
            "status": g.get("gameStatusText"),
            "start_time": raw_time,
            "start_time_arg": arg_time,
            "game_date": game_date,
            "season": g.get("season"),
        })

    return out


def _create_tables_if_missing(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS games (
        game_id TEXT PRIMARY KEY,
        season TEXT,
        game_date TEXT,
        matchup TEXT,
        home_team TEXT,
        away_team TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS player_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id TEXT NOT NULL,
        player_id INTEGER NOT NULL,
        player_name TEXT NOT NULL,

        minutes TEXT,

        points INTEGER,
        rebounds INTEGER,
        assists INTEGER,
        steals INTEGER,
        blocks INTEGER,

        fgm INTEGER,
        fga INTEGER,
        fg3m INTEGER,
        fg3a INTEGER,
        ftm INTEGER,
        fta INTEGER,

        turnovers INTEGER,
        fouls INTEGER
    )
    """)

    conn.commit()


def _save_boxscore_file(game_id: str, players: list[dict]):
    file_path = BOX_DIR / f"boxscore_{game_id}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(players, f, indent=2, ensure_ascii=False)


def _fetch_boxscore_players(game_id: str, retries: int = 3) -> list[dict]:
    for attempt in range(1, retries + 1):
        try:
            box = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id, timeout=60)
            df = box.get_data_frames()[0]
            data = df.to_dict(orient="records")
            return _clean_nan(data)
        except Exception as e:
            time.sleep(5 * attempt)
    return []


def _players_exist(conn: sqlite3.Connection, game_id: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(1) FROM player_stats WHERE game_id = ?", (game_id,))
    row = cur.fetchone()
    return (row[0] if row else 0) > 0


def update_for_date(d: date, reset_db: bool = False):
    """Descarga partidos de la fecha `d`, guarda boxscores e inserta en la DB.

    Por defecto solo inserta si no hay estadísticas para ese `game_id`.
    """
    games = get_games_on_date(d)

    # Conectar DB
    if reset_db and DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    _create_tables_if_missing(conn)
    cur = conn.cursor()

    insert_players_sql = """
    INSERT INTO player_stats (
        game_id,
        player_id,
        player_name,
        minutes,
        team_id,
        team_tricode,
        points,
        rebounds,
        assists,
        steals,
        blocks,
        fgm,
        fga,
        fg3m,
        fg3a,
        ftm,
        fta,
        turnovers,
        fouls
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    for g in games:
        gid = g.get("game_id")
        if not gid:
            continue

        matchup = f"{g.get('home_team')} vs {g.get('away_team')}"

        # Insert game row if not exists
        cur.execute(
            "INSERT OR IGNORE INTO games (game_id, season, game_date, matchup, home_team, away_team, home_tricode, away_tricode) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                gid,
                g.get("season"),
                g.get("game_date"),
                matchup,
                g.get("home_team"),
                g.get("away_team"),
                g.get("home_tricode"),
                g.get("away_tricode"),
            ),
        )

        # Si ya tenemos players para este game_id, saltamos
        if _players_exist(conn, gid):
            continue

        # Buscar boxscore y guardar
        players = _fetch_boxscore_players(gid)

        if players:
            _save_boxscore_file(gid, players)

            for p in players:
                def _v(key1, key2):
                    """Pick first non-None value (0 is valid)."""
                    v = p.get(key1)
                    return v if v is not None else p.get(key2)

                cur.execute(
                    insert_players_sql,
                    (
                        gid,
                        _v("personId", "PLAYER_ID"),
                        f"{p.get('firstName', '')} {p.get('familyName', '')}".strip() if p.get('firstName') or p.get('familyName') else p.get("PLAYER_NAME"),
                        p.get("minutes"),
                        _v("teamId", "team_id"),
                        _v("teamTricode", "team_tricode"),
                        p.get("points"),
                        _v("reboundsTotal", "REB"),
                        p.get("assists"),
                        p.get("steals"),
                        p.get("blocks"),
                        _v("fieldGoalsMade", "FGM"),
                        _v("fieldGoalsAttempted", "FGA"),
                        _v("threePointersMade", "FG3M"),
                        _v("threePointersAttempted", "FG3A"),
                        _v("freeThrowsMade", "FTM"),
                        _v("freeThrowsAttempted", "FTA"),
                        p.get("turnovers"),
                        _v("foulsPersonal", "PF"),
                    ),
                )

            conn.commit()

        # Respetar límites de rate
        time.sleep(1)

    conn.close()


def run_startup_update(reset_db: bool = False):
    """Descarga partidos de ayer y HOY, y guarda boxscores e inserta en DB.

    Esto asegura que siempre haya datos del día anterior (para resumen),
    y partidos de hoy (para H2H contra el rival del día).
    """
    yesterday = date.today() - timedelta(days=1)
    today = date.today()
    
    # Download yesterday and today
    for d in [yesterday, today]:
        update_for_date(d, reset_db=False)


def get_today_games():
    return get_games_on_date(date.today())
