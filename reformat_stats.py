import pandas as pd

import pandas as pd

df = pd.read_csv("output/hero_playtime.csv")
# Calculate aggregated kills and deaths for each player
grouped_df = df.groupby("player_name").agg(
    {"kills": "sum", "deaths": "sum"})

# Calculate the difference between kills and deaths
grouped_df["+/-"] = grouped_df["kills"] - grouped_df["deaths"]

# Reset the index and add 'player_name' back as a column
grouped_df.reset_index(inplace=True)

# Create a temporary DataFrame with unique player names and their order
player_order_df = df[['player_name']].drop_duplicates().reset_index(drop=True)
player_order_df['order'] = player_order_df.index

# Merge the grouped DataFrame with the player_order_df based on 'player_name'
grouped_df = pd.merge(player_order_df, grouped_df, on='player_name')

# Sort the DataFrame by the 'order' column and drop it
grouped_df = grouped_df.sort_values('order').drop('order', axis=1)

# Save the result to a new CSV file
grouped_df.to_csv("output/total_kills.csv", index=False, columns=[
                  "player_name", "kills", "deaths", "+/-"])
