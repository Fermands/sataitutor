import sqlite3
from datetime import datetime, timedelta
DB_NAME = "vocab.db"

def vocab_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vocab_users (
            user_id INTEGER PRIMARY KEY,
            time TEXT,
            current_day INTEGER DEFAULT 1,
            progress INTEGER DEFAULT 0,
            next_reminder TEXT
        )
    """)
    conn.commit()
    conn.close()

from datetime import datetime, timedelta

def change_user_time(user_id, time_str):
    from datetime import datetime, timedelta
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Get current day and progress
    c.execute("SELECT current_day, progress FROM vocab_users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if not row:
        # If user doesn't exist, create default
        current_day = 1
        progress = 0
    else:
        current_day, progress = row

    # Compute next reminder datetime
    hour, minute = map(int, time_str.split(":"))
    now = datetime.now()
    next_reminder = datetime.combine(now.date(), datetime.min.time()) + timedelta(hours=hour, minutes=minute)
    if next_reminder <= now:
        next_reminder += timedelta(days=1)

    # Update DB without resetting day
    c.execute("""
        UPDATE vocab_users 
        SET time=?, next_reminder=? 
        WHERE user_id=?
    """, (time_str, next_reminder.isoformat(), user_id))
    conn.commit()
    conn.close()



def save_user_time(user_id, time_str, day=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # compute next reminder datetime
    hour, minute = map(int, time_str.split(":"))
    now = datetime.now()
    next_reminder = datetime.combine(now.date(), datetime.min.time()) + timedelta(hours=hour, minutes=minute)
    if next_reminder <= now:
        next_reminder += timedelta(days=1)  # schedule for tomorrow
    
    # if day is provided, update current_day; else keep existing
    if day:
        c.execute("""
            INSERT INTO vocab_users (user_id, time, current_day, progress, next_reminder)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                time=excluded.time,
                current_day=excluded.current_day,
                next_reminder=excluded.next_reminder
        """, (user_id, time_str, day, 0, next_reminder.isoformat()))
    else:
        c.execute("""
            INSERT INTO vocab_users (user_id, time, current_day, progress, next_reminder)
            VALUES (?, ?, 1, 0, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                time=excluded.time,
                next_reminder=excluded.next_reminder
        """, (user_id, time_str, next_reminder.isoformat()))
    
    conn.commit()
    conn.close()


def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT time, current_day, progress, next_reminder FROM vocab_users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row if row else None
def get_user11(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Only select the columns you need
    c.execute("SELECT time, current_day, progress FROM vocab_users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row if row else None

def update_progress(user_id, progress):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE vocab_users SET progress=? WHERE user_id=?", (progress, user_id))
    conn.commit()
    conn.close()

def reset_day(user_id, new_day):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE vocab_users SET current_day=?, progress=0 WHERE user_id=?", (new_day, user_id))
    conn.commit()
    conn.close()
