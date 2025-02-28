import pandas as pd
import snowflake.connector
import inquirer
import sys
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
external_path = os.path.abspath("../src") 
sys.path.append(external_path)
from snowflake_connection import cur

cur.execute("""SELECT DISTINCT(P.Match_ID), datetime, username, Player_Champ, OPPOSING_CHAMP, LANE_PLAYED, WIN, Kills, Deaths, CS/(M.game_duration/60) as "cs/min", VISION_SCORE FROM LEAGUEOFSTATS.MAIN.PLAYER_INFO P 
INNER JOIN LEAGUEOFSTATS.MAIN.CHAMP_STATS C ON C.MATCH_ID =  P.Match_ID AND  C.champ_name = P.PLAYER_CHAMP
INNER JOIN LEAGUEOFSTATS.MAIN.Matches M on M.MATCH_ID = P.Match_ID
WHERE Player_Champ = 'Vladimir' """)

champ_stats =  cur.fetchall()

columns = [desc[0] for desc in cur.description]

champ_data = pd.DataFrame(data=champ_stats, columns = columns)

#Plot cs/time
def plot_cs_overtime(champ_data):
    # Ensure datetime is in correct format and sort it
    champ_data['DATETIME'] = pd.to_datetime(champ_data['DATETIME'])
    champ_data = champ_data.sort_values(by='DATETIME')
    
    
    
    # Set up the figure
    plt.figure(figsize=(12, 6))
    
    # Line plot
    plt.plot(champ_data['DATETIME'], champ_data['cs/min'], marker='o', linestyle='-', label='CS/Min', color='blue')
    
    # Improve x-axis readability
    plt.xlabel("Datetime")
    plt.ylabel("CS/Min")
    plt.title("CS/Min Over Time")
    plt.xticks(rotation=45)
    
    # Format x-axis to avoid clutter
    plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())  # Auto-adjusts date ticks
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))  # Formats dates
    
    plt.legend()
    plt.grid(True)
    
    # Show plot
    plt.show()

cur.execute("""SELECT DISTINCT(P.Match_ID), datetime, username, Player_Champ, OPPOSING_CHAMP, LANE_PLAYED, WIN, Kills, Deaths, CS/(M.game_duration/60) as "cs/min", VISION_SCORE FROM LEAGUEOFSTATS.MAIN.PLAYER_INFO P 
INNER JOIN LEAGUEOFSTATS.MAIN.CHAMP_STATS C ON C.MATCH_ID =  P.Match_ID AND  C.champ_name = P.PLAYER_CHAMP
INNER JOIN LEAGUEOFSTATS.MAIN.Matches M on M.MATCH_ID = P.Match_ID
WHERE Player_Champ = 'Vladimir' """)

champ_stats =  cur.fetchall()

columns = [desc[0] for desc in cur.description]

champ_data = pd.DataFrame(data=champ_stats, columns = columns)
