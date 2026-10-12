import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from flask import current_app, g

def sqlite_path():
    return current_app.config.get("SQLITE_DATABASE") or (
        current_app.config["TEST_DATABASE"] if current_app.config.get("TESTING") else None
    )

def get_db():
    if "db" not in g:
        database = sqlite_path()
        if database:
            # Refuse to silently create an empty database when a path is wrong.
            uri = Path(database).resolve().as_uri() + "?mode=rw"
            g.db = sqlite3.connect(uri, uri=True, timeout=10)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys=ON")
        else:
            import mysql.connector
            g.db = mysql.connector.connect(
                host=os.environ.get("DB_HOST", "127.0.0.1"),
                port=int(os.environ.get("DB_PORT", "3306")),
                user=os.environ["DB_USER"], password=os.environ["DB_PASSWORD"],
                database=os.environ["DB_NAME"], connection_timeout=10,
            )
    return g.db

def cursor():
    db = get_db()
    return db.cursor() if sqlite_path() else db.cursor(dictionary=True)

def query(sql, values=()):
    cur = cursor()
    try:
        cur.execute(sql.replace("%s", "?") if sqlite_path() else sql, values)
        return [dict(row) for row in cur.fetchall()]
    finally:
        cur.close()

def execute(sql, values=()):
    cur = cursor()
    try:
        cur.execute(sql.replace("%s", "?") if sqlite_path() else sql, values)
        return cur.lastrowid, cur.rowcount
    finally:
        cur.close()

@contextmanager
def transaction():
    db = get_db()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise

def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
