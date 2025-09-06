from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
#use selenium to bypass dynamic loading
#parse html using beautiful soup 
#convert to pandas df for local use and ML
#format(player link pair)

#global variables
driver = webdriver.Chrome()


def leagueTable(driver):
    table_element = driver.find_element(By.ID, "div_stats_standard")
    #print(table_element.text)
    html = table_element.get_attribute('outerHTML')
    # print(html)
    '''successfully obtained player standard stats table data with selenium'''
    return html

def getTeamLinks(html):
    '''
    parse html using beautiful soup
    print(soup)
    player links stored in 'a' tag in table row 
    test by storing them in a list
    find_all() method does this
    Objective - create dictionary of value: player link, key: player name pair
    '''
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a") #now have a list of player links
    player_dict = {} 
    # uncomment if needed
    for link in links:
        href = "https://fbref.com" + link.get('href') 
        name = link.text.strip()
        # Only add if href looks like a player link
        if href and name and '/en/players/' in href:
            player_dict[name] = href
    
    # similarly, find player positions
    positions = {'CM', 'AM', 'FW', 'LW', 'RW', 'CF', 'SS', 'CAM', 'ST' }
    rows = soup.find_all("tr")
    #want to search for (data-stat = "position")
    for row in rows:
        pos_cell = row.find('td', {'data-stat': 'position'})
        if pos_cell:
            position = pos_cell.text.strip()
            print(position)
	    



    # player_dict.pop('Matches')
    # print(player_dict)
    '''
    Since there are too many players to scrape, pop all players who aren't attackers or midfielders
    '''
    return player_dict
    # #convert to dataframe for easier viewing    
    # df = pd.DataFrame.from_dict(player_dict, orient='index', columns=['Link'])
    # df.index.name = 'Player'  # Rename the index to 'Player'
    # df = df.reset_index()     # Move index to a column
    # # print(df)
    # # df = df.drop('Matches', errors='ignore')  # Remove 'Matches'


    # # df.to_excel("/Users/riyadrajan/Desktop/Player-Link-df.xlsx" )



'''
now access player data for each player(xg, xa)
scrape from standard stats table
iterate over the last 5 seasons for each player
'''
def getPlayerStats(player_dict):
    seasons = ['2024-2025', '2023-2024', '2022-2023', '2021-2022', '2020-2021']
    # Outer dict: season -> {player: goals}
    season_player_goals = {season: {} for season in seasons}

    for player, url in player_dict.items():
        driver.get(url)
        try:
            table_element = driver.find_element(By.ID, "div_stats_standard_dom_lg")
            html = table_element.get_attribute('outerHTML')
            soup = BeautifulSoup(html, "html.parser")
            for season in seasons:
                goals = getGoals(soup, season)
                season_player_goals[season][player] = goals
        except Exception as e:
            print(f"Error processing {player}: {e}")
            for season in seasons:
                season_player_goals[season][player] = None

    # Convert to DataFrame: index=season, columns=player names, values=goals
    df = pd.DataFrame.from_dict(season_player_goals, orient='index')
    df.to_excel("/Users/riyadrajan/Desktop/Player-Link-df.xlsx" )
    return df

    # for player in player_dict:
    #     driver.get(player_dict[player])
    #     table_element = driver.find_element(By.ID, "div_stats_standard_dom_lg")
    #     #obtain goals and store it in another dictionary, key: Player Name, value: goals
    #     html = table_element.get_attribute('outerHTML')
    #     soup = BeautifulSoup(html, "html.parser")
    #     getGoals(soup, '2024-2025')
    #     getGoals(soup, '2023-2024')
    #     getGoals(soup, '2022-2023')
    #     getGoals(soup, '2021-2022')
    #     getGoals(soup, '2020-2021')

    # player = 'Bruno Fernandes'
    # driver.get(player_dict[player])
    # table_element = driver.find_element(By.ID, "div_stats_standard_dom_lg")
    # #obtain goals and store it in another dictionary, key: Player Name, value: goals
    # html = table_element.get_attribute('outerHTML')
    # soup = BeautifulSoup(html, "html.parser")
    # # print(soup.prettify())
    # individual = {}
    # seasons = ['2024-2025', '2023-2024', '2022-2023', '2021-2022', '2020-2021']
    # for season in seasons:
    #     print(f"Goals ({season}):", getGoals(soup, season))
    '''
    Confirming helper function works, and individual test for Bruno Fernandes aligns with website stats
    Now create df for all players, key: Name, Elements: [Season: Goals]
    '''

    
def getGoals(soup, season):
    # gets goals for a specific season
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
            # print(f"Goals ({season}):", goals)
    return goals

def main():
    base_url = "https://fbref.com/en/comps/9/stats/Premier-League-Stats"
    driver.get(base_url)
    html = leagueTable(driver)
    player_dict = getTeamLinks(html)
    # getPlayerStats(player_dict)
    driver.quit()


if __name__ == "__main__":
    main()
