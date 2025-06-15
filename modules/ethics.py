# modules/ethics.py
class EthicsGuide:
    def __init__(self):
        self.high_risk_topics = [
            "illegal activities",
            "self-harm methods",
            "dangerous medical advice",
            "manipulative techniques",
            "exploitation",
        ]
    
    def check_content(self, message):
        """Check content against ethical guidelines"""
        message_lower = message.lower()
        
        for topic in self.high_risk_topics:
            if topic in message_lower:
                return False, f"Content related to {topic} is not supported for ethical reasons."
        
        return True, ""
    
    def check_user_capabilities(self, user_context):
        """Check if user appears to have diminished capacity to consent"""
        concerns = []
        
        # Check for potential diminished capacity based on assessment scores
        if user_context.get("phq9_score", 0) >= 20:
            concerns.append("Severe depression symptoms may impair decision-making capacity")
        
        # Other checks for vulnerability
        age = user_context.get("age")
        if age and (age < 18 or age > 90):
            concerns.append("Age-related considerations for informed consent")
        
        return concerns
    
    def get_ethical_guidelines(self):
        """Return the ethical guidelines for the application"""
        return """
        # Ethical Guidelines for EFT Chatbot
        
        ## Principles
        
        This application adheres to the following ethical principles:
        
        1. **Non-maleficence**: Do no harm to users
        2. **Beneficence**: Promote user wellbeing
        3. **Autonomy**: Respect user choices and independence
        4. **Justice**: Provide fair and equal service
        5. **Transparency**: Be clear about capabilities and limitations
        
        ## Boundaries
        
        This application is not designed to:
        - Replace professional mental health care
        - Diagnose medical or psychological conditions
        - Provide emergency services in crisis situations
        - Give advice on medication management
        - Address complex trauma without professional guidance
        
        ## Safety Measures
        
        We implement several safety measures:
        - Crisis detection and appropriate resource provision
        - Regular screening for concerning symptoms
        - Clear statements about the limitations of EFT
        - Encouragement of professional care when appropriate
        """