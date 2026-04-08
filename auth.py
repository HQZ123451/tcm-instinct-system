# auth.py - 登录认证逻辑

import streamlit as st
from database import verify_login, update_last_login

def login(username, password):
    """
    登录用户，设置session状态
    """
    success, user_info = verify_login(username, password)
    
    if success and user_info:
        # 设置登录状态
        st.session_state['authenticated'] = True
        st.session_state['user_id'] = user_info['id']
        st.session_state['username'] = user_info['username']
        st.session_state['name'] = user_info['name']
        st.session_state['email'] = user_info['email']
        st.session_state['role'] = user_info['role']
        
        # 更新最后登录时间
        update_last_login(user_info['id'])
        
        return True
    return False

def logout():
    """退出登录"""
    keys_to_clear = ['authenticated', 'user_id', 'username', 'name', 'email', 'role', 'show_admin']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

def is_logged_in():
    """检查是否已登录"""
    return st.session_state.get('authenticated', False)

def is_admin():
    """检查是否是管理员"""
    return st.session_state.get('role') == 'admin'

def get_current_user():
    """获取当前用户信息"""
    if is_logged_in():
        return {
            'id': st.session_state.get('user_id'),
            'username': st.session_state.get('username'),
            'name': st.session_state.get('name'),
            'email': st.session_state.get('email'),
            'role': st.session_state.get('role')
        }
    return None
