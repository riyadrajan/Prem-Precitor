# ML Project - Premier League Golden Boot Predictor 
## Implemented so far
- Data scraping of all Premier League attackers/midfielders (Batch Processing)
  - Seasons 20/21 to 24/25
- Used Postgresql to store player data

To view player stats over seasons, run:
```sql
SELECT
    p.playerName,
    p.nationality,
    p.position,
    p.team,
	s.season_year,
    ps.goals
FROM players p
JOIN playerstats ps
    ON p.player_id = ps.player_id
JOIN seasons s
    ON ps.season_id = s.season_id;
```
