"""Initialize a persistent local database without enabling Flask test mode."""
import argparse
import os
import sqlite3
from pathlib import Path
from workapi import FIELDS


def initialize_database(filename):
    path = Path(filename).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with sqlite3.connect(path) as connection:
        connection.execute("BEGIN IMMEDIATE")
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        if version not in (0, 1) or (version == 0 and tables):
            raise ValueError("Unrecognized local database; no schema changes were made")
        if version == 0:
            connection.execute(
                "CREATE TABLE person(personId INTEGER PRIMARY KEY AUTOINCREMENT,"
                "personName TEXT NOT NULL,personWx TEXT NOT NULL,"
                "active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)))"
            )
            fields = ",".join(name + " TEXT NOT NULL DEFAULT ''" for name in FIELDS)
            connection.execute(
                "CREATE TABLE work(workId INTEGER PRIMARY KEY AUTOINCREMENT,"
                "workIdentifier TEXT NOT NULL UNIQUE," + fields + ","
                "createTime TEXT NOT NULL,version INTEGER NOT NULL DEFAULT 1 CHECK(version>0),"
                "archived INTEGER NOT NULL DEFAULT 0 CHECK(archived IN (0,1)))"
            )
            connection.execute(
                "CREATE TABLE work_history(historyId INTEGER PRIMARY KEY AUTOINCREMENT,"
                "workIdentifier TEXT NOT NULL REFERENCES work(workIdentifier),"
                "action TEXT NOT NULL,actor TEXT NOT NULL,beforeData TEXT,afterData TEXT,"
                "reason TEXT NOT NULL,createdAt TEXT NOT NULL)"
            )
            connection.execute("CREATE INDEX history_work ON work_history(workIdentifier)")
            connection.execute("PRAGMA user_version=1")
        connection.commit()
        connection.execute("PRAGMA journal_mode=WAL")
    os.chmod(path, 0o600)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database")
    print(initialize_database(parser.parse_args().database))
