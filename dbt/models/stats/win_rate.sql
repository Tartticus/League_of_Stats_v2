{{ config(
    materialized='table',
    alias='Champ_Winrates'
) }}
SELECT player_champ, (100*COUNT(CASE WHEN WIN = 'True' THEN 1 END)/COUNT(WIN)) As "win_rate%" , COUNT(WIN) as games_played FROM LEAGUEOFSTATS.MAIN.PLAYER_INFO P 
INNER JOIN MATCHES M ON M.MATCH_ID = P.MATCH_ID

WHERE M.GAME_MODE = 'Ranked'
group by player_champ
