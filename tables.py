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
    Team TEXT,
    Nationality TEXT
);

CREATE TABLE IF NOT EXISTS Seasons (
    season_id SERIAL PRIMARY KEY,
    season_year VARCHAR(10) UNIQUE NOT NULL            
    );
            
CREATE TABLE IF NOT EXISTS playerStats (
    player_id INTEGER,
    season_id INTEGER,
    goals INTEGER,
    Xg INTEGER,
    PRIMARY KEY (player_id, season_id),
    FOREIGN KEY (player_id) REFERENCES Players (player_id),
    FOREIGN KEY (season_id) REFERENCES Seasons (season_id)
);
            
CREATE TABLE scrape_queue (
    player_id INT PRIMARY KEY,
    status VARCHAR(20) DEFAULT 'pending',
    last_attempt TIMESTAMP,
    error_message TEXT
);

""")

conn.commit()
cur.close()
conn.close()
