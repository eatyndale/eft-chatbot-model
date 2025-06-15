"""
Session Tracker module for EFT Chatbot
Manages current user session state and tracks interactions
"""

import datetime
import os
from modules.database import (
    create_session, 
    end_session, 
    store_message, 
    store_tapping_sequence,
    mark_tapping_step_completed
)
from modules.emotion_analysis import EmotionAnalyzer, detect_emotion_keywords

class SessionTracker:
    """Class for tracking therapy session data"""
    
    def __init__(self):
        self.current_user_id = None
        self.current_session_id = None
        self.is_session_active = False
        self.chat_session = []
        self.emotion_analyzer = None
        
        # Try to initialize emotion analyzer
        try:
            self.emotion_analyzer = EmotionAnalyzer()
        except Exception as e:
            print(f"Error initializing emotion analyzer: {e}")
            print("Will use keyword-based fallback for emotion detection")
    
    def start_session(self, user_id):
        """Start a new therapy session for user"""
        if self.is_session_active:
            self.end_current_session()
        
        self.current_user_id = user_id
        self.current_session_id = create_session(user_id)
        self.is_session_active = True
        self.chat_session = []
        
        print(f"Started new session {self.current_session_id} for user {self.current_user_id}")
        return self.current_session_id
    
    def end_current_session(self):
        """End the current therapy session"""
        if not self.is_session_active:
            return
        
        end_session(self.current_session_id)
        self.is_session_active = False
        
        print(f"Ended session {self.current_session_id} for user {self.current_user_id}")
    
    def record_message(self, sender, content):
        """
        Record a message in the current session
        
        Args:
            sender: 'user' or 'assistant'
            content: Message content
        """
        if not self.is_session_active:
            print("Warning: Trying to record message but no active session")
            return
        
        # Detect emotion for user messages
        emotion = None
        if sender == "user" and content:
            if self.emotion_analyzer and self.emotion_analyzer.is_initialized:
                emotion = self.emotion_analyzer.detect_emotion(content)
            else:
                emotion = detect_emotion_keywords(content)
        
        # Store in database
        store_message(self.current_session_id, sender, content, emotion)
        
        # Update chat session for context
        self.chat_session.append({"role": sender, "content": content})
        
        return emotion
    
    def record_tapping_sequence(self, tapping_steps):
        """
        Record a tapping sequence in the current session
        
        Args:
            tapping_steps: List of tapping step instructions
        """
        if not self.is_session_active or not tapping_steps:
            return
        
        store_tapping_sequence(self.current_session_id, tapping_steps)
    
    def record_tapping_step_completion(self, step_index):
        """
        Record completion of a tapping step
        
        Args:
            step_index: Index of the completed step
        """
        if not self.is_session_active:
            return
        
        mark_tapping_step_completed(self.current_session_id, step_index)
    
    def get_chat_session(self):
        """Get current chat session for the OpenAI API"""
        return self.chat_session
    
    def clear_chat_session(self):
        """Clear the current chat session"""
        self.chat_session = []
    
    def is_active(self):
        """Check if a session is currently active"""
        return self.is_session_active
    
    def get_current_user_id(self):
        """Get the current user ID"""
        return self.current_user_id
    
    def get_current_session_id(self):
        """Get the current session ID"""
        return self.current_session_id