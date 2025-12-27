from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
import psycopg2
from dotenv import load_dotenv
import os
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
#use selenium to bypass dynamic loading
#parse html using beautiful soup 
#convert to pandas df for local use and ML
#format(player link pair)

load_dotenv()
#global variables
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT")
)
cur = conn.cursor()

driver = webdriver.Chrome()

def teamsTable(driver):
    table_element = driver.find_element(By.ID, "switcher_stats_squads_standard")
    leagueHtml = table_element.get_attribute('outerHTML')
    return leagueHtml

def getTeamLinks(leagueHtml):
    soup = BeautifulSoup(leagueHtml, "html.parser")
    #Create a dictionary of TeamName : [Team link, [xg] ] pairs
    team_dict = {}
    rows = soup.find_all("tr")
    for row in rows:
        link = row.find("a")
        if not link:
            continue
        name = link.text.strip()
        teamLink = "https://fbref.com" + link.get('href')
        # Visit team page and collect xG for current + previous 4 seasons
        xg_list = []
        try:
            driver.get(teamLink)
            for i in range(5):
                # wait for the meta block to be present and parse it
                try:
                    meta_el = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "meta"))
                    )
                    meta_html = meta_el.get_attribute('outerHTML')
                    soup_xg = BeautifulSoup(meta_html, "html.parser")
                except Exception:
                    # meta didn't load; try to advance once, otherwise pad and break
                    try:
                        prev_btn = driver.find_element(By.CSS_SELECTOR, "div#meta div.prevnext a")
                        try:
                            prev_btn.click()
                        except Exception:
                            driver.execute_script("arguments[0].click();", prev_btn)
                        time.sleep(0.5)
                        continue
                    except Exception:
                        for _ in range(i, 5):
                            xg_list.append(None)
                        break

                # check header_end presence and whether it indicates a competition we accept
                header_el = soup_xg.find("span", class_="header_end")
                is_allowed_comp = False
                if header_el and header_el.text:
                    header_text = header_el.text.strip()
                    allowed = ["Premier League", "Championship", "League One"]
                    is_allowed_comp = any(a in header_text for a in allowed)

                # if not on an allowed competition, navigate back until we find one or give up
                nav_attempts = 0
                while not is_allowed_comp and nav_attempts < 10:
                    try:
                        prev_btn = driver.find_element(By.CSS_SELECTOR, "div#meta div.prevnext a")
                        try:
                            prev_btn.click()
                        except Exception:
                            driver.execute_script("arguments[0].click();", prev_btn)

                        WebDriverWait(driver, 8).until(
                            lambda d: d.find_element(By.ID, "meta").get_attribute('outerHTML') != meta_html
                        )
                        time.sleep(0.5)
                        meta_el = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.ID, "meta"))
                        )
                        meta_html = meta_el.get_attribute('outerHTML')
                        soup_xg = BeautifulSoup(meta_html, "html.parser")
                        header_el = soup_xg.find("span", class_="header_end")
                        if header_el and header_el.text:
                            header_text = header_el.text.strip()
                            is_allowed_comp = any(a in header_text for a in ["Premier League", "Championship", "League One"])
                        nav_attempts += 1
                    except Exception:
                        break

                # extract xG only if we are on an allowed competition page
                if is_allowed_comp:
                    strong = soup_xg.find('strong', string=lambda s: s and 'xG' in s)
                    if strong and strong.next_sibling:
                        xg_text = strong.next_sibling.strip().replace(",", "")
                        xg_list.append(xg_text if xg_text != '' else None)
                    else:
                        xg_list.append(None)
                else:
                    xg_list.append(None)

                # advance one season for the next outer iteration; if can't, pad remaining and break
                try:
                    prev_btn = driver.find_element(By.CSS_SELECTOR, "div#meta div.prevnext a")
                    try:
                        prev_btn.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", prev_btn)
                    WebDriverWait(driver, 8).until(
                        lambda d: d.find_element(By.ID, "meta").get_attribute('outerHTML') != meta_html
                    )
                    time.sleep(0.5)
                except Exception:
                    for _ in range(i+1, 5):
                        xg_list.append(None)
                    break
        except Exception as e:
            print(f"Failed to load team page for {name}: {e}")
            # if page fails to load entirely, ensure we have five None entries
            xg_list = [None] * 5

        team_dict[name] = [teamLink, xg_list]
    return team_dict

