import psycopg2
from psycopg2.extras import RealDictCursor
from db_config import DB_CONFIG

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_CONFIG["dbname"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"]
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None