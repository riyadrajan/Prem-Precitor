import requests
import pandas as pd

# Call the bootstrap endpoint
url = "https://fantasy.premierleague.com/api/bootstrap-static/"
data = requests.get(url).json()

# "elements" contains all players
players = data['elements']

# Convert to DataFrame for easier handling, with key columns
df = pd.DataFrame(players)
df = df[['id', 'web_name', 'team', 'minutes', 'goals_scored', 'assists', 'form']]


#Filter out a single player by web name
#Example Bruno ID = 449
#print(df[df['web_name'].str.contains("Fern", case=False)].iloc[0]['id'])
bruno = df[df['id'] == 449]
print(bruno)

