"""
Simplified personalisation module for EFT Chatbot
Only provides basic session info without attempting to reference past sessions
"""

from modules.auth import get_username

def build_personalised_prompt(user_id, chat_session):
    """
    Build a simple system prompt for the model
    
    Args:
        user_id: User ID for getting username
        chat_session: Current chat session messages
        
    Returns:
        List of message dictionaries for the OpenAI API
    """
    # Get username if available
    username = get_username(user_id) if user_id else None
    
    # Start with base system message
    system_msg = "You are Sarah, an EFT (Emotional Freedom Techniques) therapist chatbot. "
    
    if username:
        system_msg += f"You are speaking with {username}. "
    
    system_msg += """
    Your role is to provide supportive EFT tapping guidance. Be warm, conversational, and helpful.
    
    Follow these guidelines:
    1. Be natural and authentic in your responses
    2. Don't try to reference past sessions or imply a relationship history
    3. Focus on the present moment and the user's current needs
    4. When offering tapping, create sequences based on what the user is currently experiencing
    5. Always maintain a warm, empathetic tone without being overly familiar
    6. Always ask for intensity on a scale of 0-10 before tapping
    
    IMPORTANT ABOUT TAPPING SEQUENCES:
    - Include the karate chop point as the FIRST point in your tapping sequences
    - Always provide a setup statement with the karate chop point
    - Then continue with the remaining 8 tapping points
    - Your complete tapping sequence should include: karate chop, top of head, eyebrow, side of eye, under eye, under nose, chin, collarbone, under arm
    
    For complete tapping sequences, follow this pattern:
    - Start with "Karate chop: [setup statement]"
    - Then continue with the remaining 8 points with appropriate reminder phrases
    - After tapping, ask about the intensity level
    
    Keep your messages concise, helpful, and focused on the user's present needs.
    """
    
    # Create messages array
    messages = [
        {"role": "system", "content": system_msg}
    ]
    
    # Add current conversation context
    messages.extend(chat_session)
    
    return messages