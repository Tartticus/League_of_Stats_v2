import snowflake.connector
import os
#Get password from os var

sign_pass = os.getenv("passwordLoLstats")
account =  os.getenv("Snow_Account")
# Establish connection
conn = snowflake.connector.connect(
    user="LEAGUEOFSTATS",
    password=sign_pass,
    account=account, 
    warehouse="COMPUTE_WH",
    database="LEAGUEOFSTATS",
    schema="MAIN"
)

# Create a cursor object
cur = conn.cursor()

print(cur)


