import os
import sqlite3
from contextlib import contextmanager
from flask import current_app, g

def get_db():
    if "db" not in g:
        if current_app.config.get("TESTING"):
            g.db = sqlite3.connect(current_app.config["TEST_DATABASE"])
            g.db.row_factory = sqlite3.Row
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
    return db.cursor() if current_app.config.get("TESTING") else db.cursor(dictionary=True)

def query(sql, values=()):
    cur = cursor()
    try:
        cur.execute(sql.replace("%s", "?") if current_app.config.get("TESTING") else sql, values)
        return [dict(row) for row in cur.fetchall()]
    finally:
        cur.close()

def execute(sql, values=()):
    cur = cursor()
    try:
        cur.execute(sql.replace("%s", "?") if current_app.config.get("TESTING") else sql, values)
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
