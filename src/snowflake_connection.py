"""Lazy Snowflake connections; importing this module never connects or prints secrets."""
import os


def connect():
    import snowflake.connector
    settings = {
        'account': os.getenv('SNOWFLAKE_ACCOUNT') or os.getenv('Snow_Account'),
        'user': os.getenv('SNOWFLAKE_USER', 'LEAGUEOFSTATS'),
        'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
        'database': os.getenv('SNOWFLAKE_DATABASE', 'LEAGUEOFSTATS'),
        'schema': os.getenv('SNOWFLAKE_SCHEMA', 'MAIN'),
    }
    authenticator = os.getenv('SNOWFLAKE_AUTHENTICATOR', 'snowflake')
    settings['authenticator'] = authenticator
    if authenticator != 'externalbrowser':
        settings['password'] = os.getenv('SNOWFLAKE_PASSWORD') or os.getenv('passwordLoLstats')
        if not settings['password']:
            raise ValueError('Set SNOWFLAKE_PASSWORD or use externalbrowser authentication')
    if not settings['account']:
        raise ValueError('Set SNOWFLAKE_ACCOUNT')
    if os.getenv('SNOWFLAKE_ROLE'):
        settings['role'] = os.environ['SNOWFLAKE_ROLE']
    return snowflake.connector.connect(**settings)


# Compatibility for existing scripts using `from snowflake_connection import cur`.
class LazyCursor:
    def __init__(self):
        self.connection = None
        self.cursor = None

    def __getattr__(self, name):
        if self.cursor is None:
            self.connection = connect()
            self.cursor = self.connection.cursor()
        return getattr(self.cursor, name)


cur = LazyCursor()
