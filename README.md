## League of Stats v2 Snowflake Edition

First Run utility/bulk_load.py to catchup on games for your acct
Schedule main to run on an interval you decide (retrieves last 10 games, try to run once a day minimum)

## Vladimir Companion: Snowflake ingestion

Use a personally owned or explicitly authorized Snowflake account. The new importer
is separate from the legacy scripts and does not interact with the running game.

1. Install dependencies: `python -m pip install -r requirements.txt`.
2. Set the environment variables listed in `.env.example` in your shell.
   The template is documentation; `.env` files are not automatically loaded.
   For browser authentication, set `SNOWFLAKE_AUTHENTICATOR=externalbrowser` and
   omit the password. The database and warehouse must already exist.
3. Initialize and import five completed matches:
   `python src/ingest.py --game-name BlackInter69 --tag-line NA1 --count 5 --init-schema`
4. Repeat without `--init-schema` for subsequent imports. Use `--region` for match
   routing and `--account-region` for account routing (both default to americas).

The schema in `sql/companion.sql` creates BRONZE raw match/timeline tables and
SILVER views for matches, participants, participant frames, and champion kill events.
Run one importer at a time: MERGE supports sequential reruns, but concurrent writers
are not protected by enforced uniqueness constraints. Each match/timeline pair is
committed together. Missing timelines stop the import; reruns safely update earlier
matches. Kill event identity is `(match_id, frame_index, event_index)`.
Raw payloads preserve participant items, runes and source evidence for later analytics.
These views do not populate legacy MAIN tables or existing dbt models.

Run offline checks: `python -m unittest discover -s tests -v`.
Live API, Snowflake SQL and account privileges require a separate integration run.
To delete this new dataset, remove the relevant BRONZE rows or dedicated schemas in
Snowflake after confirming scope; SILVER views reflect deletion immediately.

Legacy `src/main.py` remains a work in progress and contains a hardcoded Riot key.
Replace/revoke that exposed key and use RIOT_API_KEY with the new importer.
The Snowflake connection module no longer prints passwords or connects on import.
