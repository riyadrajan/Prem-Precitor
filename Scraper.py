from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
#use selenium to bypass dynamic loading
#parse html using beautiful soup 
#convert to pandas df for local use and ML
#format(player link pair)


def leagueTable(driver):
    table_element = driver.find_element(By.ID, "div_stats_standard")
    #print(table_element.text)
    html = table_element.get_attribute('outerHTML')
    print(html)
    '''successfully obtained player standard stats table data with selenium'''
    return html

def getTeamLinks(html):
    #parse html using beautiful soup
    soup = BeautifulSoup(html, "html.parser")
    # print(soup)
    '''
    team links stored in 'a' tag in table row
    test by storing them in a list
    '''


def main():
    driver = webdriver.Chrome()
    base_url = "https://fbref.com/en/comps/9/stats/Premier-League-Stats"
    driver.get(base_url)
    html = leagueTable(driver)
    getTeamLinks(html)
    driver.quit()


if __name__ == "__main__":
    main()
