import os
import psycopg2
from contextlib import contextmanager
from psycopg2.extras import RealDictCursor
from db_config import DB_CONFIG


def _cfg(key: str, default: str | None = None) -> str | None:
    """
    Read DB config from environment first (PG* vars), then fall back to DB_CONFIG.
    This lets you run locally with db_config.py, but deploy with env vars.
    """
    env_map = {
        "dbname": "PGDATABASE",
        "user": "PGUSER",
        "password": "PGPASSWORD",
        "host": "PGHOST",
        "port": "PGPORT",
    }
    env_key = env_map.get(key)
    return os.getenv(env_key) or DB_CONFIG.get(key, default)


def get_db_connection(dict_rows: bool = False):
    """
    Create and return a psycopg2 connection.
    If dict_rows=True, cursors will return rows as dictionaries.
    """
    try:
        kwargs = dict(
            dbname=_cfg("dbname"),
            user=_cfg("user"),
            password=_cfg("password"),
            host=_cfg("host"),
            port=_cfg("port"),
        )
        if dict_rows:
            kwargs["cursor_factory"] = RealDictCursor
        return psycopg2.connect(**kwargs)
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


@contextmanager
def get_cursor(dict_rows: bool = False):
    """
    Context manager that yields a cursor and handles commit/rollback/close.

    Usage:
        with get_cursor() as cur:
            cur.execute("SELECT 1")
            print(cur.fetchone())
    """
    conn = get_db_connection(dict_rows=dict_rows)
    if conn is None:
        raise RuntimeError("Could not establish database connection.")
    try:
        with conn:
            with conn.cursor() as cur:
                yield cur
    except Exception:
        raise
    finally:
        try:
            conn.close()
        except Exception:
            pass