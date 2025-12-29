import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT")
)

cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS Players (
    player_id SERIAL PRIMARY KEY,
    playerName VARCHAR(100),
    position VARCHAR(20),
    playerLink TEXT,
    team TEXT,
    nationality TEXT
);

CREATE TABLE IF NOT EXISTS Seasons (
    season_id SERIAL PRIMARY KEY,
    season_year VARCHAR(10) UNIQUE NOT NULL            
    );

CREATE TABLE IF NOT EXISTS Teams (
    team TEXT,
    team_xG FLOAT,
    season_id INTEGER,
    PRIMARY KEY (team, season_id),
    FOREIGN KEY (season_id) REFERENCES Seasons (season_id)
);
            
CREATE TABLE IF NOT EXISTS playerStats (
    player_id INTEGER,
    season_id INTEGER,
    goals INTEGER,
    team TEXT,
    xG FLOAT,
    g90 FLOAT,
    PRIMARY KEY (player_id, season_id),
    FOREIGN KEY (player_id) REFERENCES Players (player_id),
    FOREIGN KEY (season_id) REFERENCES Seasons (season_id),
    FOREIGN KEY (team, season_id) REFERENCES Teams(team, season_id)
);
            
CREATE TABLE scrape_queue (
    player_id INT PRIMARY KEY,
    status VARCHAR(20) DEFAULT 'pending',
    last_attempt TIMESTAMP,
    error_message TEXT
);
            
INSERT INTO Seasons (season_year)
VALUES
    ('2024-2025'),
    ('2023-2024'),
    ('2022-2023'),
    ('2021-2022'),
    ('2020-2021');

""")

conn.commit()
cur.close()
conn.close()
