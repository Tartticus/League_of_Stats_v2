import os
import getpass
import snowflake.connector

password = os.getenv("SNOWFLAKE_PASSWORD")

if not password:
    password = getpass.getpass("Snowflake password: ")

totp_code = getpass.getpass("Enter your 6-digit MFA code: ")

conn = snowflake.connector.connect(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    user=os.environ["SNOWFLAKE_USER"],
    password=password,
    authenticator="username_password_mfa",
    passcode=totp_code,
    role=os.environ["SNOWFLAKE_ROLE"],
)

try:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            CURRENT_USER(),
            CURRENT_ROLE(),
            CURRENT_DATABASE(),
            CURRENT_WAREHOUSE()
    """)
    print("Connected successfully!")
    print(cursor.fetchone())
finally:
    conn.close()