def leagueTable(driver):
    table_element = driver.find_element(By.ID, "div_stats_standard")
    #print(table_element.text)
    html = table_element.get_attribute('outerHTML')
    # print(html)
    '''successfully obtained player standard stats table data with selenium'''
    return html

# player names are found here as well
def getPlayerLinks(html):
    soup = BeautifulSoup(html, "html.parser")
    player_dict = {}
    rows = soup.find_all("tr")
    for row in rows:
        # Get the first <a> tag in this row (player link) using .find()
        link = row.find("a")
        if not link:
            continue
        name = link.text.strip()
        href = "https://fbref.com" + link.get('href')

        # Get the position cell in this row
        pos_cell = row.find('td', {'data-stat': 'position'})
        if not pos_cell:
            continue
        position = pos_cell.text.strip()
        #Get nationality
        nationality_td = row.find("td", {"data-stat": "nationality"})
        nationality = nationality_td.get_text(strip=True)
        #Get Team
        team_td = row.find('td', {'data-stat': 'team'})
        team = team_td.get_text(strip=True)

        # Player name: attributes
        player_dict[name] = [href, position, nationality, team]

    # Filter by allowed positions
    allowed_positions = {'CM', 'AM', 'FW', 'LW', 'RW', 'CF', 'SS', 'CAM', 'ST', 'MF'}
    # Keep player if ANY allowed position is in their position string
    player_dict = {
        name: info
        for name, info in player_dict.items()
        if any(pos in info[1].split(',') or pos in info[1] for pos in allowed_positions)
    }

    # print(player_dict)
    # df = pd.DataFrame.from_dict(player_dict, orient='index', columns=['Link', 'Position'])
    # df.index.name = 'Player'
    # print(df)

    return player_dict

