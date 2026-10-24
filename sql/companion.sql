CREATE SCHEMA IF NOT EXISTS BRONZE;
CREATE SCHEMA IF NOT EXISTS SILVER;
CREATE TABLE IF NOT EXISTS BRONZE.RAW_MATCHES (match_id VARCHAR NOT NULL, retrieved_at TIMESTAMP_TZ, payload VARIANT);
CREATE TABLE IF NOT EXISTS BRONZE.RAW_TIMELINES (match_id VARCHAR NOT NULL, retrieved_at TIMESTAMP_TZ, payload VARIANT);
CREATE OR REPLACE VIEW SILVER.MATCHES AS
SELECT match_id, payload:info:gameVersion::VARCHAR AS game_version,
       TO_TIMESTAMP_NTZ(payload:info:gameCreation::NUMBER, 3) AS created_at,
       payload:info:gameDuration::NUMBER AS duration_seconds,
       payload:info:queueId::NUMBER AS queue_id
FROM BRONZE.RAW_MATCHES;
CREATE OR REPLACE VIEW SILVER.PARTICIPANTS AS
SELECT r.match_id, p.value:participantId::NUMBER AS participant_id,
       p.value:puuid::VARCHAR AS puuid, p.value:championName::VARCHAR AS champion,
       p.value:teamId::NUMBER AS team_id, p.value:teamPosition::VARCHAR AS team_position,
       p.value:win::BOOLEAN AS win, p.value:kills::NUMBER AS kills,
       p.value:deaths::NUMBER AS deaths, p.value:assists::NUMBER AS assists,
       p.value:totalMinionsKilled::NUMBER + p.value:neutralMinionsKilled::NUMBER AS cs,
       p.value AS payload
FROM BRONZE.RAW_MATCHES r, LATERAL FLATTEN(input => r.payload:info:participants) p;
CREATE OR REPLACE VIEW SILVER.TIMELINE_FRAMES AS
SELECT r.match_id, p.value:participantId::NUMBER AS participant_id,
       f.value:timestamp::NUMBER AS timestamp_ms,
       p.value:position:x::NUMBER AS x, p.value:position:y::NUMBER AS y,
       p.value:minionsKilled::NUMBER AS lane_cs, p.value:jungleMinionsKilled::NUMBER AS jungle_cs,
       p.value:level::NUMBER AS level, p.value:xp::NUMBER AS xp,
       p.value:totalGold::NUMBER AS total_gold
FROM BRONZE.RAW_TIMELINES r, LATERAL FLATTEN(input => r.payload:info:frames) f,
     LATERAL FLATTEN(input => f.value:participantFrames) p;
CREATE OR REPLACE VIEW SILVER.KILL_EVENTS AS
SELECT r.match_id, f.index AS frame_index, e.index AS event_index,
       e.value:timestamp::NUMBER AS timestamp_ms, e.value:killerId::NUMBER AS killer_id,
       e.value:victimId::NUMBER AS victim_id, e.value:assistingParticipantIds AS assistant_ids,
       e.value:position:x::NUMBER AS x, e.value:position:y::NUMBER AS y, e.value AS payload
FROM BRONZE.RAW_TIMELINES r, LATERAL FLATTEN(input => r.payload:info:frames) f,
     LATERAL FLATTEN(input => f.value:events) e
WHERE e.value:type::VARCHAR = 'CHAMPION_KILL';
