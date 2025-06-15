"""
Emotion Analysis module for EFT Chatbot
Uses BERT model to detect emotions in user messages
"""

from transformers import pipeline

class EmotionAnalyzer:
    def __init__(self):
        # Initialize the emotion classifier
        try:
            # Load a pre-trained emotion detection model
            self.classifier = pipeline(
                "text-classification", 
                model="bhadresh-savani/distilbert-base-uncased-emotion",
                top_k=1
            )
            self.is_initialized = True
            print("Emotion analyzer initialized successfully")
        except Exception as e:
            print(f"Error initializing emotion analyzer: {e}")
            self.is_initialized = False
    
    def detect_emotion(self, text):
        """
        Detect the primary emotion in text
        
        Args:
            text: The text to analyze
            
        Returns:
            String representing the detected emotion
        """
        if not self.is_initialized:
            return "neutral"
            
        if not text or len(text.strip()) == 0:
            return "neutral"
        
        try:
            # Get prediction from model
            result = self.classifier(text)[0][0]
            emotion = result["label"]
            confidence = result["score"]
            
            # Map to more general categories for consistency
            emotion_mapping = {
                "joy": "happy",
                "love": "positive",
                "sadness": "sad",
                "anger": "angry",
                "fear": "anxious",
                "surprise": "surprised"
            }
            
            # Use mapped emotion or original if not in mapping
            mapped_emotion = emotion_mapping.get(emotion, emotion)
            
            return mapped_emotion
            
        except Exception as e:
            print(f"Error detecting emotion: {e}")
            return "neutral"
    
    def analyze_with_details(self, text):
        """
        Analyze text and return detailed emotion information
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary with emotion information
        """
        if not self.is_initialized:
            return {"emotion": "neutral", "confidence": 1.0, "original": None}
            
        if not text or len(text.strip()) == 0:
            return {"emotion": "neutral", "confidence": 1.0, "original": None}
        
        try:
            # Get prediction from model
            result = self.classifier(text)[0][0]
            emotion = result["label"]
            confidence = result["score"]
            
            # Map to more general categories
            emotion_mapping = {
                "joy": "happy",
                "love": "positive",
                "sadness": "sad",
                "anger": "angry",
                "fear": "anxious",
                "surprise": "surprised"
            }
            
            mapped_emotion = emotion_mapping.get(emotion, emotion)
            
            return {
                "emotion": mapped_emotion,
                "confidence": confidence,
                "original": emotion
            }
            
        except Exception as e:
            print(f"Error analyzing emotion: {e}")
            return {"emotion": "neutral", "confidence": 1.0, "original": None}

# Fallback emotion detection using keywords if BERT fails
def detect_emotion_keywords(text):
    """
    Simple emotion detection using keywords
    
    Args:
        text: Text to analyze
        
    Returns:
        Detected emotion string
    """
    text = text.lower()
    
    emotions = {
        "anxious": ["anxious", "worried", "nervous", "stress", "panic", "afraid", "scared", "terrified"],
        "sad": ["sad", "unhappy", "depressed", "down", "blue", "upset", "miserable", "grief"],
        "angry": ["angry", "mad", "furious", "annoyed", "irritated", "frustrated", "upset"],
        "happy": ["happy", "glad", "joy", "pleased", "delighted", "content", "satisfied"],
        "positive": ["better", "good", "relieved", "hopeful", "grateful", "thankful"]
    }
    
    # Check each emotion category
    for emotion, keywords in emotions.items():
        if any(keyword in text for keyword in keywords):
            return emotion
    
    return "neutral"