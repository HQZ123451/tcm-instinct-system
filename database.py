# database.py - SQLite数据库操作

import sqlite3
import bcrypt
import os
from config import DB_PATH, DEFAULT_ADMIN

def init_database():
    """初始化数据库，创建用户表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    )
    ''')
    
    # 创建分析历史表（可选）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS analysis_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        image_features TEXT,
        instinct_systems TEXT,
        recommended_prescriptions TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    
    # 检查是否已有管理员，没有则创建默认管理员
    cursor.execute("SELECT * FROM users WHERE username = ?", (DEFAULT_ADMIN["username"],))
    if not cursor.fetchone():
        create_user(
            username=DEFAULT_ADMIN["username"],
            password=DEFAULT_ADMIN["password"],
            name=DEFAULT_ADMIN["name"],
            email=DEFAULT_ADMIN["email"],
            role=DEFAULT_ADMIN["role"]
        )
        print(f"✅ 默认管理员已创建：用户名 {DEFAULT_ADMIN['username']}，密码 {DEFAULT_ADMIN['password']}")
    
    conn.close()

def create_user(username, password, name, email='', role='user'):
    """
    创建新用户
    返回: (success: bool, message: str)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 密码加密
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    try:
        cursor.execute('''
        INSERT INTO users (username, password_hash, name, email, role)
        VALUES (?, ?, ?, ?, ?)
        ''', (username, password_hash, name, email, role))
        conn.commit()
        conn.close()
        return True, "注册成功！请返回登录"
    except sqlite3.IntegrityError:
        conn.close()
        return False, "用户名已存在，请更换"

def verify_login(username, password):
    """
    验证登录
    返回: (success: bool, user_info: dict or None)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, username, name, email, role, password_hash 
    FROM users WHERE username = ?
    ''', (username,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        user_id, username, name, email, role, password_hash = result
        if bcrypt.checkpw(password.encode('utf-8'), password_hash):
            return True, {
                "id": user_id,
                "username": username,
                "name": name,
                "email": email,
                "role": role
            }
    
    return False, None

def get_all_users():
    """获取所有用户列表（管理员用）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT id, username, name, email, role, created_at, last_login 
    FROM users ORDER BY created_at DESC
    ''')
    
    users = cursor.fetchall()
    conn.close()
    return users

def delete_user(user_id):
    """删除用户"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return True

def update_user_role(user_id, new_role):
    """修改用户角色"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, user_id))
    conn.commit()
    conn.close()
    return True

def update_last_login(user_id):
    """更新最后登录时间"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

def check_username_exists(username):
    """检查用户名是否存在"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT 1 FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    return result is not None
