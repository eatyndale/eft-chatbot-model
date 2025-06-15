import os
import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI
import time
import sqlite3

# Set environment variable to avoid BERT parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Import modules
from modules.animation_trigger import detect_animation, TAPPING_POINTS
from modules.screening import create_screening_interface, get_screening_status, reset_screening
from modules.database import ensure_db_exists, setup_database
from modules.auth import create_auth_interface
from modules.session_tracker import SessionTracker
from modules.personalisation import build_personalised_prompt

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_NAME = "ft:gpt-3.5-turbo-0125:university-of-bolton:eft-therapist-v1:BRjhRNWc"  # Replace with your fine-tuned model name

def verify_all_tables():
    """Verify all required tables exist and create them if needed"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"Existing tables: {existing_tables}")
        
        # Create any missing tables WITHOUT trying to recreate existing ones
        if 'users' not in existing_tables:
            print("Creating missing 'users' table...")
            cursor.execute('''
            CREATE TABLE users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE,
                password_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
        
        if 'consent' not in existing_tables:
            print("Creating missing 'consent' table...")
            cursor.execute('''
            CREATE TABLE consent (
                consent_id TEXT PRIMARY KEY,
                user_id TEXT,
                consented_at TIMESTAMP,
                consent_version TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            ''')
            
        if 'assessments' not in existing_tables:
            print("Creating missing 'assessments' table...")
            cursor.execute('''
            CREATE TABLE assessments (
                assessment_id TEXT PRIMARY KEY,
                user_id TEXT,
                completed_at TIMESTAMP,
                gad7_score INTEGER,
                phq9_score INTEGER,
                is_high_risk BOOLEAN,
                has_suicide_risk BOOLEAN,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            ''')
            
        if 'sessions' not in existing_tables:
            print("Creating missing 'sessions' table...")
            cursor.execute('''
            CREATE TABLE sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            ''')
        
        if 'messages' not in existing_tables:
            print("Creating missing 'messages' table...")
            cursor.execute('''
            CREATE TABLE messages (
                message_id TEXT PRIMARY KEY,
                session_id TEXT,
                timestamp TIMESTAMP,
                sender TEXT,
                content TEXT,
                emotion TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
            ''')
        
        if 'tapping_steps' not in existing_tables:
            print("Creating missing 'tapping_steps' table...")
            cursor.execute('''
            CREATE TABLE tapping_steps (
                step_id TEXT PRIMARY KEY,
                session_id TEXT,
                step_number INTEGER,
                step_content TEXT,
                completed BOOLEAN DEFAULT 0,
                completed_at TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (session_id)
            )
            ''')
        
        conn.commit()
        conn.close()
        print("Database tables verified successfully")
    except Exception as e:
        print(f"Error verifying database tables: {e}")
        try:
            conn.close()
        except:
            pass

def initialize_app():
    """Initialize the application and make sure all components are ready"""
    # Just verify database tables without trying to recreate them
    print("Verifying database...")
    verify_all_tables()  # Don't call setup_database() directly
    
    # Print all tapping point files
    print("Verifying tapping point animations...")
    for point, path in TAPPING_POINTS.items():
        print(f"Tapping point '{point}' file exists: {os.path.exists(path)}")
    
    # Print all tapping point files
    print("Verifying tapping point animations...")
    for point, path in TAPPING_POINTS.items():
        print(f"Tapping point '{point}' file exists: {os.path.exists(path)}")

# Initialize the app
initialize_app()

# Initialize session tracker
session_tracker = SessionTracker()

# Global session variables
current_tapping_steps = []
current_step_index = 0
awaiting_tapping_steps = False
current_user_id = None

# Improved tapping detection function
def split_tapping_instructions(text):
    """
    Detects tapping instructions in the text and returns a list of formatted tapping steps
    """
    # Check for bullet points or numbered lists with tapping points
    tapping_points = ["karate chop", "top of head", "eyebrow", "side of eye", "under eye", 
                     "under nose", "chin", "collarbone", "under arm"]
    
    steps = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        # Skip empty lines
        if not line:
            continue
            
        # Check if line contains a tapping point
        for point in tapping_points:
            if point in line.lower():
                # Clean up the line - remove bullets, numbers, etc.
                clean_line = line
                # Remove bullet points, asterisks, or numbers at the beginning
                for prefix in ['•', '*', '-', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.']:
                    if clean_line.startswith(prefix):
                        clean_line = clean_line[len(prefix):].strip()
                
                # Create proper tapping point format if needed
                if not point.lower() in clean_line.lower()[:20]:
                    # Point mentioned but not in expected format, reformat it
                    if ":" in clean_line:
                        reminder_phrase = clean_line.split(":", 1)[1].strip()
                    else:
                        reminder_phrase = clean_line
                    steps.append(f"{point.title()}: {reminder_phrase}")
                else:
                    # Already in good format
                    steps.append(clean_line)
                
                break
    
    return steps

# Function to check for suicide mentions in user message
def contains_suicide_risk(message):
    suicide_terms = [
        "suicide", "kill myself", "end my life", "take my life",
        "don't want to live", "want to die", "end it all",
        "no reason to live", "better off dead"
    ]
    message_lower = message.lower()
    return any(term in message_lower for term in suicide_terms)

# Improved generate_response function
def generate_response(user_message):
    global awaiting_tapping_steps, current_step_index, current_tapping_steps
    
    # Check for suicide risk in user message
    if contains_suicide_risk(user_message):
        crisis_message = "I notice you're mentioning thoughts of harm. This is serious and I want to make sure you get the right support. Please contact emergency services by calling 999, or call the Samaritans at 116 123 (free, 24/7). You can also text SHOUT to 85258. Your wellbeing matters, and professionals are ready to help you through this difficult time."
        
        # Log the interaction with the session tracker
        session_tracker.record_message("user", user_message)
        session_tracker.record_message("assistant", crisis_message)
        
        return crisis_message
    
    # Record user message
    session_tracker.record_message("user", user_message)
    
    # Get basic prompt with just username
    messages = build_personalised_prompt(
        current_user_id, 
        session_tracker.get_chat_session()
    )
    
    # Add the current user message
    if messages and messages[-1]["role"] != "user":
        messages.append({"role": "user", "content": user_message})
    
    # Get response from model
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.7
        )

        assistant_reply = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error getting model response: {e}")
        assistant_reply = "I'm having trouble connecting to my systems. Please try again in a moment."
    
    # Record assistant message
    session_tracker.record_message("assistant", assistant_reply)

    # Check for tapping sequence markers
    has_tapping_indicators = (
        "tapping through the points" in assistant_reply.lower() or
        "tapping sequence" in assistant_reply.lower() or
        "tap through each point" in assistant_reply.lower() or
        ("karate chop" in assistant_reply.lower() and any(point in assistant_reply.lower() for point in ["top of head", "eyebrow", "collarbone"]))
    )
    
    # If message appears to have a tapping sequence, extract the tapping points
    if has_tapping_indicators:
        tapping_steps = split_tapping_instructions(assistant_reply)
        
        # Check if we have enough tapping steps for a sequence
        if len(tapping_steps) >= 3:
            # Save original reply for use in creating a more natural introduction
            original_text_parts = assistant_reply.split('\n')
            intro_text = ""
            
            # Extract any text before the tapping sequence as an intro
            for line in original_text_parts:
                if not any(point in line.lower() for point in ["karate chop", "top of head", "eyebrow", 
                                                             "side of eye", "under eye", "under nose", 
                                                             "chin", "collarbone", "under arm"]):
                    intro_text += line + "\n"
                else:
                    break
            
            intro_text = intro_text.strip()
            if not intro_text:
                intro_text = "Let's begin tapping through the points."
                
            # Set up the tapping sequence
            current_tapping_steps = tapping_steps
            current_step_index = 0
            awaiting_tapping_steps = True
            
            # Record the sequence
            session_tracker.record_tapping_sequence(tapping_steps)
            
            # Return just the intro text, we'll show tapping steps one by one
            return f"{intro_text}\n\nClick 'Next' to continue through each tapping point."
            
    # If no tapping sequence detected or not enough steps, return the original reply
    return assistant_reply

# Updated next_tapping_step function
def next_tapping_step(chatbot_value):
    global current_step_index, current_tapping_steps, awaiting_tapping_steps
    
    # Keep existing chat history - handling both formats
    updated_history = []
    if chatbot_value:
        # Convert any tuple format to message format if needed
        for item in chatbot_value:
            if isinstance(item, list) or isinstance(item, tuple):
                user_msg = {"role": "user", "content": item[0]} if item[0] else None
                assistant_msg = {"role": "assistant", "content": item[1]} if item[1] else None
                if user_msg:
                    updated_history.append(user_msg)
                if assistant_msg:
                    updated_history.append(assistant_msg)
            else:
                updated_history.append(item)

    if not current_tapping_steps or current_step_index >= len(current_tapping_steps):
        # No tapping steps or we've reached the end
        awaiting_tapping_steps = False
        current_tapping_steps = []
        current_step_index = 0
        
        # Add completion message
        completion_message = "Tapping session complete. How are you feeling now on a scale of 0-10?"
        updated_history.append({"role": "assistant", "content": completion_message})
        
        # Record completion message
        session_tracker.record_message("assistant", completion_message)
        
        return updated_history, None, gr.update(visible=False)
    
    # We have more steps
    step = current_tapping_steps[current_step_index]
    
    # Record step completion
    session_tracker.record_tapping_step_completion(current_step_index)
    
    current_step_index += 1
    image_path = detect_animation(step)
    
    # Add this step to the chat history
    updated_history.append({"role": "assistant", "content": step})
    
    # Return updated chat history and image
    return updated_history, image_path, gr.update(visible=True if image_path else False)

# Reset everything
def reset_chat():
    global current_tapping_steps, current_step_index, awaiting_tapping_steps
    
    # End current session if active
    if session_tracker.is_active():
        session_tracker.end_current_session()
    
    # Start new session
    if current_user_id:
        session_tracker.start_session(current_user_id)
    
    # Reset tapping variables
    current_tapping_steps = []
    current_step_index = 0
    awaiting_tapping_steps = False
    
    return [], "", gr.update(visible=False)

# Handle user sending message
def handle_user_message(user_message, chatbot_value):
    global current_tapping_steps, current_step_index, awaiting_tapping_steps
    
    # Check for empty messages
    if not user_message or user_message.strip() == "":
        return chatbot_value, "", gr.update(visible=False)
    
    # Check for explicit tapping requests
    tapping_phrases = ["let's tap", "another round", "start tapping", "do tapping", 
                      "let's go again", "tap", "tapping"]
    is_tapping_request = any(phrase in user_message.lower() for phrase in tapping_phrases)
    
    # Make sure we have an active session
    if not session_tracker.is_active() and current_user_id:
        session_tracker.start_session(current_user_id)
    
    # Record the user message
    session_tracker.record_message("user", user_message)
    
    # Keep existing chat history - convert to message format
    updated_history = []
    if chatbot_value:
        # Handle different formats and convert to message format
        for item in chatbot_value:
            if isinstance(item, list) or isinstance(item, tuple):
                user_msg = {"role": "user", "content": item[0]} if item[0] else None
                assistant_msg = {"role": "assistant", "content": item[1]} if item[1] else None
                if user_msg:
                    updated_history.append(user_msg)
                if assistant_msg:
                    updated_history.append(assistant_msg)
            else:
                updated_history.append(item)
    
    # Add new user message
    updated_history.append({"role": "user", "content": user_message})
    
    # If it's a direct tapping request, trigger tapping sequence
    if is_tapping_request:
        # Default tapping sequence with karate chop included
        default_tapping_steps = [
            "Karate chop: 'Even though I'm feeling anxious right now, I deeply and completely accept myself.'",
            "Top of head: 'This anxiety I'm feeling.'",
            "Eyebrow: 'It's overwhelming right now.'",
            "Side of eye: 'I acknowledge this fear.'",
            "Under eye: 'All this worry and stress.'",
            "Under nose: 'The tension in my body.'",
            "Chin: 'Feeling anxious about everything.'",
            "Collarbone: 'All this pressure I'm feeling.'",
            "Under arm: 'This anxiety in my body.'"
        ]
        
        # Add acknowledgment message
        tapping_response = "Let's begin a new tapping sequence. Click 'Next' to continue through each tapping point."
        updated_history.append({"role": "assistant", "content": tapping_response})
        
        # Record the bot's response
        session_tracker.record_message("assistant", tapping_response)
        
        # Set up tapping sequence
        current_tapping_steps = default_tapping_steps
        current_step_index = 0
        awaiting_tapping_steps = True
        
        # Store sequence in database
        session_tracker.record_tapping_sequence(default_tapping_steps)
        
        return updated_history, "", gr.update(visible=False)
    else:
        # Otherwise, proceed with normal response
        bot_reply = generate_response(user_message)
        
        # Add bot response to history
        updated_history.append({"role": "assistant", "content": bot_reply})
        
        return updated_history, "", gr.update(visible=False)

# Gradio UI
with gr.Blocks(css="footer {visibility: hidden}") as demo:
    gr.Markdown("# 🌿 Your EFT Chatbot")
    
    # Create shared state for user ID
    user_id_state = gr.State(None)
    
    # Authentication container
    with gr.Group(visible=True) as auth_container:
        auth_interface, auth_user_id, auth_message = create_auth_interface()
    
    # Screening container - initially hidden
    with gr.Group(visible=False) as screening_container:
        screening_components = create_screening_interface()
        
        # Share the user_id with the screening interface
        def update_screening_user_id(user_id):
            return user_id
        
        # Connect user_id to screening components
        user_id_state.change(
            update_screening_user_id,
            inputs=[user_id_state],
            outputs=[screening_components["user_id_state"]]
        )
    
    # Chatbot container - initially hidden
    with gr.Group(visible=False) as chatbot_container:
        # Main UI components
        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(label="Sarah", height=600, type="messages")
                user_input = gr.Textbox(placeholder="Type your message...", scale=8)
                
                with gr.Row():
                    send_btn = gr.Button("Send", variant="primary")
                    next_btn = gr.Button("Next Step", visible=True)
                    reset_btn = gr.Button("Reset Chat")
                    logout_btn = gr.Button("Logout", variant="secondary")
                    
            # Dedicated column for tapping images
            with gr.Column(scale=1, visible=False) as image_column:
                tapping_image = gr.Image(label="Tapping Point", show_label=True, height=300)

        # Connect UI components to functions
        send_btn.click(
            handle_user_message, 
            inputs=[user_input, chatbot], 
            outputs=[chatbot, user_input, image_column]
        )
        
        user_input.submit(
            handle_user_message, 
            inputs=[user_input, chatbot], 
            outputs=[chatbot, user_input, image_column]
        )
        
        next_btn.click(
            next_tapping_step, 
            inputs=[chatbot], 
            outputs=[chatbot, tapping_image, image_column]
        )
        
        reset_btn.click(
            reset_chat, 
            inputs=[], 
            outputs=[chatbot, user_input, image_column]
        )
        
    # Function to show screening after login
    def show_screening_after_login(auth_user_id_value, auth_message_value):
        global current_user_id
        
        if auth_user_id_value:
            current_user_id = auth_user_id_value
            # Start a new session for this user
            session_tracker.start_session(auth_user_id_value)
            print(f"User {auth_user_id_value} logged in successfully")
            
            return {
                auth_container: gr.update(visible=False),
                screening_container: gr.update(visible=True),
                user_id_state: auth_user_id_value
            }
            
        return {
            auth_container: gr.update(visible=True),
            screening_container: gr.update(visible=False),
            user_id_state: None
        }
    
    # Function to show chatbot after screening
    def show_chatbot_after_screening(user_id_value):
        screening_status = get_screening_status()
        
        if screening_status["eligible"] and screening_status["completed"]:
            # Clear any existing chat history before starting
            reset_chat()
            
            return {
                screening_container: gr.update(visible=False),
                chatbot_container: gr.update(visible=True)
            }
        else:
            # Stay on the current screening page
            return {}
    
    # Function to handle logout
    def handle_logout():
        global current_user_id
        
        # End current session if active
        if session_tracker.is_active():
            session_tracker.end_current_session()
        
        current_user_id = None
        
        return {
            chatbot_container: gr.update(visible=False),
            auth_container: gr.update(visible=True)
        }
    
    # Connect authentication to screening
    auth_user_id.change(
        show_screening_after_login,
        inputs=[auth_user_id, auth_message],
        outputs=[auth_container, screening_container, user_id_state]
    )
    
    # Connect screening to chatbot
    screening_components["continue_btn_output"].then(
        show_chatbot_after_screening,
        inputs=[user_id_state],
        outputs=[screening_container, chatbot_container]
    )
    
    if "skip_btn_output" in screening_components:
        screening_components["skip_btn_output"].then(
            show_chatbot_after_screening,
            inputs=[user_id_state],
            outputs=[screening_container, chatbot_container]
        )
    
    # Connect logout button
    logout_btn.click(
        handle_logout,
        inputs=[],
        outputs=[chatbot_container, auth_container]
    )

# Launch the app
if __name__ == "__main__":
    demo.launch(share=True)