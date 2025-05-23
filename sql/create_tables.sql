CREATE TABLE matches (
    match_id NVARCHAR(20) NOT NULL,
    patch_id NVARCHAR(20),
    datetime TIMESTAMP_NTZ,
    game_duration FLOAT,
    game_mode NVARCHAR(20),
    region NVARCHAR(5),
    PRIMARY KEY (match_id)
);

CREATE TABLE  player_info (
    match_id NVARCHAR(20) NOT NULL,
    username NVARCHAR(20) NOT NULL,
    team_id NVARCHAR(15),
    player_champ NVARCHAR(20),
    opposing_champ NVARCHAR(20),
    win BOOLEAN,
    lane_played NVARCHAR(20),
    UNIQUE (match_id, username)
);

CREATE TABLE champs (
    match_id NVARCHAR(20) NOT NULL,
    friend_champ1 NVARCHAR(20),
    friend_champ2 NVARCHAR(20),
    friend_champ3 NVARCHAR(20),
    friend_champ4 NVARCHAR(20),
    friend_champ5 NVARCHAR(20),
    enemy_champ1 NVARCHAR(20),
    enemy_champ2 NVARCHAR(20),
    enemy_champ3 NVARCHAR(20),
    enemy_champ4 NVARCHAR(20),
    enemy_champ5 NVARCHAR(20),
    PRIMARY KEY (match_id)
);

CREATE TABLE items (
    match_id NVARCHAR(20) NOT NULL
    ,champ_name NVARCHAR(20) NOT NULL
    ,primary_rune NVARCHAR(20)
    ,secondary_rune NVARCHAR(20)
    ,item1 NVARCHAR(40) 
    ,purchase_time1 FLOAT
    ,item2 NVARCHAR(40)
    ,purchase_time2 FLOAT
    ,item3 NVARCHAR(40)
    ,purchase_time3 FLOAT
    ,item4 NVARCHAR(40)
    ,purchase_time4 FLOAT
    ,item5 NVARCHAR(40) 
    ,purchase_time5 FLOAT
    ,item6 NVARCHAR(40) 
    ,purchase_time6 FLOAT
    ,item7 NVARCHAR(40)
    ,purchase_time7 FLOAT
    ,item8 NVARCHAR(40) 
    ,purchase_time8 FLOAT
    ,UNIQUE (match_id, champ_name)
);

CREATE TABLE champ_stats (
    match_id NVARCHAR(20) NOT NULL,
    champ_name NVARCHAR(20) NOT NULL,
    gold_earned INTEGER,
    kills INTEGER,
    deaths INTEGER,
    assists INTEGER,
    cs INTEGER,
    vision_score INTEGER,
    UNIQUE (match_id, champ_name)
);
