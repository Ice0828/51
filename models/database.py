import sqlite3
import os
from config import Config

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库"""
    # 确保数据库目录存在
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        address TEXT,
        nationality TEXT,
        native_language TEXT
    )
    ''')
    
    # 创建用户音色表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_voices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        voice_uri TEXT NOT NULL,
        voice_name TEXT NOT NULL,
        custom_name TEXT NOT NULL,
        voice_description TEXT,
        create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    ''')
    
    # 创建用户活动记录表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        activity_type TEXT NOT NULL,
        description TEXT,
        create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    ''')
    
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_voices_user_id ON user_voices (user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_activities_user_id ON user_activities (user_id)')
    
    conn.commit()
    conn.close() 