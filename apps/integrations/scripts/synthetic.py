import numpy as np
import pandas as pd

df = pd.read_csv("/Users/saschahofmann/Downloads/google_analytics.csv")

# Create date column currently string
df["date"] = pd.to_datetime(df.date, format="%Y-%m-%d")

# Periodically add data
days = df.date.max() - df.date.min()
df_c = df.copy()
new_dfs = []

for _ in range(10):
    df_c = df_c.copy()
    df_c["date"] = df_c.date + days
    new_dfs.append(df_c)

df = pd.concat([df, *new_dfs])

# Obfuscate metrics by multiplying with normal distribution

df.transaction_revenue = df.transaction_revenue * np.random.normal(1, size=len(df))
df.transactions = df.transactions * np.random.normal(1, size=len(df))
df.users = df.users * np.random.normal(1, size=len(df))

# Save
df.to_csv("/Users/saschahofmann/Downloads/ga.csv")
