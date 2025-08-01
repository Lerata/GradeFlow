import streamlit as st
from typing import Optional, Dict
from utils.database import get_user_by_username
from utils.crypto import hash_password

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authenticate user with username and password"""
    if not username or not password:
        return None
    
    user = get_user_by_username(username)
    if user and user['password_hash'] == hash_password(password):
        return {
            'id': user['id'],
            'username': user['username'],
            'name': user['name'],
            'email': user['email'],
            'role': user['role']
        }
    return None

def get_current_user() -> Optional[Dict]:
    """Get current authenticated user"""
    if st.session_state.get('authenticated') and st.session_state.get('user'):
        return st.session_state.user
    return None

def logout_user():
    """Logout current user"""
    st.session_state.authenticated = False
    st.session_state.user = None
    st.session_state.current_page = "login"

def require_auth(role: Optional[str] = None):
    """Decorator to require authentication and optionally specific role"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user:
                st.error("Authentication required")
                return None
            
            if role and user['role'] != role:
                st.error(f"Access denied. Required role: {role}")
                return None
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def has_permission(user: Dict, permission: str) -> bool:
    """Check if user has specific permission"""
    role_permissions = {
        'admin': ['all'],
        'teacher': ['grade', 'review', 'upload'],
        'student': ['view_results']
    }
    
    user_permissions = role_permissions.get(user['role'], [])
    return 'all' in user_permissions or permission in user_permissions
