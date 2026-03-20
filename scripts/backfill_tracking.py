# scripts/backfill_tracking.py
# Run locally: python scripts/backfill_tracking.py
# Downloads tracking data (rebound chances, potential assists, usage%)
# for the last 35 days of games.

import sqlite3
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from nba_api.stats.endpoints import boxscoreplayertrackv3, boxscoreusagev3

conn = sqlite3.connect('db/nba.db')
cur = conn.cursor()

# Ensure columns exist
for col in ('reb_chances_off INTEGER', 'reb_chances_def INTEGER',
            'reb_chances INTEGER', 'secondary_ast INTEGER',
            'potential_ast INTEGER', 'usage_pct REAL'):
    try:
        cur.execute(f'ALTER TABLE player_stats ADD COLUMN {col}')
    except:
        pass

# Get recent games missing tracking
cur.execute('''
    SELECT DISTINCT ps.game_id FROM player_stats ps
    JOIN games g ON ps.game_id = g.game_id
    WHERE ps.reb_chances IS NULL AND ps.game_id LIKE '002%'
    AND g.game_date >= date('now', '-35 days')
    ORDER BY g.game_date DESC
''')
gids = [r[0] for r in cur.fetchall()]
print(f'Games to fetch: {len(gids)}')

fixed = 0
for i, gid in enumerate(gids):
    if i % 20 == 0:
        print(f'  [{i}/{len(gids)}] fixed={fixed}', flush=True)
        conn.commit()

    print(f'  Descargando partido {i+1}/{len(gids)} ({gid})...', end='\r', flush=True)

    # Tracking
    try:
        track = boxscoreplayertrackv3.BoxScorePlayerTrackV3(game_id=gid, timeout=60)
        data = track.get_dict()
        bp = data.get('boxScorePlayerTrack', {})
        for side in ('homeTeam', 'awayTeam'):
            for p in bp.get(side, {}).get('players', []):
                name = f"{p.get('firstName', '')} {p.get('familyName', '')}".strip()
                s = p.get('statistics', {})
                cur.execute(
                    '''UPDATE player_stats
                       SET reb_chances_off=?, reb_chances_def=?, reb_chances=?,
                           secondary_ast=?, potential_ast=?
                       WHERE game_id=? AND player_name=? AND reb_chances IS NULL''',
                    (s.get('reboundChancesOffensive'),
                     s.get('reboundChancesDefensive'),
                     s.get('reboundChancesTotal'),
                     s.get('secondaryAssists'),
                     s.get('passes'),
                     gid, name))
                fixed += cur.rowcount
    except Exception as e:
        print(f'  Track error {gid}: {e}')

    # Usage
    try:
        usage = boxscoreusagev3.BoxScoreUsageV3(game_id=gid, timeout=60)
        data = usage.get_dict()
        bu = data.get('boxScoreUsage', {})
        for side in ('homeTeam', 'awayTeam'):
            for p in bu.get(side, {}).get('players', []):
                name = f"{p.get('firstName', '')} {p.get('familyName', '')}".strip()
                s = p.get('statistics', {})
                usg = s.get('usagePercentage')
                if usg is not None:
                    usg = round(usg * 100, 1)
                cur.execute(
                    '''UPDATE player_stats SET usage_pct=?
                       WHERE game_id=? AND player_name=? AND usage_pct IS NULL''',
                    (usg, gid, name))
    except Exception as e:
        print(f'  Usage error {gid}: {e}')

    time.sleep(1)

conn.commit()
print(f'Done! Fixed: {fixed} rows')
conn.close()
