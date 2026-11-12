import mysql.connector
from config import Config


def get_connection():

    print("DB STEP 1: Starting MySQL connection", flush=True)

    try:

        conn = mysql.connector.connect(
            host="127.0.0.1",
            port=3306,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            connection_timeout=5
        )

        print("DB STEP 2: MySQL connection successful", flush=True)

        return conn

    except mysql.connector.Error as e:

        print("DB ERROR:", e, flush=True)

        raise