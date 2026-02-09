import sqlite3

conn = sqlite3.connect("db/nba.db")
cur = conn.cursor()

query = """
SELECT
    g.game_date,
    ps.minutes,
    ps.points,
    ps.rebounds,
    ps.assists
FROM player_stats ps
JOIN games g ON ps.game_id = g.game_id
WHERE ps.player_name = ?
ORDER BY g.game_date DESC
LIMIT 5;
"""

player = "Lauri Markkanen"

cur.execute(query, (player,))
rows = cur.fetchall()

print(f"Últimos 5 partidos de {player}:")
for r in rows:
    print(r)

conn.close()