'''
now access player data for each player(xg, xa)
scrape from standard stats table
iterate over the last 5 seasons for each player
'''
'''Process players in batches to prevent selenium web driver from timing out'''
def getPlayerStats(player_dict):
    batch_size = 10
    seasons = ['2024-2025', '2023-2024', '2022-2023', '2021-2022', '2020-2021']
    
    cur.execute("""
        SELECT p.player_id, p.playerName, p.playerLink, p.position, p.Nationality
        FROM Players p
        JOIN scrape_queue sq ON p.player_id = sq.player_id
        WHERE sq.status = 'pending'
        ORDER BY p.player_id
        LIMIT %s    
    """, (batch_size,))

    pending_players = cur.fetchall()

    for player_id, name, link, position, nationality in pending_players:
        try:
            print(f"Processing {name}...")
            driver.get(link)
            
            # Wait for the table to load (up to 10 seconds)
            wait = WebDriverWait(driver, 10)
            table_element = wait.until(
                EC.presence_of_element_located((By.ID, "div_stats_standard_dom_lg"))
            )
            
            html = table_element.get_attribute('outerHTML')
            soup = BeautifulSoup(html, "html.parser")
            
            for season in seasons:
                # returns list of goals, xg
                stats = getGoals(soup, season)

                # Initialize to None
                goals_value = None
                xg_value = None
                
                if stats and stats[0]:
                    try:
                        goals_value = int(stats[0]) 
                    except (ValueError, TypeError):
                        goals_value = None

                if stats and stats[1]:
                    try:
                        xg_value = float(stats[1]) 
                    except (ValueError, TypeError):
                        xg_value = None
                
                cur.execute("SELECT season_id FROM Seasons WHERE season_year = %s", (season,))
                season_result = cur.fetchone()
                
                if season_result is not None:
                    season_id = season_result[0]  # Extract integer from tuple
                    
                    cur.execute("""
                        INSERT INTO playerStats (player_id, season_id, goals, Xg)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (player_id, season_id) 
                        DO UPDATE SET goals = EXCLUDED.goals, Xg = EXCLUDED.Xg
                    """, (player_id, season_id, goals_value, xg_value ))
            
            # Mark as completed
            cur.execute("""
                UPDATE scrape_queue 
                SET status = 'completed', last_attempt = NOW()
                WHERE player_id = %s
            """, (player_id,))
            
            conn.commit()  # Commit after each successful player
            # Add delay between players to avoid rate limiting
            time.sleep(2)

        except Exception as e:
            conn.rollback()  # Rollback failed transaction
            try:
                cur.execute("""
                    UPDATE scrape_queue 
                    SET status = 'failed', last_attempt = NOW(), error_message = %s
                    WHERE player_id = %s
                """, (str(e), player_id))
                conn.commit()
            except Exception as update_error:
                print(f"Failed to update error status: {update_error}")
                conn.rollback()
    
    print(f"Batch completed, processed {len(pending_players)} players")

    cur.execute("SELECT COUNT(*) FROM scrape_queue WHERE status = 'pending'")
    remaining = cur.fetchone()[0]
    print(f"Remaining pending players: {remaining}")
    return remaining == 0
            
    # for player, (link, position, nationality) in player_dict.items():
    #     driver.get(link)
    #     # time.sleep(2)  # Wait 2 seconds between requests (adjust as needed)
    #     try:
    #         table_element = driver.find_element(By.ID, "div_stats_standard_dom_lg")
    #         html = table_element.get_attribute('outerHTML')
    #         soup = BeautifulSoup(html, "html.parser")
    #         for season in seasons:
    #             goals = getGoals(soup, season)
    #             records.append({
    #                 'Player': player,
    #                 'Link': link,
    #                 'Position': position,
    #                 'Season': season,
    #                 'Goals': goals,
    #                 'Nationality' : nationality
    #             })
    #     except Exception as e:
    #         print(f"Error processing {player}: {e}")
    #         for season in seasons:
    #             records.append({
    #                 'Player': player,
    #                 'Link': link,
    #                 'Position': position,
    #                 'Season': season,
    #                 'Goals': None,
    #                 'Nationality' : None
    #             })

    # Convert to DataFrame
    # df = pd.DataFrame(records)
    # print(df)
    # # df.to_excel("/Users/riyadrajan/Desktop/Player-Link-Position-Goals-df.xlsx", index=False)
    # df.to_excel("/Users/riyadrajan/Desktop/Player-Link-df.xlsx", index=False)
    # print("Printed to Player-Link-df")
    # return df

    
def getGoals(soup, season):
    goals = None
    xg = None
    
    # Find the row for a specific season 
    season_row = soup.find('tr', {'id': 'stats'}, string=lambda s: s and season in s)
    if not season_row:
        # fallback: search by year in the first <th>
        for row in soup.find_all('tr', {'id': 'stats'}):
            th = row.find('th', {'data-stat': 'year_id'})
            if th and th.text.strip() == season:
                season_row = row
                break
    
    if season_row:
        goals_cell = season_row.find('td', {'data-stat': 'goals'})
        if goals_cell:
            goals = goals_cell.text.strip()
            
        xg_cell = season_row.find('td', {'data-stat': 'xg'})
        if xg_cell:  
            xg = xg_cell.text.strip()

    return [goals, xg]

def main():
    base_url = "https://fbref.com/en/comps/9/stats/Premier-League-Stats"
    driver.get(base_url)
    html = leagueTable(driver)
    #remove below
    leagueHTML = teamsTable(driver)
    team_dict = getTeamLinks(leagueHTML)
    # print(team_dict)
    player_dict = getPlayerLinks(html)

    # for name, (href, position, nationality, team) in player_dict.items():
    #     cur.execute(
    #         "INSERT INTO Players (playerName, playerLink, position, Nationality, Team) VALUES (%s, %s, %s, %s, %s)",
    #         (name, href, position, nationality, team)
    #     )

    finished = False
    while (finished is not True) :
        finished = getPlayerStats(player_dict)
        time.sleep(5)

    driver.quit()
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()

'''
Note that scrape queue was polulated once with 
INSERT INTO scrape_queue (player_id)
SELECT player_id FROM players;
if the player status is still pending, they need to be processed in the batch

To be implemented:  get teams/squad for each season for a player
                    assign a weight of <1 for players outside the prem in previous seasons 
                    in getGoals, also get expected goals
'''
