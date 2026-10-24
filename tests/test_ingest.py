import sys
from pathlib import Path
import unittest
from unittest.mock import MagicMock
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from ingest import RiotClient, store_match


class ImportTests(unittest.TestCase):
    def test_pagination(self):
        client = RiotClient('test')
        client.get = MagicMock(side_effect=[list(map(str, range(100))), ['last']])
        self.assertEqual(len(list(client.match_ids('player', 101))), 101)
        self.assertEqual(client.get.call_args.args[1], {'start': 100, 'count': 1})

    def test_retry_after(self):
        session, sleep = MagicMock(), MagicMock()
        session.get.side_effect = [MagicMock(status_code=429, headers={'Retry-After': '3'}),
                                   MagicMock(status_code=200, json=lambda: {'ok': True})]
        client = RiotClient('test', session=session, sleep=sleep)
        self.assertEqual(client.get('/test'), {'ok': True})
        sleep.assert_called_once_with(3)

    def test_pair_commit_and_bound_payload(self):
        connection = MagicMock()
        payload = {'metadata': {'matchId': 'NA1_1'}}
        store_match(connection, payload, payload)
        connection.commit.assert_called_once()
        cursor = connection.cursor.return_value.__enter__.return_value
        self.assertEqual(cursor.execute.call_count, 3)
        self.assertEqual(cursor.execute.call_args.args[1][0], 'NA1_1')
        self.assertIn('MERGE INTO', cursor.execute.call_args.args[0])

    def test_rollback(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.execute.side_effect = [None, None, RuntimeError('failed')]
        payload = {'metadata': {'matchId': 'NA1_1'}}
        with self.assertRaises(RuntimeError):
            store_match(connection, payload, payload)
        connection.rollback.assert_called_once()
        connection.commit.assert_not_called()

    def test_mismatched_ids(self):
        connection = MagicMock()
        with self.assertRaises(ValueError):
            store_match(connection, {'metadata': {'matchId': 'a'}}, {'metadata': {'matchId': 'b'}})
        connection.cursor.assert_not_called()


if __name__ == '__main__':
    unittest.main()
