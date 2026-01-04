import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT")
)
cur = conn.cursor()

query = """
SELECT
    p.player_id,
    p.playerName,
    p.nationality,
    p.position,
    p.team,
    s.season_year,
    ps.goals,
    ps.xG,
    ps.g90,
    t.team_xG
FROM players p
JOIN playerstats ps
    ON p.player_id = ps.player_id
JOIN seasons s
    ON ps.season_id = s.season_id
JOIN teams t
    ON t.season_id = ps.season_id
   AND t.team = ps.team;    
"""

df = pd.read_sql(query, conn)
'''clean dataframe, fill in NaN values so we could use the ML model
set missing goals to 0
set missing xG with median
set missing team_xG with median
'''
df["goals"] = df["goals"].fillna(0)
df["xg"] = df.groupby("position")["xg"].transform(
    lambda x: x.fillna(x.median())
)
df["g90"] = df.groupby("position")["g90"].transform(
    lambda x: x.fillna(x.median())
)
df["team_xg"] = df.groupby("team")["team_xg"].transform(
    lambda x: x.fillna(x.median())
)

bruno = df[df["player_id"] == 73]
print(bruno)
conn.close()
