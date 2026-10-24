"""Completed-match importer. Run from the repository: python src/ingest.py --help."""
import argparse
import json
import os
from pathlib import Path
import time
from urllib.parse import quote

import requests
from snowflake_connection import connect


class RiotClient:
    def __init__(self, key, region='americas', account_region='americas', session=None, sleep=time.sleep):
        if region not in {'americas', 'asia', 'europe', 'sea'}:
            raise ValueError('Invalid match routing region')
        if account_region not in {'americas', 'asia', 'europe'}:
            raise ValueError('Invalid account routing region')
        self.region, self.account_region = region, account_region
        self.session = session or requests.Session()
        self.key, self.sleep = key, sleep

    def get(self, path, params=None, account=False):
        region = self.account_region if account else self.region
        for attempt in range(5):
            try:
                response = self.session.get(
                    f'https://{region}.api.riotgames.com{path}', params=params,
                    headers={'X-Riot-Token': self.key}, timeout=30)
            except requests.RequestException:
                if attempt == 4:
                    raise RuntimeError('Riot network request failed') from None
                self.sleep(2 ** attempt)
                continue
            if response.status_code == 429 or 500 <= response.status_code < 600:
                if attempt == 4:
                    break
                try:
                    delay = max(0, float(response.headers.get('Retry-After', 2 ** attempt)))
                except ValueError:
                    delay = 2 ** attempt
                self.sleep(delay)
                continue
            if response.status_code != 200:
                raise RuntimeError(f'Riot request failed (HTTP {response.status_code})')
            return response.json()
        raise RuntimeError('Riot retry limit reached')

    def match_ids(self, puuid, count):
        start = 0
        while start < count:
            size = min(100, count - start)
            batch = self.get(f'/lol/match/v5/matches/by-puuid/{quote(puuid, safe="")}/ids',
                             {'start': start, 'count': size})
            yield from batch
            if len(batch) < size:
                break
            start += len(batch)


def store_match(connection, match, timeline):
    match_id = match['metadata']['matchId']
    if timeline['metadata']['matchId'] != match_id:
        raise ValueError('Match and timeline IDs differ')
    with connection.cursor() as cursor:
        cursor.execute('BEGIN')
        try:
            for table, payload in [('RAW_MATCHES', match), ('RAW_TIMELINES', timeline)]:
                cursor.execute(f'''MERGE INTO BRONZE.{table} t
                    USING (SELECT %s::VARCHAR AS match_id, PARSE_JSON(%s) AS payload) s
                    ON t.match_id = s.match_id
                    WHEN MATCHED THEN UPDATE SET payload=s.payload, retrieved_at=CURRENT_TIMESTAMP()
                    WHEN NOT MATCHED THEN INSERT (match_id, retrieved_at, payload)
                    VALUES (s.match_id, CURRENT_TIMESTAMP(), s.payload)''',
                    (match_id, json.dumps(payload)))
            connection.commit()
        except Exception:
            connection.rollback()
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-name', required=True)
    parser.add_argument('--tag-line', required=True)
    parser.add_argument('--count', type=int, default=5)
    parser.add_argument('--region', default='americas')
    parser.add_argument('--account-region', default='americas')
    parser.add_argument('--init-schema', action='store_true')
    args = parser.parse_args()
    if args.count < 1:
        parser.error('--count must be positive')
    key = os.getenv('RIOT_API_KEY')
    if not key:
        parser.error('Set RIOT_API_KEY in your environment')
    client = RiotClient(key, args.region, args.account_region)
    account = client.get('/riot/account/v1/accounts/by-riot-id/' +
                         quote(args.game_name, safe='') + '/' + quote(args.tag_line, safe=''), account=True)
    connection = connect()
    try:
        if args.init_schema:
            sql = (Path(__file__).resolve().parents[1] / 'sql' / 'companion.sql').read_text(encoding='utf-8-sig')
            with connection.cursor() as cursor:
                for statement in sql.split(';'):
                    if statement.strip():
                        cursor.execute(statement)
        for match_id in dict.fromkeys(client.match_ids(account['puuid'], args.count)):
            path = '/lol/match/v5/matches/' + quote(match_id, safe='')
            match = client.get(path)
            timeline = client.get(path + '/timeline')
            store_match(connection, match, timeline)
            print(f'Stored {match_id}')
    finally:
        connection.close()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        raise SystemExit('Import failed. Check configuration, API access and schema privileges; no credentials were logged.') from None
