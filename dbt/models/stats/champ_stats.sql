SELECT 
 P.match_id
 ,M.datetime
,username
,player_champ
,opposing_champ
,lane_played
,win
,M.Game_Mode
,M.game_duration
,C.gold_earned
,C.kills
,C.deaths
,C.assists
,C.CS/(M.GAME_DURATION/60) AS "CS/Min"
,C.VISION_SCORE



FROM PLAYER_INFO P 
INNER JOIN MATCHES M ON M.MATCH_ID = P.MATCH_ID
INNER JOIN ITEMS I ON I.CHAMP_NAME = P.PLAYER_CHAMP AND I.MATCH_ID = P.MATCH_ID
INNER JOIN CHAMP_STATS C ON C.CHAMP_NAME = P.PLAYER_CHAMP AND C.MATCH_ID = P.MATCH_ID

WHERE M.GAME_DURATION > 600
