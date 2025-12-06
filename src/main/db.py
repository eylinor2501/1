# db.py
import sqlite3

DB_NAME = "worktime.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row       # чтобы удобно читать по именам полей
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn
