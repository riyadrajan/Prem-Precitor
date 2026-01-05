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

#filter out test year (2024 - 2025)
train_df = df[df["season_year"].isin([
    "2020-2021",
    "2021-2022",
    "2022-2023",
    "2023-2024"
])]

test_df = df[df["season_year"] == "2024-2025"]


X_train = train_df[num_features + cat_features]
y_train = train_df["goals"].astype(int)

pipe.fit(X_train, y_train)
test_df["predicted goals"] = pipe.predict(test_df[num_features + cat_features])

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

# print(coef_df)

conn.close()
