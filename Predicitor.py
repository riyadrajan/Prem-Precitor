import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv
from sklearn import linear_model
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import PoissonRegressor

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
    s.season_id,
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

# Create lagged dataset: Season N features → Season N+1 goals
df_lagged = df.copy()
df_lagged = df_lagged.sort_values(['player_id', 'season_year'])

# For each player, shift goals up by 1 season (get next season's goals)
df_lagged['next_season_goals'] = df_lagged.groupby('player_id')['goals'].shift(-1)

# Remove rows where we don't have next season data
df_lagged = df_lagged.dropna(subset=['next_season_goals'])
df_lagged['next_season_goals'] = df_lagged['next_season_goals'].astype(int)

# bruno = df[df["player_id"] == 73]
# print(bruno)
# print(df.dtypes)

# ohe = OneHotEncoder(
#     handle_unknown="ignore",
#     sparse_output=False 
# )

# encoded = ohe.fit_transform(df[["team", "position"]])

# encoded_df = pd.DataFrame(
#     encoded,
#     columns=ohe.get_feature_names_out(["team", "position"])
# )
# bruno = encoded_df.iloc[363]
# print(bruno)
# rice = df[df["playername"] == "Declan Rice"]
# print(rice)

'''prepare dataframe for ML Poisson Regression
Solve mixed data types in the df; we want the ML model to learn not base off of the stats alone, but also factors like team success'''

num_features = ["xg", "g90", "team_xg"]
cat_features = ["team", "position"] # to be one hot encoded

preprocessor = ColumnTransformer(
    transformers=[
        ("num", "passthrough", num_features),
        ("cat", OneHotEncoder(
            handle_unknown="ignore",
            sparse_output=False
        ), cat_features)
    ]
)

pipe = Pipeline(steps=[
    ("preprocess", preprocessor),
    ("model", PoissonRegressor(alpha=0.001, max_iter=1000))
])

# Train on 2020-2023 features → 2021-2024 goals (lagged prediction)
train_df_lagged = df_lagged[df_lagged["season_year"].isin([
    "2020-2021",
    "2021-2022",
    "2022-2023"
])]

X_train = train_df_lagged[num_features + cat_features]
y_train = train_df_lagged["next_season_goals"]

pipe.fit(X_train, y_train)

#Analyse the encoded feature names
feature_names = pipe.named_steps["preprocess"].get_feature_names_out()
# print(feature_names)

#Analyse the weighted coefficients produced by the model
coefs = pipe.named_steps["model"].coef_

coef_df = (
    pd.DataFrame({
        "feature": feature_names,
        "coef": coefs
    })
    .sort_values("coef", ascending=False)
)

print(coef_df)

"""Predict Haaland's 2025-2026 goals using 2024-2025 features"""
haaland = df[df["playername"]=='Erling Haaland']
haaland_2425 = haaland[haaland["season_year"] == "2024-2025"]
features = ["xg", "g90", "team_xg", "team", "position"]
X_haaland = haaland_2425[features]
predicted_2526_goals = pipe.predict(X_haaland)[0]

# used as the reference for testing predicted 2024/25 results against actual 24/25 results
# in this case, the input to the model would have been the 2023/24 season (see haaland_2425)
# haaland_accGoals = haaland[haaland["season_year"] == "2024-2025"] 
# actualGoals = haaland_accGoals["goals"]
# absError = abs (( (float(actualGoals) - float(predicted_2526_goals) ) / actualGoals) * 100)

print(f"\nPredicting 2025-2026 Season:")
print(f"Predicted Goals for Haaland (2025-2026): {predicted_2526_goals:.2f}")
# print(f"Actual Goals for Haaland (2024-2025): {int(actualGoals)}")
print(f"Based on 2024-2025 features: xG={haaland_2425['xg'].values[0]:.2f}, g90={haaland_2425['g90'].values[0]:.2f}, team_xG={haaland_2425['team_xg'].values[0]:.2f}")
# print(f"Error: {absError}")
conn.close()
