#!/usr/bin/env python3
"""Database migration script to add missing status column"""

import sqlite3
import os

db_path = r'c:\Users\PROGRESS\Desktop\tradingbot\instance\trading_bot.db'

if not os.path.exists(db_path):
    print("Database does not exist yet - nothing to migrate")
    exit(0)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if status column exists in transaction table
    cursor.execute('PRAGMA table_info("transaction")')
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'status' not in columns:
        print("Adding 'status' column to transaction table...")
        cursor.execute('ALTER TABLE "transaction" ADD COLUMN status VARCHAR(20) DEFAULT "completed"')
        conn.commit()
        print("Migration complete for transaction table!")
    else:
        print("Database schema is already up to date")
    
    # Check trade table
    cursor.execute('PRAGMA table_info("trade")')
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'status' not in columns:
        print("Adding 'status' column to trade table...")
        cursor.execute('ALTER TABLE "trade" ADD COLUMN status VARCHAR(20) DEFAULT "completed"')
        conn.commit()
        print("Trade table updated!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Migration failed: {e}")
    exit(1)
