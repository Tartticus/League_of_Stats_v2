CREATE TABLE matches (
    match_id NVARCHAR(20) NOT NULL,
    patch_id NVARCHAR(20),
    datetime TIMESTAMP_NTZ,
    game_duration INTEGER,
    game_mode NVARCHAR(20),
    PRIMARY KEY (match_id)
);

CREATE TABLE  player_info (
    match_id NVARCHAR(20) NOT NULL,
    username NVARCHAR(20) NOT NULL,
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
    match_id NVARCHAR(20) NOT NULL,
    champ_name NVARCHAR(20) NOT NULL,
    item1 NVARCHAR(20), item2 NVARCHAR(20), item3 NVARCHAR(20), item4 NVARCHAR(20),
    item5 NVARCHAR(20), item6 NVARCHAR(20), item7 NVARCHAR(20), item8 NVARCHAR(20),
    UNIQUE (match_id, champ_name)
);

CREATE TABLE champ_stats (
    match_id NVARCHAR(20) NOT NULL,
    champ_name NVARCHAR(20) NOT NULL,
    gold_earned INTEGER,
    kills INTEGER,
    deaths INTEGER,
    cs INTEGER,
    vision_score INTEGER,
    UNIQUE (match_id, champ_name)
);
