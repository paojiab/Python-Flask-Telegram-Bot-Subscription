import sqlite3
from datetime import datetime, timedelta

from flutterwave import generate_payment_reference

from telegram.ext import (
    ContextTypes,
)

from keys import CHANNEL_CHAT_ID

DATABASE_FILE = 'subscriptions.db'

plans = ["month","quarter","half"]

def create_database():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id INTEGER PRIMARY KEY,
            product TEXT,
            payment_method TEXT,
            currency TEXT,
            plan TEXT,
            subscription_start TEXT,
            subscription_end TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_tokens_database():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            user_id INTEGER PRIMARY KEY,
            token TEXT
        )
    ''')
    conn.commit()
    conn.close()

async def add_subscription(user_id, plan):
    product = "signals"
    payment_method = "selar"
    currency = "USD"
    raw_subscription_start = datetime.now()
    raw_subscription_end = raw_subscription_start + timedelta(days=30)
    if(plan == "quarter"):
        raw_subscription_end = raw_subscription_start + timedelta(days=30*3)
    elif(plan == "half"):
        raw_subscription_end = raw_subscription_start + timedelta(days=30*6)
    subscription_start = raw_subscription_start.isoformat()
    subscription_end = raw_subscription_end.isoformat()
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO subscriptions VALUES (?, ?, ?, ?, ?, ?, ?)", (user_id, product, payment_method, currency, plan, subscription_start, subscription_end))
    conn.commit()
    conn.close()

async def check_subscription(user_id):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM subscriptions WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

async def secure(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    user_id = job.user_id
    security_token = job.data
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO tokens VALUES (?, ?)", (user_id, security_token))
    conn.commit()
    conn.close()

async def check_token(user_id):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tokens WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

async def check_raw_token(token):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tokens WHERE token = ?", (token,))
    result = cursor.fetchone()
    conn.close()
    return result

async def wipe_token(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    token = job.data
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tokens WHERE token = ?", (token,))
    conn.commit()
    conn.close()

async def remove_subscription(context: ContextTypes.DEFAULT_TYPE) -> None:
    
    job = context.job
    user_id = job.user_id

    await context.bot.ban_chat_member(chat_id=CHANNEL_CHAT_ID,user_id=user_id)

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM subscriptions WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
