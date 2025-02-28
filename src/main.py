import requests
import pandas as pd
import duckdb
import datetime
import time
from snowflake_connection import cur
# Set up API details and DuckDB connection
api_key = 'RGAPI-ddaf216c-35d9-4af8-8749-ba2f95b9eb33'
game_name = 'BlackInter69'
tag_line = 'NA1'
lol_excel = "lol_data.xlsx"
duckdb_conn = duckdb.connect('league_data.db')

# Define function to get item data from Data Dragon API
def get_item_mapping():
    version_url = 'https://ddragon.leagueoflegends.com/api/versions.json'
    version = requests.get(version_url).json()[0]  # Get the latest version

    items_url = f'https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/item.json'
    items_data = requests.get(items_url).json()['data']

    # Create a mapping of item ID to item name
    item_mapping = {int(item_id): item_info['name'] for item_id, item_info in items_data.items()}
    return item_mapping

# Define function to get the player's PUUID
def get_puuid():
    url = f'https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}'
    headers = {'X-Riot-Token': api_key}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('puuid')
    else:
        print("Error fetching summoner data")
        return None

# Define function to get match history IDs
def get_match_ids(puuid,count):
    match_url = f'https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}'
    headers = {'X-Riot-Token': api_key}
    response = requests.get(match_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error fetching match history")
        return []

# Define function to fetch match details
def get_match_details(match_id):
    url = f'https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}'
    headers = {'X-Riot-Token': api_key}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data for match {match_id}")
        return None




def reset_tables():
    #funciton to delete data in all tables   
    duckdb_conn = duckdb.connect('league_data.db')
    duckdb_conn.execute("delete from matches")
    duckdb_conn.execute("delete from items")
    duckdb_conn.execute("delete from champs")
    duckdb_conn.execute("delete from champ_stats")
    duckdb_conn.execute("delete from player_info")
    print("\nTable Data Deleted")


# Main function to fetch match data and populate tables
def fetch_and_store_match_data():
    global game_name
    
    item_mapping = get_item_mapping()
    puuid = get_puuid()
    if not puuid:
        return
    
    #ask user how many games
    while True:
        count = input("\nHow many games would you like to retrieve?\n")
        try:
            # Check if the input is a valid integer
            int(count)
            # Convert the validated integer input to a string
            count = str(count)
            print(f"Retrieving last {count} games for {game_name}")
            break
        except ValueError:
            print("Please enter a valid integer for the number of games.")
    match_ids = get_match_ids(puuid,count)
    
    #count to initialize wait
    match_count = 0
    #wait count variable for api
    wait_count = 0
    for match_id in match_ids:
        match_data = get_match_details(match_id)
        if not match_data:
            continue

        # Extract general match information
        match_count += 1
        wait_count += 1
        match_datetime = datetime.datetime.fromtimestamp(match_data['info']['gameCreation'] / 1000)
        
        
        # Get the game mode and queue ID
        raw_game_mode = match_data['info'].get('gameMode', 'Unknown')
        queue_id = match_data['info'].get('queueId', -1)

        # Set game mode based on queue ID and game mode
        if raw_game_mode == "CLASSIC":
            if queue_id in {420, 440}:  # Ranked Solo/Duo or Ranked Flex queue IDs
                game_mode = "Ranked"
            else:
                game_mode = "Norms"
        else:
            game_mode = raw_game_mode  # Use raw game mode for non-CLASSIC modes
        
        
        game_duration = match_data['info']['gameDuration']
        participant_data = next((p for p in match_data['info']['participants'] if p['puuid'] == puuid), None)
        if not participant_data:
            continue
        
        # patch info
        game_version = match_data["info"]["gameVersion"]
        patch_version = ".".join(game_version.split(".")[:2])
        
        # Win
        win = participant_data['win']
        player_champ = participant_data['championName']
        lane = participant_data['lane']
        team_id = participant_data['teamId']
        
        
        # Function to find the opposing champion in the same lane/position
        opponent_data = next((p for p in match_data['info']['participants'] 
                      if p['puuid'] != puuid 
                      and p['lane'] == lane 
                      and p['teamId'] != team_id), None)
        
        try:
            opposing_champ = opponent_data['championName']
            
        except TypeError:
            #if cant find opposing champ, put unknown
            opposing_champ = "Unknown"
            
        
        # Insert into matches table dont insert duplicate
        cur.execute("""
            INSERT INTO matches (match_id, patch_id, datetime, game_duration, game_mode)
            VALUES (%s, %s, %s, %s, %s)
        """, (match_id, patch_version, match_datetime, game_duration, game_mode))

        
        # Insert into player_info table
        cur.execute("""
            INSERT INTO player_info (match_id, username,player_champ, opposing_champ, win, lane_played)
            VALUES (%s, %s, %s, %s, %s,%s)
        """, (match_id, game_name, player_champ, opposing_champ, win, lane))
        
        # Collect friendly champions
        friend_champs = [p['championName'] for p in match_data['info']['participants'] if p['teamId'] == participant_data['teamId']]
        friend_champs += [None] * (5 - len(friend_champs))  # Pad to ensure 5 entries
        
        #collect enemy champs
        enemy_champs = [p['championName'] for p in match_data['info']['participants'] if p['teamId'] != participant_data['teamId']]
        enemy_champs += [None] * (5 - len(friend_champs))  # Pad to ensure 5 entries

        # Insert into champs table
        cur.execute("""
            INSERT INTO champs (match_id, friend_champ1, friend_champ2, friend_champ3, friend_champ4, friend_champ5, enemy_champ1, enemy_champ2, enemy_champ3, enemy_champ4, enemy_champ5)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (match_id, *friend_champs, *enemy_champs))

        for champ in friend_champs + enemy_champs:
            if champ:  # Ensure it's not None
                # Find the participant data for this champion
                champ_data = next((p for p in match_data['info']['participants'] if p['championName'] == champ), None)
                
                if champ_data:
                    # Collect items (up to 8)
                    items = [
                        item_mapping.get(champ_data.get(f'item{i}', 'Unknown'), 'Unknown')
                        for i in range(8)
                    ]

                    # Insert into items table
                    cur.execute("""
                        INSERT INTO items (match_id, champ_name, item1, item2, item3, item4, item5, item6, item7, item8)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
                    """, (match_id, champ, *items))
                    
                    # Extract CS and Vision Score
                    gold_earned = champ_data.get("goldEarned", 0)  # Default to 0 if missing
                    cs = champ_data.get("totalMinionsKilled", 0) + champ_data.get("neutralMinionsKilled", 0)  # CS includes jungle creeps
                    vision_score = champ_data.get("visionScore", 0)
                    kills = champ_data.get("kills", 0)
                    deaths = champ_data.get("deaths", 0)
                    
                    cur.execute("""
                        INSERT INTO champ_stats (match_id, champ_name, gold_earned, kills, deaths, cs, vision_score)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (match_id, champ, gold_earned, kills, deaths, cs, vision_score))

        print(f"Inserted match {match_count} out of {count}: {match_id} from {match_datetime}")
        #Api wait section
        if wait_count == 25 and match_count != count:
            print("\nWaiting 15 sec for api rate limit...\n")
            time.sleep(15)
            wait_count = 0
    print("-----------------------------------------------------")        
    print(f"\n{match_count} Matches inserted for {game_name}\n")


def main():
    # create tables
    #ask if wants to reset tables
    global game_name
    while True:
        decision = input("Would you like to delete existing table data? y or n?:\n")
        if decision.lower() == 'y':
            print("\nDeleting table data")
            reset_tables()
            break
        if decision.lower() == 'n':
            break
        else:
            print("\nPlease enter y or n")
    game_name = input("\nWhat is your summoner_name?:\n").strip()      
    
    fetch_and_store_match_data()
    
    """ 
    lol_df = duckdb_conn.execute("SELECT *
    FROM matches
    JOIN champs ON matches.match_id = champs.match_id
    JOIN items ON matches.match_id = items.match_id
    JOIN champ_stats ON matches.match_id = champ_stats.match_id;").df()
    
    
    lol_df.to_excel(lol_excel)
    return print(f"Excel File Updated at {lol_excel}")
    """

# Run main function
main()
