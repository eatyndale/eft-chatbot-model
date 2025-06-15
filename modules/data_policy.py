"""
Data and Ethics Policy Module for EFT Chatbot

This module provides functions for managing user data ethically:
- Data retention policies
- Data anonymization functions
- Data export/deletion capabilities
"""

import os
import json
import shutil
import datetime
from pathlib import Path
import pandas as pd

def anonymize_data_for_research(data_dir="session_data", output_file="anonymized_research_data.csv"):
    """
    Processes session data into anonymized format suitable for research
    
    Args:
        data_dir: Directory containing session data files
        output_file: Filename for the output CSV
    
    Returns:
        Path to the created CSV file
    """
    # List all session files
    session_files = list(Path(data_dir).glob("session_*.json"))
    
    if not session_files:
        return None
    
    # Process files into a list of dictionaries
    processed_data = []
    
    for file_path in session_files:
        try:
            with open(file_path, 'r') as f:
                session = json.load(f)
            
            # Create anonymized record
            record = {
                # Generate a random ID different from the original session ID
                "anonymized_id": hash(session["session_id"]) % 10000000,
                
                # Basic session metadata
                "session_date": session["timestamp"].split("T")[0],
                "session_duration_minutes": calculate_session_duration(session),
                
                # Screening data (only scores, not individual answers)
                "gad7_score": session["screening"].get("gad7_score", None),
                "phq9_score": session["screening"].get("phq9_score", None),
                
                # Interaction metrics
                "total_interactions": len(session["interactions"]),
                "tapping_sessions": session["tapping_sessions"],
                "completed_tapping_steps": session["completed_tapping_steps"],
                
                # Sentiment analysis (aggregated)
                "negative_sentiment_messages": count_sentiment(session["interactions"], "negative"),
                "positive_sentiment_messages": count_sentiment(session["interactions"], "positive"),
                "neutral_sentiment_messages": count_sentiment(session["interactions"], "neutral"),
                
                # Feedback (if provided)
                "feedback_rating": session["feedback"].get("rating", None) if session["feedback"] else None,
                "feedback_provided": session["feedback"].get("comments_provided", False) if session["feedback"] else False,
            }
            
            processed_data.append(record)
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    # Convert to DataFrame and save as CSV
    if processed_data:
        df = pd.DataFrame(processed_data)
        df.to_csv(output_file, index=False)
        return output_file
    
    return None

def calculate_session_duration(session_data):
    """Calculate session duration in minutes from session data"""
    if not session_data.get("interactions"):
        return 0
    
    start_time = datetime.datetime.fromisoformat(session_data["timestamp"])
    
    if session_data.get("feedback") and session_data["feedback"].get("timestamp"):
        end_time = datetime.datetime.fromisoformat(session_data["feedback"]["timestamp"])
    elif session_data["interactions"]:
        latest_interaction = session_data["interactions"][-1]
        end_time = datetime.datetime.fromisoformat(latest_interaction["timestamp"])
    else:
        return 0
    
    duration = (end_time - start_time).total_seconds() / 60.0
    return round(duration, 2)  # Return duration in minutes

def count_sentiment(interactions, sentiment_type):
    """Count interactions with a specific sentiment type"""
    return sum(1 for interaction in interactions if interaction.get("sentiment") == sentiment_type)

def implement_data_retention_policy(data_dir="session_data", retention_days=90):
    """
    Implement data retention policy by removing data older than specified days
    
    Args:
        data_dir: Directory containing session data files
        retention_days: Number of days to retain data
    
    Returns:
        Number of files deleted
    """
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=retention_days)
    session_files = list(Path(data_dir).glob("session_*.json"))
    
    deleted_count = 0
    
    for file_path in session_files:
        try:
            with open(file_path, 'r') as f:
                session = json.load(f)
            
            session_date = datetime.datetime.fromisoformat(session["timestamp"])
            
            if session_date < cutoff_date:
                os.remove(file_path)
                deleted_count += 1
                
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    
    return deleted_count

def delete_user_data(session_id, data_dir="session_data"):
    """
    Delete all data for a specific session ID
    
    Args:
        session_id: Session ID to delete
        data_dir: Directory containing session data
    
    Returns:
        Boolean indicating success/failure
    """
    try:
        file_path = os.path.join(data_dir, f"session_{session_id}.json")
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting session {session_id}: {e}")
        return False

def export_user_data(session_id, data_dir="session_data", output_dir="user_exports"):
    """
    Export a user's data for GDPR compliance
    
    Args:
        session_id: Session ID to export
        data_dir: Directory containing session data
        output_dir: Directory for exported data
    
    Returns:
        Path to exported file or None if not found
    """
    try:
        # Create export directory if it doesn't exist
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Source and destination paths
        source_path = os.path.join(data_dir, f"session_{session_id}.json")
        dest_path = os.path.join(output_dir, f"exported_session_{session_id}.json")
        
        if os.path.exists(source_path):
            shutil.copy2(source_path, dest_path)
            return dest_path
        return None
    except Exception as e:
        print(f"Error exporting session {session_id}: {e}")
        return None