# config.py - 全局配置

import streamlit as st

# 数据库配置
DB_PATH = "users.db"

# 默认管理员账号
DEFAULT_ADMIN = {
    "username": "admin",
    "password": "admin123",
    "name": "系统管理员",
    "email": "admin@tcm.com",
    "role": "admin"
}

# 本能论系统配置
INSTINCT_SYSTEMS = [
    "排异本能系统",
    "自主调节系统", 
    "自塑本能系统",
    "自我修复系统",
    "自我更新系统",
    "应变系统",
    "共生性本能系统"
]

# API配置（从secrets读取）
def get_api_keys():
    return {
        "neo4j_uri": st.secrets.get("NEO4J_URI"),
        "neo4j_user": st.secrets.get("NEO4J_USER"),
        "neo4j_password": st.secrets.get("NEO4J_PASSWORD"),
        "zhipuai_key": st.secrets.get("API_KEY"),
        "dashscope_key": st.secrets.get("DASHSCOPE_API_KEY")
    }
