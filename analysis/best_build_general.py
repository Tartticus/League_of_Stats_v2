import pandas as pd
import snowflake.connector
import inquirer
import sys

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

# Convert 'win' column to numeric (1 for win, 0 for loss)
item_data['win'] = item_data['win'].astype(int)

# Extract unique champions
player_champs = sorted(item_data['player_champ'].unique()) 


# Simple input selection (Spyder-friendly)
print("\nAvailable Champions:")
for i, champ in enumerate(player_champs):
    print(f"{i}: {champ}")

# Get user input (integer index)
while True:
    try:
        player_choice = int(input("\nEnter the number of your champion: "))
        if 0 <= player_choice < len(player_champs):
            player_selected = player_champs[player_choice]
            break
        else:
            print("Invalid selection. Please enter a valid number.")
    except ValueError:
        print("Invalid input. Please enter a number.")

print(f"\nAnalyzing best build order for {player_selected}...\n")

# Filter data for the selected champion
filtered_df = item_data[item_data['player_champ'] == player_selected]

# Ensure we have enough data
if filtered_df.empty:
    print("No data found for this champion.")
    exit()

# Item slots
item_columns = ['item1', 'item2', 'item3', 'item4', 'item5', 'item6']

# Calculate win rates for each item in each slot
win_rates = {}
for slot in item_columns:
    item_stats = filtered_df.groupby(slot)['win'].mean().dropna().sort_values(ascending=False)
    win_rates[slot] = item_stats

# Determine the best build order based on win rates in each slot
best_build = []
for slot, stats in win_rates.items():
    if not stats.empty:
        best_item = stats.idxmax()  # Get the item with the highest win rate
        best_build.append((slot, best_item, stats.max()))  # Store (slot, item, win rate)

# Sort build order by slot number (ensuring proper sequence)
best_build.sort(key=lambda x: int(x[0][-1]))  # Sort by item slot number

# Display results
print("Best Build Order for Maximum Wins:\n")
for slot, item, win_rate in best_build:
    print(f"{slot.upper()}: {item} (Win Rate: {win_rate:.2%})")

print(f"\nThis build order is based on historical win rates while playing {player_selected}.")
