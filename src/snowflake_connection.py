"""Lazy Snowflake connections; importing this module never connects or prints secrets."""
import os
import sys
from getpass import getpass


def connect():
    import snowflake.connector
    settings = {
        'account': os.getenv('SNOWFLAKE_ACCOUNT') or 'KXVXDWF-VGA63262',
        'user': os.getenv('SNOWFLAKE_USER') or 'TARTTICUS',
        'warehouse': os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
        'database': os.getenv('SNOWFLAKE_DATABASE', 'LEAGUEOFSTATS'),
        'schema': os.getenv('SNOWFLAKE_SCHEMA', 'MAIN'),
    }
    settings['authenticator'] = 'username_password_mfa'
    password = os.getenv('SNOWFLAKE_PASSWORD')
    if not password:
        if not sys.stdin.isatty():
            raise ValueError('Run in an interactive terminal or set SNOWFLAKE_PASSWORD')
        password = getpass('Snowflake password (hidden): ')
    if not password:
        raise ValueError('A password is required')
    settings['password'] = password
    if not sys.stdin.isatty():
        raise ValueError('Run in an interactive terminal to enter your MFA code')
    totp_code = getpass('Enter your 6-digit MFA code (hidden): ').strip()
    if len(totp_code) != 6 or not totp_code.isascii() or not totp_code.isdigit():
        raise ValueError('MFA code must contain exactly six digits')
    settings['passcode'] = totp_code
    if not settings['account']:
        raise ValueError('Set SNOWFLAKE_ACCOUNT')
    settings['role'] = os.getenv('SNOWFLAKE_ROLE') or 'ACCOUNTADMIN'
    settings['login_timeout'] = 60
    settings['network_timeout'] = 30
    settings['socket_timeout'] = 15
    print('Connecting to Snowflake with password and MFA code...', flush=True)
    try:
        return snowflake.connector.connect(**settings)
    except snowflake.connector.errors.Error as exc:
        # Preserve diagnostics without exposing the submitted password.
        detail = str(getattr(exc, 'msg', '') or str(exc)).replace(password, '[REDACTED]').replace(totp_code, '[REDACTED]')
        import re
        detail = re.sub(r'https?://\S+', '[URL REDACTED]', detail)
        detail = re.sub(r'(?i)((?:token|password|passcode|secret)\s*[=:]\s*)\S+', r'\1[REDACTED]', detail)
        exc.safe_detail = detail
        raise


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


def main():
    print('Checking Snowflake connection...', flush=True)
    print('Using password and authenticator-app MFA for Snowflake.', flush=True)
    try:
        connection = connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                if cursor.fetchone()[0] != 1:
                    raise RuntimeError('Unexpected connection check result')
            print('Successfully connected to Snowflake.')
        finally:
            connection.close()
    except ValueError as exc:
        print(f'Configuration error: {exc}')
        print('Set SNOWFLAKE_ACCOUNT and SNOWFLAKE_USER in the environment used by VS Code.')
        raise SystemExit(1) from None
    except ImportError:
        print('Missing Snowflake dependency. Run: python -m pip install snowflake-connector-python')
        raise SystemExit(1) from None
    except Exception as exc:
        print(f'Snowflake connection failed ({type(exc).__name__}).')
        print(f"Error code: {getattr(exc, 'errno', None)}; SQL state: {getattr(exc, 'sqlstate', None)}")
        if getattr(exc, 'safe_detail', None):
            print(f'Details: {exc.safe_detail}')
        if not os.getenv('SNOWFLAKE_USER'):
            print('SNOWFLAKE_USER is unset; using TARTTICUS. Verify LOGIN_NAME in Snowsight.')
        print('Use your account identifier for SNOWFLAKE_ACCOUNT (not the Snowsight URL).')
        print('Check account, username, authenticator, browser login, and role/database access.')
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
