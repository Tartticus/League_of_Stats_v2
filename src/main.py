import requests
import pandas as pd
import duckdb
import datetime
import time
import snowflake.connector
from snowflake_connection import cur
import os


api_key = os.getenv("LoL_API_Key")
game_name = 'BlackInter69'
tag_line = 'NA1'


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
def get_match_ids(puuid):
    #look at last 10 matches
    match_url = f'https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count=10'
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



   
def process_match_header(match_id, match_data):
    
    
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
    
    puuid = get_puuid()
    participant_data = next((p for p in match_data['info']['participants'] if p['puuid'] == puuid), None)
    if not participant_data:
        return
    
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
        
    
    # Insert into matches table dont insert duplicates
    cur.execute("""
        INSERT INTO matches (match_id, patch_id, datetime, game_duration, game_mode)
        VALUES (%s, %s, %s, %s, %s)
    """, (match_id, patch_version, match_datetime, game_duration, game_mode))

    
    # Insert into player_info table
    cur.execute("""
        INSERT INTO player_info (match_id, username,player_champ, opposing_champ, win, lane_played)
        VALUES (%s, %s, %s, %s, %s,%s)
    """, (match_id, game_name, player_champ, opposing_champ, win, lane))        
        
def process_champ_stats(match_id, match_data):
        
        puuid = get_puuid()
        participant_data = next((p for p in match_data['info']['participants'] if p['puuid'] == puuid), None)
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
                    item_mapping = get_item_mapping()
                    
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
        return
        


def main():
    # create tables
    #ask if wants to reset tables
    global game_name
    
    puuid = get_puuid()
    match_ids = get_match_ids(puuid)
         
    
    #count to initialize wait
    match_count = 0
    
    #Extract max datetime in DB for indexing
    cur.execute("SELECT MAX(datetime) FROM matches")
    datetimemax = cur.fetchone()
    datetime_index = datetimemax[0]
    
    
    for match_id in match_ids:
    # Extract general match information
    #keep track of inserions
        
          
        match_data = get_match_details(match_id)
        try:
            match_datetime = datetime.datetime.fromtimestamp(match_data['info']['gameCreation'] / 1000)
        except Exception as e:
            print(e)
            continue
        
        if datetime_index >= match_datetime:
            print(f"{match_id} already in DB, skipping")
            continue
        if not match_data:
            continue
        process_match_header(match_id, match_data)
        process_champ_stats(match_id, match_data)
        match_count += 1
        
        print(f"Inserted match: {match_id} from {match_datetime}")
       
        
    print("-----------------------------------------------------")        
    print(f"\n{match_count} Matches inserted for {game_name}\n")

# Run main function
if __name__ == "__main__":
    main()
