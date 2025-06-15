"""
Screening module for EFT Chatbot
Handles assessments for anxiety (GAD-7) and depression (PHQ-9) with informed consent
"""

import gradio as gr
from modules.database import (
    has_given_consent, 
    record_consent, 
    store_assessment_results, 
    has_recent_assessment
)

# Assessment questions
GAD7_QUESTIONS = [
    "Feeling nervous, anxious or on edge?",
    "Not being able to stop or control worrying?",
    "Worrying too much about different things?",
    "Trouble relaxing?",
    "Being so restless that it is hard to sit still?",
    "Becoming easily annoyed or irritable?",
    "Feeling afraid as if something awful might happen?"
]

PHQ9_QUESTIONS = [
    "Little interest or pleasure in doing things?",
    "Feeling down, depressed, or hopeless?",
    "Trouble falling or staying asleep, or sleeping too much?",
    "Feeling tired or having little energy?",
    "Poor appetite or overeating?",
    "Feeling bad about yourself — or that you are a failure or have let yourself or your family down?",
    "Trouble concentrating on things, such as reading the newspaper or watching television?",
    "Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual?",
    "Thoughts that you would be better off dead or of hurting yourself in some way?"
]

# Response options
RESPONSE_OPTIONS = ["Not at all", "Several days", "More than half the days", "Nearly every day"]
RESPONSE_VALUES = [0, 1, 2, 3]

# Risk thresholds
GAD7_HIGH_RISK_THRESHOLD = 15  # Severe anxiety
PHQ9_HIGH_RISK_THRESHOLD = 15  # Moderately severe to severe depression
SUICIDE_QUESTION_INDEX = 8  # Index of suicide question in PHQ9

# Support resources
CRISIS_RESOURCES = """
## Please seek immediate help

**If you are in immediate danger, please call emergency services:**
- Call 999 (UK Emergency Services)

**Mental health crisis support:**
- Call NHS 111 and select the mental health option
- Contact the Samaritans: 116 123 (free from any phone, 24/7)
- Text "SHOUT" to 85258 (Crisis Text Line UK, 24/7)

**Please talk to someone about how you're feeling. Help is available.**
"""

HIGH_RISK_MESSAGE = """
## Support Resources

Based on your responses, we recommend speaking with a healthcare professional.

**NHS Mental Health Services:**
- Call NHS 111 and select the mental health option
- Contact your GP to discuss your mental health concerns
- Visit [NHS Mental Health Services](https://www.nhs.uk/mental-health/)

This chatbot is not a substitute for professional mental health support.
"""

# Informed consent text
INFORMED_CONSENT_TEXT = """
# Informed Consent

Before proceeding with the EFT (Emotional Freedom Techniques) chatbot service, please read and agree to the following:

## About This Service
This chatbot uses a fine-tuned AI model to provide EFT tapping guidance. It is designed as a research project and should not be considered a replacement for professional mental health services.

## Limitations
- This is an **experimental service** using artificial intelligence
- The chatbot is not a licensed therapist or healthcare provider
- It cannot diagnose or treat medical or psychological conditions
- It may not be suitable for severe mental health issues

## Data Privacy
- Your conversation with the chatbot is processed using OpenAI's API
- We collect anonymous usage data for research purposes
- We do not store personally identifiable information
- Your screening assessment results are not shared with third parties

## Risks and Benefits
**Potential Benefits:**
- Learning EFT techniques that may help with mild stress and anxiety
- Convenient access to guided EFT sessions

**Potential Risks:**
- EFT may not be effective for your specific situation
- Focusing on emotional issues without professional guidance may temporarily increase distress
- Technical limitations may result in inappropriate or ineffective guidance

## Your Rights
- You can stop using the service at any time
- You can request that your data be deleted by contacting the research team

## Emergency Support
This chatbot is not equipped to handle crises or emergencies. If you experience thoughts of harming yourself or others, please contact emergency services immediately.

By clicking "I Agree" below, you confirm that you understand and accept these terms.
"""

# State variables
current_assessment = "intro"  # Options: intro, consent, gad7, phq9, results, chatbot
gad7_scores = []
phq9_scores = []
is_high_risk = False
has_suicide_risk = False
has_consented = False

def reset_screening():
    """Reset all screening data"""
    global current_assessment, gad7_scores, phq9_scores, is_high_risk, has_suicide_risk, has_consented
    current_assessment = "intro"
    gad7_scores = []
    phq9_scores = []
    is_high_risk = False
    has_suicide_risk = False
    has_consented = False

