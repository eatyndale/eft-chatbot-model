"""
Authentication module for EFT Chatbot
Handles user registration, login, and session management
"""

import hashlib
import uuid
import sqlite3
import gradio as gr
from modules.database import DB_PATH

def hash_password(password):
    """Create a secure hash of a password"""
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    """Register a new user"""
    if not username or not password:
        return {"success": False, "message": "Username and password are required"}
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if username exists
    cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return {"success": False, "message": "Username already exists"}
    
    # Create new user
    user_id = str(uuid.uuid4())
    password_hash = hash_password(password)
    
    cursor.execute(
        "INSERT INTO users (user_id, username, password_hash) VALUES (?, ?, ?)",
        (user_id, username, password_hash)
    )
    
    conn.commit()
    conn.close()
    
    return {"success": True, "user_id": user_id, "message": "Registration successful"}

def login_user(username, password):
    """Authenticate a user"""
    if not username or not password:
        return {"success": False, "message": "Username and password are required"}
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT user_id, password_hash FROM users WHERE username = ?", 
        (username,)
    )
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return {"success": False, "message": "Invalid username or password"}
    
    user_id, stored_hash = result
    
    if hash_password(password) != stored_hash:
        conn.close()
        return {"success": False, "message": "Invalid username or password"}
    
    conn.close()
    return {"success": True, "user_id": user_id, "message": "Login successful"}

def get_username(user_id):
    """Get username from user_id"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT username FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        return result[0]
    return None

def create_auth_interface():
    """Create login/registration interface with Gradio"""
    # Create state for storing user ID
    user_id_state = gr.State(None)
    login_message_state = gr.State("")
    
    with gr.Blocks() as auth_block:
        gr.Markdown("# Welcome to the EFT Chatbot")
        gr.Markdown("Please login or register to continue")
        
        with gr.Tab("Login"):
            login_username = gr.Textbox(label="Username")
            login_password = gr.Textbox(label="Password", type="password")
            login_btn = gr.Button("Login", variant="primary")
            login_message = gr.Markdown("")
        
        with gr.Tab("Register"):
            reg_username = gr.Textbox(label="Create Username")
            reg_password = gr.Textbox(label="Create Password", type="password")
            reg_confirm = gr.Textbox(label="Confirm Password", type="password")
            reg_btn = gr.Button("Register", variant="primary")
            reg_message = gr.Markdown("")
        
        # Handle login
        def handle_login(username, password):
            result = login_user(username, password)
            if result["success"]:
                return gr.update(value=f"✅ {result['message']}"), result["user_id"], result["message"]
            else:
                return gr.update(value=f"❌ {result['message']}"), None, ""
        
        # Handle registration
        def handle_registration(username, password, confirm):
            if password != confirm:
                return gr.update(value="❌ Passwords do not match")
            
            result = register_user(username, password)
            if result["success"]:
                return gr.update(value=f"✅ {result['message']}. Please go to the Login tab.")
            else:
                return gr.update(value=f"❌ {result['message']}")
        
        # Connect buttons
        login_btn.click(
            handle_login, 
            inputs=[login_username, login_password], 
            outputs=[login_message, user_id_state, login_message_state]
        )
        
        reg_btn.click(
            handle_registration,
            inputs=[reg_username, reg_password, reg_confirm],
            outputs=[reg_message]
        )
    
    return auth_block, user_id_state, login_message_state