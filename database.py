# database.py - 完整修复版

import sqlite3
import bcrypt
from neo4j import GraphDatabase
import streamlit as st

DB_PATH = "users.db"

# Neo4j 连接配置（从 secrets 读取）
def get_neo4j_config():
    """获取Neo4j配置"""
    return {
        "uri": st.secrets.get("NEO4J_URI", "bolt://localhost:7687"),
        "user": st.secrets.get("NEO4J_USER", "neo4j"),
        "password": st.secrets.get("NEO4J_PASSWORD", "")
    }

# 全局连接缓存
_neo4j_driver = None

def init_connections():
    """
    初始化所有连接（Neo4j + 智谱AI）
    返回: (neo4j_driver, zhipuai_client)
    """
    global _neo4j_driver
    
    # 初始化 Neo4j
    if _neo4j_driver is None:
        config = get_neo4j_config()
        _neo4j_driver = GraphDatabase.driver(
            config["uri"], 
            auth=(config["user"], config["password"])
        )
    
    # 初始化智谱AI
    try:
        from zhipuai import ZhipuAI
        api_key = st.secrets.get("API_KEY", "")
        zhipu_client = ZhipuAI(api_key=api_key) if api_key else None
    except:
        zhipu_client = None
    
    return _neo4j_driver, zhipu_client

def get_neo4j_driver():
    """获取Neo4j驱动（用于查询）"""
    global _neo4j_driver
    if _neo4j_driver is None:
        init_connections()
    return _neo4j_driver

def close_connections():
    """关闭所有连接"""
    global _neo4j_driver
    if _neo4j_driver:
        _neo4j_driver.close()
        _neo4j_driver = None

# ========== SQLite 用户数据库操作 ==========

def init_database():
    """初始化数据库，创建用户表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
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
    
    conn.commit()
    
    # 创建默认管理员账号
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        create_user('admin', 'admin123', '管理员', 'admin@tcm.com', 'admin')
        print("默认管理员已创建：用户名 admin，密码 admin123")
    
    conn.close()

def create_user(username, password, name, email='', role='user'):
    """创建新用户"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
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
        return False, "用户名已存在"

def verify_login(username, password):
    """验证用户登录"""
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
    """获取所有用户列表"""
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

def user_exists(username):
    """检查用户名是否存在"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT 1 FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    return result is not None
