import os

import psycopg

from dotenv import load_dotenv


# Load .env file

load_dotenv()


# Get the connection string from the environment variable

connection_string = os.getenv("DATABASE_URL")


# Connect to the Postgres database

with psycopg.connect(connection_string) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT NOW();")
        time = cur.fetchone()[0]
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        cur.close()
        conn.close()
        print("Current time:", time)
        print("PostgreSQL version:", version)
