from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
#use selenium to bypass dynamic loading
#parse html using beautiful soup 
#convert to pandas df for local use and ML
#format(player link pair)


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
    for link in links:
        href = "fbref.com" + link.get('href') 
        name = link.text.strip()
        # Only add if href looks like a player link
        if href and name and '/en/players/' in href:
            player_dict[name] = href

    #convert to dataframe    
    df = pd.DataFrame.from_dict(player_dict, orient='index', columns=['Link'])
    df.index.name = 'Player'  # Rename the index to 'Player'
    df = df.reset_index()     # Move index to a column
    df = df.drop('Matches', errors='ignore')  # Remove 'Matches'
    print(df)
    # hrefs = [link.get('href') for link in links if link.get('href')]
    # player_names = [link.text.strip() for link in links]
    # print(player_names)
    df.to_excel("/Users/riyadrajan/Desktop/Player-Link-df.xlsx" )

    # for link in links:
    #     print(link)

    # #clean up links
    # for tag in tags:
    #     print(tags)


def main():
    driver = webdriver.Chrome()
    base_url = "https://fbref.com/en/comps/9/stats/Premier-League-Stats"
    driver.get(base_url)
    html = leagueTable(driver)
    getTeamLinks(html)
    driver.quit()


if __name__ == "__main__":
    main()
