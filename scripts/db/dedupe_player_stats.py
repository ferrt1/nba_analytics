import sqlite3
from pathlib import Path

DB = Path('db/nba.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()

# Delete duplicate rows keeping the smallest id
cur.execute('''
    DELETE FROM player_stats
    WHERE id NOT IN (
        SELECT MIN(id) FROM player_stats GROUP BY game_id, player_id
    )
''')

conn.commit()
# Create unique index if not exists
try:
    cur.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_player_game_unique ON player_stats(game_id, player_id)')
    conn.commit()
except Exception as e:
    print('Index creation error:', e)

print('Deduplication complete')
conn.close()
