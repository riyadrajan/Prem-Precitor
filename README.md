# ML Project - Premier League Golden Boot Predictor 
## Implemented so far
- Data scraping of all Premier League attackers/midfielders (Batch Processing)
  - Seasons 20/21 to 24/25
- Used Postgresql to store player data
- Cleaned queried data in a pandas dataframe (this will be used for the ML)

Query to view player stats over seasons:
```sql
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
```
Sample DataFrame row:
```bash
     player_id       playername nationality position            team season_year  goals    xg   g90  team_xg
361         73  Bruno Fernandes       ptPOR       MF  Manchester Utd   2024-2025    8.0   9.9  0.24     52.6
362         73  Bruno Fernandes       ptPOR       MF  Manchester Utd   2023-2024   10.0  10.0  0.29     56.5
363         73  Bruno Fernandes       ptPOR       MF  Manchester Utd   2022-2023    8.0   9.3  0.22     67.7
364         73  Bruno Fernandes       ptPOR       MF  Manchester Utd   2021-2022   10.0   9.7  0.29     55.8
365         73  Bruno Fernandes       ptPOR       MF  Manchester Utd   2020-2021   18.0  16.1  0.52     60.1
```