def create_screening_interface():
    """Create and return all the screening UI components"""
    # Create state for current user ID
    user_id_state = gr.State(None)
    
    # Introduction screen
    with gr.Row(visible=True) as intro_screen:
        with gr.Column():
            gr.Markdown("""
            # Welcome to the EFT Chatbot

            This chatbot provides guidance on using Emotional Freedom Techniques (EFT), a form of psychological acupressure that may help reduce stress and anxiety.
            
            Before using the chatbot, you'll need to:
            1. Provide informed consent
            2. Complete a brief mental health screening
            
            These steps help ensure this tool is appropriate for your needs.
            """)
            intro_btn = gr.Button("Get Started", variant="primary")

    # Informed consent screen
    with gr.Row(visible=False) as consent_screen:
        with gr.Column():
            gr.Markdown(INFORMED_CONSENT_TEXT)
            with gr.Row():
                decline_btn = gr.Button("Decline", variant="secondary")
                consent_btn = gr.Button("I Agree", variant="primary")
            gr.Markdown("", elem_id="consent_error")
    
    # GAD-7 questionnaire
    with gr.Row(visible=False) as gad7_screen:
        with gr.Column():
            gr.Markdown("# Anxiety Assessment (GAD-7)\nOver the last 2 weeks, how often have you been bothered by the following problems?")
            gad7_questions = []
            for i, question in enumerate(GAD7_QUESTIONS):
                gad7_questions.append(gr.Radio(
                    choices=RESPONSE_OPTIONS,
                    label=f"{i+1}. {question}",
                    info="Please select one option"
                ))
            gad7_submit = gr.Button("Continue to Next Assessment", variant="primary")
    
    # PHQ-9 questionnaire
    with gr.Row(visible=False) as phq9_screen:
        with gr.Column():
            gr.Markdown("# Depression Assessment (PHQ-9)\nOver the last 2 weeks, how often have you been bothered by the following problems?")
            phq9_questions = []
            for i, question in enumerate(PHQ9_QUESTIONS):
                phq9_questions.append(gr.Radio(
                    choices=RESPONSE_OPTIONS,
                    label=f"{i+1}. {question}",
                    info="Please select one option"
                ))
            phq9_submit = gr.Button("Complete Assessment", variant="primary")
    
    # Results screen for high risk or suicide risk
    with gr.Row(visible=False) as risk_screen:
        with gr.Column():
            risk_message = gr.Markdown("", elem_id="risk_message")
    
    # Results screen for eligible users
    with gr.Row(visible=False) as results_screen:
        with gr.Column():
            gr.Markdown("# Assessment Results")
            gad7_result = gr.Markdown("", elem_id="gad7_result")
            phq9_result = gr.Markdown("", elem_id="phq9_result")
            continue_btn = gr.Button("Continue to EFT Chatbot", variant="primary")
    
    # Consent declined screen
    with gr.Row(visible=False) as consent_declined_screen:
        with gr.Column():
            gr.Markdown("""
            # Consent Declined

            You have declined to provide consent for using this EFT chatbot service.

            If you change your mind, you can refresh the page to start again.

            Thank you for your interest.
            """)
    
    # Returning user screen (skip assessment)
    with gr.Row(visible=False) as returning_user_screen:
        with gr.Column():
            gr.Markdown("# Welcome Back")
            gr.Markdown("""
            We see you've already completed the screening assessment recently.
            
            You can proceed directly to the EFT chatbot or take the assessment again if you wish.
            """)
            with gr.Row():
                reassess_btn = gr.Button("Take Assessment Again", variant="secondary")
                skip_btn = gr.Button("Proceed to Chatbot", variant="primary")
    
    # Function to show consent screen
    def show_consent():
        global current_assessment
        current_assessment = "consent"
        return {
            intro_screen: gr.update(visible=False),
            consent_screen: gr.update(visible=True)
        }
    
    # Function to handle consent agreement
    def agree_to_consent(user_id):
        global current_assessment, has_consented
        
        has_consented = True
        if user_id:
            record_consent(user_id)
            
            # Check if user has a recent assessment
            if has_recent_assessment(user_id):
                current_assessment = "returning"
                return {
                    consent_screen: gr.update(visible=False),
                    returning_user_screen: gr.update(visible=True)
                }
            else:
                current_assessment = "gad7"
                return {
                    consent_screen: gr.update(visible=False),
                    gad7_screen: gr.update(visible=True)
                }
        
        # Default fallback if no user_id
        current_assessment = "gad7"
        return {
            consent_screen: gr.update(visible=False),
            gad7_screen: gr.update(visible=True)
        }
    
    # Function to handle consent decline
    def decline_consent():
        global current_assessment
        current_assessment = "declined"
        return {
            consent_screen: gr.update(visible=False),
            consent_declined_screen: gr.update(visible=True)
        }
    
    # Function to validate GAD-7 answers
    def validate_gad7(*answers):
        # Check if all questions are answered
        for i, answer in enumerate(answers):
            if answer is None:
                return f"Please answer question {i+1} before continuing."
        return None
    
    # Function to validate PHQ-9 answers
    def validate_phq9(*answers):
        # Check if all questions are answered
        for i, answer in enumerate(answers):
            if answer is None:
                return f"Please answer question {i+1} before continuing."
        return None
    
    # Function to handle GAD-7 submission
    def submit_gad7(*answers):
        global current_assessment, gad7_scores
        
        # Validate answers
        error = validate_gad7(*answers)
        if error:
            return {
                gr.update(): error  # This will show as a warning in the UI
            }
        
        # Convert answers to scores
        gad7_scores = []
        for answer in answers:
            if answer == RESPONSE_OPTIONS[0]:
                gad7_scores.append(0)
            elif answer == RESPONSE_OPTIONS[1]:
                gad7_scores.append(1)
            elif answer == RESPONSE_OPTIONS[2]:
                gad7_scores.append(2)
            elif answer == RESPONSE_OPTIONS[3]:
                gad7_scores.append(3)
            else:
                gad7_scores.append(0)  # Default if not answered
        
        # Move to PHQ-9
        current_assessment = "phq9"
        return {
            gad7_screen: gr.update(visible=False),
            phq9_screen: gr.update(visible=True)
        }
    
    # Function to handle PHQ-9 submission
    def submit_phq9(user_id, *answers):
        global current_assessment, phq9_scores, is_high_risk, has_suicide_risk
        
        # Validate answers
        error = validate_phq9(*answers)
        if error:
            return {
                gr.update(): error  # This will show as a warning in the UI
            }
        
        # Convert answers to scores
        phq9_scores = []
        for answer in answers:
            if answer == RESPONSE_OPTIONS[0]:
                phq9_scores.append(0)
            elif answer == RESPONSE_OPTIONS[1]:
                phq9_scores.append(1)
            elif answer == RESPONSE_OPTIONS[2]:
                phq9_scores.append(2)
            elif answer == RESPONSE_OPTIONS[3]:
                phq9_scores.append(3)
            else:
                phq9_scores.append(0)  # Default if not answered
        
        # Calculate total scores
        gad7_total = sum(gad7_scores)
        phq9_total = sum(phq9_scores)
        
        # Check risk levels
        is_high_risk = (gad7_total >= GAD7_HIGH_RISK_THRESHOLD or 
                        phq9_total >= PHQ9_HIGH_RISK_THRESHOLD)
        
        # Check suicide risk (PHQ-9 question 9, index 8)
        if len(phq9_scores) > SUICIDE_QUESTION_INDEX:
            has_suicide_risk = phq9_scores[SUICIDE_QUESTION_INDEX] > 0
        
        # Store assessment results if we have a user_id
        if user_id:
            store_assessment_results(
                user_id, 
                gad7_total, 
                phq9_total, 
                is_high_risk, 
                has_suicide_risk
            )
        
        # Determine which screen to show next
        if has_suicide_risk:
            current_assessment = "crisis"
            return {
                phq9_screen: gr.update(visible=False),
                risk_screen: gr.update(visible=True),
                risk_message: CRISIS_RESOURCES
            }
        elif is_high_risk:
            current_assessment = "high_risk"
            return {
                phq9_screen: gr.update(visible=False),
                risk_screen: gr.update(visible=True),
                risk_message: HIGH_RISK_MESSAGE
            }
        else:
            current_assessment = "results"
            # Format GAD-7 result
            gad7_interpretation = "Minimal anxiety"
            if sum(gad7_scores) >= 15:
                gad7_interpretation = "Severe anxiety"
            elif sum(gad7_scores) >= 10:
                gad7_interpretation = "Moderate anxiety"
            elif sum(gad7_scores) >= 5:
                gad7_interpretation = "Mild anxiety"
            
            # Format PHQ-9 result
            phq9_interpretation = "Minimal depression"
            if sum(phq9_scores) >= 20:
                phq9_interpretation = "Severe depression"
            elif sum(phq9_scores) >= 15:
                phq9_interpretation = "Moderately severe depression"
            elif sum(phq9_scores) >= 10:
                phq9_interpretation = "Moderate depression"
            elif sum(phq9_scores) >= 5:
                phq9_interpretation = "Mild depression"
            
            return {
                phq9_screen: gr.update(visible=False),
                results_screen: gr.update(visible=True),
                gad7_result: f"**GAD-7 Score:** {sum(gad7_scores)}/21 - {gad7_interpretation}",
                phq9_result: f"**PHQ-9 Score:** {sum(phq9_scores)}/27 - {phq9_interpretation}"
            }
    
    # Function to skip assessment for returning users
    def skip_assessment():
        global current_assessment
        current_assessment = "chatbot"
        return {
            returning_user_screen: gr.update(visible=False)
        }
    
    # Function to take assessment again
    def retake_assessment():
        global current_assessment
        current_assessment = "gad7"
        return {
            returning_user_screen: gr.update(visible=False),
            gad7_screen: gr.update(visible=True)
        }
    
    # Connect button handlers
    intro_btn.click(
        show_consent,
        inputs=[],
        outputs=[intro_screen, consent_screen]
    )
    
    # Use user_id_state as input for agree_to_consent
    consent_btn_output = consent_btn.click(
        agree_to_consent,
        inputs=[user_id_state],
        outputs=[consent_screen, gad7_screen, returning_user_screen]
    )
    
    decline_btn.click(
        decline_consent,
        inputs=[],
        outputs=[consent_screen, consent_declined_screen]
    )
    
    gad7_submit.click(
        submit_gad7,
        inputs=gad7_questions,
        outputs=[gad7_screen, phq9_screen]
    )
    
    # Pass user_id to submit_phq9
    phq9_submit_output = phq9_submit.click(
        submit_phq9,
        inputs=[user_id_state] + phq9_questions,  # Pass user_id as first argument
        outputs=[
            phq9_screen, risk_screen, risk_message,
            phq9_screen, results_screen, gad7_result, phq9_result
        ]
    )
    
    continue_btn_output = continue_btn.click(
        lambda: {results_screen: gr.update(visible=False)},
        inputs=[],
        outputs=[results_screen]
    )
    
    skip_btn_output = skip_btn.click(
        skip_assessment,
        inputs=[],
        outputs=[returning_user_screen]
    )
    
    reassess_btn.click(
        retake_assessment,
        inputs=[],
        outputs=[returning_user_screen, gad7_screen]
    )
    
    # Return all screen components and output events for visibility control
    return {
        "intro_screen": intro_screen,
        "consent_screen": consent_screen,
        "gad7_screen": gad7_screen,
        "phq9_screen": phq9_screen,
        "risk_screen": risk_screen,
        "results_screen": results_screen,
        "consent_declined_screen": consent_declined_screen,
        "returning_user_screen": returning_user_screen,
        "continue_btn": continue_btn,
        "consent_btn_output": consent_btn_output,
        "phq9_submit_output": phq9_submit_output,
        "continue_btn_output": continue_btn_output,
        "skip_btn_output": skip_btn_output,
        "user_id_state": user_id_state
    }

def check_eligibility():
    """Check if the user is eligible to use the chatbot based on screening results"""
    return has_consented and not (is_high_risk or has_suicide_risk)

def get_screening_status():
    """Return the current status of the screening process"""
    return {
        "completed": current_assessment in ["results", "chatbot", "crisis", "high_risk"],
        "consented": has_consented,
        "eligible": check_eligibility(),
        "current_screen": current_assessment,
        "gad7_score": sum(gad7_scores) if gad7_scores else 0,
        "phq9_score": sum(phq9_scores) if phq9_scores else 0,
        "suicide_risk": has_suicide_risk
    }

def skip_consent_for_returning_user(user_id):
    """Update the interface to skip consent for returning users"""
    if has_given_consent(user_id):
        return {
            consent_screen: gr.update(visible=False),
            gad7_screen: gr.update(visible=True)
        }
    return {}