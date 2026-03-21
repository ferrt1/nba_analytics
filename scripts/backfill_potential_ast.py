# scripts/backfill_potential_ast.py
# Downloads REAL potential assists from leaguedashptstats endpoint.
# Much faster than per-game: 1 request per game-date, not per game.

import sqlite3
import time
import sys
import io
import random
import unicodedata

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from nba_api.stats.endpoints import leaguedashptstats

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

conn = sqlite3.connect('db/nba.db')
cur = conn.cursor()

# Build name lookup: ascii name -> DB name (with accents)
cur.execute('SELECT DISTINCT player_name FROM player_stats')
name_map = {}
for (db_name,) in cur.fetchall():
    name_map[strip_accents(db_name)] = db_name

# Ensure column exists
try:
    cur.execute('ALTER TABLE player_stats ADD COLUMN potential_ast INTEGER')
except:
    pass

# Reset bad data (passes were stored as potential_ast incorrectly)
cur.execute('UPDATE player_stats SET potential_ast = NULL WHERE potential_ast IS NOT NULL')
conn.commit()
reset = cur.rowcount
if reset:
    print(f'Reset {reset} rows with bad potential_ast data', flush=True)

# Get distinct game dates that need potential_ast
cur.execute('''
    SELECT DISTINCT g.game_date FROM player_stats ps
    JOIN games g ON ps.game_id = g.game_id
    WHERE ps.potential_ast IS NULL AND ps.game_id LIKE '002%'
    ORDER BY g.game_date DESC
''')
dates = [r[0] for r in cur.fetchall()]
print(f'Dates to fetch: {len(dates)}', flush=True)

fixed = 0
for i, game_date in enumerate(dates):
    if i % 10 == 0:
        print(f'  [{i}/{len(dates)}] fixed={fixed}', flush=True)
        conn.commit()

    # Convert YYYY-MM-DD to MM/DD/YYYY for NBA API
    parts = game_date.split('-')
    nba_date = f'{parts[1]}/{parts[2]}/{parts[0]}'

    print(f'  Descargando {game_date} ({i+1}/{len(dates)})...', end='\r', flush=True)

    for attempt in range(1, 4):
        try:
            stats = leaguedashptstats.LeagueDashPtStats(
                pt_measure_type='Passing',
                player_or_team='Player',
                per_mode_simple='Totals',
                season='2025-26',
                season_type_all_star='Regular Season',
                date_from_nullable=nba_date,
                date_to_nullable=nba_date,
                timeout=60,
            )
            df = stats.get_data_frames()[0]

            for _, row in df.iterrows():
                api_name = row['PLAYER_NAME']
                db_name = name_map.get(api_name, api_name)
                pot_ast = int(row['POTENTIAL_AST'])

                cur.execute(
                    '''UPDATE player_stats SET potential_ast=?
                       WHERE player_name=? AND game_id IN (
                           SELECT g2.game_id FROM games g2 WHERE g2.game_date=?
                       ) AND potential_ast IS NULL''',
                    (pot_ast, db_name, game_date))
                fixed += cur.rowcount

            break
        except Exception as e:
            if attempt < 3:
                print(f'  Retry {attempt} for {game_date}: {e}', flush=True)
                time.sleep(10 * attempt)
            else:
                print(f'  Error {game_date}: {e}', flush=True)

    # Also fetch 2024-25 season if needed
    if game_date < '2025-10-01':
        for attempt in range(1, 4):
            try:
                stats = leaguedashptstats.LeagueDashPtStats(
                    pt_measure_type='Passing',
                    player_or_team='Player',
                    per_mode_simple='Totals',
                    season='2024-25',
                    season_type_all_star='Regular Season',
                    date_from_nullable=nba_date,
                    date_to_nullable=nba_date,
                    timeout=60,
                )
                df = stats.get_data_frames()[0]

                for _, row in df.iterrows():
                    player_name = row['PLAYER_NAME']
                    pot_ast = int(row['POTENTIAL_AST'])
                    cur.execute(
                        '''UPDATE player_stats SET potential_ast=?
                           WHERE player_name=? AND game_id IN (
                               SELECT g2.game_id FROM games g2 WHERE g2.game_date=?
                           ) AND potential_ast IS NULL''',
                        (pot_ast, player_name, game_date))
                    fixed += cur.rowcount

                break
            except Exception as e:
                if attempt < 3:
                    time.sleep(10 * attempt)
                else:
                    print(f'  Error 24-25 {game_date}: {e}', flush=True)

    time.sleep(random.uniform(3, 7))

conn.commit()
print(f'\nDone! Fixed: {fixed} rows', flush=True)
conn.close()
