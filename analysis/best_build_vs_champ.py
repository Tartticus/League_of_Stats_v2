import pandas as pd
import snowflake.connector
import inquirer
import sys
import os
# External folder for imports
external_path = os.path.abspath("../src") 
sys.path.append(external_path)
from snowflake_connection import cur

cur.execute("""SELECT I.Match_ID, Player_Champ, Opposing_Champ, Win, ITEM1, ITEM2, ITEM3, ITEM4, ITEM5, ITEM6
FROM LEAGUEOFSTATS.MAIN.PLAYER_INFO P 
INNER JOIN LEAGUEOFSTATS.MAIN.ITEMS I on P.Match_ID = I.Match_ID AND P.PLAYER_CHAMP = I.CHAMP_NAME""")


item_stats =  cur.fetchall()

columns = [desc[0] for desc in cur.description]

item_data = pd.DataFrame(data=item_stats, columns = columns)

item_data.columns = item_data.columns.str.lower()

# Convert 'win' column to numeric
item_data['win'] = item_data['win'].astype(int)

# Extract unique champions
player_champs = sorted(item_data['player_champ'].unique())
opposing_champs = sorted(item_data['opposing_champ'].unique())

# Ask user to select champions using inquirer
questions = [
    inquirer.List("player_champ",
                  message="Select your champion",
                  choices=player_champs),
    inquirer.List("opposing_champ",
                  message="Select the opposing champion",
                  choices=opposing_champs)
]

answers = inquirer.prompt(questions)
player_selected = answers["player_champ"]
opponent_selected = answers["opposing_champ"]

print(f"\nAnalyzing best items for {player_selected} vs {opponent_selected}...\n")

# Filter dataset for the selected matchup
filtered_df = item_data[
    (item_data['player_champ'] == player_selected) &
    (item_data['opposing_champ'] == opponent_selected)
]

# Check if there's enough data
if filtered_df.empty:
    print("No data available for this matchup.")
    exit()

# Item columns
item_columns = ['item1', 'item2', 'item3', 'item4', 'item5', 'item6']

# Calculate win rates for each item slot
win_rates = {}
for item_slot in item_columns:
    item_stats = filtered_df.groupby(item_slot)['win'].mean().dropna().sort_values(ascending=False)
    win_rates[item_slot] = item_stats.head(3)  # Show top 3 items per slot

# Format and display results
print(f"Best Items for {player_selected} vs {opponent_selected}:\n")
for slot, stats in win_rates.items():
    print(f"{slot.upper()}:")
    for item, win_rate in stats.items():
        print(f"  {item}: {win_rate:.2%}")
    print()
