# db.py
import sqlite3

DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            tg_id INTEGER UNIQUE,
            username TEXT,
            full_name TEXT,
            age INTEGER,
            sat_score INTEGER,
            phone TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_user1(tg_id: int):
    conn=sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
    user = cursor.fetchone()
    conn.close()
    return user 
    

def add_user(tg_id, username, full_name, age, sat_score, phone):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO users (tg_id, username, full_name, age, sat_score, phone)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (tg_id, username, full_name, age, sat_score, phone))
    conn.commit()
    conn.close()

def get_fulluserdata(tg_id: int):
    conn= sqlite3.connect(DB_NAME)
    cursor=conn.cursor()
    cursor.execute("SELECT tg_id, username, full_name, age, sat_score, phone FROM users WHERE tg_id=?",(tg_id,))
    row = cursor.fetchone()
    conn.close
    if row:
        return{
            "tg_id": row[0],
            "username": row[1],
            "full_name": row[2],
            "age": row[3],
            "sat_score": row[4],
            "phone": row[5]
        }
    return None

