#!/usr/bin/env python3
"""
DEV UI for Agentic Chat Bot - Following Flowchart Requirements

This implementation follows the exact flowchart structure:
1. Main Bot entry point
2. Login status check (Logged In vs Not Logged In)
3. Logged In path: Sentiment Analysis (Azure) → Transform/Insight/Action
4. Not Logged In path: Memory/Intent/Chat QA
"""

import gradio as gr
import json
import os
import time
from typing import Dict, Any, Optional, List, Tuple
import traceback
from datetime import datetime

# Import core functionality
try:
    from logged_in_bot.tools import handle_logged_in_turn, capabilities, redact_text, intent_of
    from logged_in_bot.handler import handle_turn
    from logged_in_bot.sentiment_azure import analyze_sentiment, SentimentResult
    from memory.sessions import SessionStore
    from memory.profile import Profile
    from core.config import settings
    from agenticcore.chatbot.services import ChatBot
except ImportError as e:
    print(f"Warning: Some imports failed: {e}")

class FlowchartAppState:
    """Application state following the flowchart structure"""
    
    def __init__(self):
        self.current_user = None
        self.session_store = None
        self.chatbot = None
        self.is_logged_in = False
        
    def initialize(self) -> Tuple[bool, str]:
        """Initialize core components"""
        try:
            self.session_store = SessionStore()
            self.chatbot = ChatBot()
            return True, "System initialized successfully"
        except Exception as e:
            return False, f"Initialization failed: {str(e)}"
    
    def set_login_status(self, username: str) -> bool:
        """Set user login status - main decision point in flowchart"""
        if username and username.strip():
            self.current_user = username.strip()
            self.is_logged_in = True
            return True
        else:
            self.current_user = None
            self.is_logged_in = False
            return False

# Global app state
app_state = FlowchartAppState()

def main_bot_entry(message: str, username: str = "") -> Tuple[str, str, str, str]:
    """
    Main Bot Entry Point (Purple box in flowchart)
    This is the central entry point that routes to different flows
    """
    if not message.strip():
        return "", "Please enter a message", "", "Enter a message to start"
    
    # Decision point: Logged In vs Not Logged In
    is_logged_in = app_state.set_login_status(username)
    
    if is_logged_in:
        # LOGGED IN PATH: Sentiment Analysis (Azure) → Transform/Insight/Action
        return logged_in_flow(message, username)
    else:
        # NOT LOGGED IN PATH: Memory/Intent/Chat QA  
        return not_logged_in_flow(message)

def logged_in_flow(message: str, username: str) -> Tuple[str, str, str, str]:
    """
    Logged In Flow (Pink box → Cyan box → Red box → Three outputs)
    1. User is logged in (Pink)
    2. Sentiment Analysis (Azure) (Cyan) 
    3. Transform/Insight/Action (Red)
    4. Three different outputs (Green circle, Pink triangle, Blue star)
    """
    try:
        # Step 1: Sentiment Analysis (Azure) - Cyan box
        sentiment_result = analyze_sentiment(message)
        sentiment_info = f"Sentiment: {sentiment_result.label} (confidence: {sentiment_result.score:.2f}, backend: {sentiment_result.backend})"
        
        # Step 2: Get logged-in user response
        user = {"id": username, "name": username}
        history = None
        if app_state.session_store:
            try:
                history = app_state.session_store.get_history(username)
            except:
                pass
        
        response = handle_logged_in_turn(message, history, user)
        if isinstance(response, dict):
            reply = response.get("reply", "No response")
            meta = response.get("meta", {})
        else:
            reply = str(response)
            meta = {}
        
        # Step 3: Transform/Insight/Action (Red box) - Generate three different outputs
        transform_output = f"🔄 Transform: {_generate_transform(message, sentiment_result)}"
        insight_output = f"💡 Insight: {_generate_insight(message, sentiment_result, meta)}"
        action_output = f"⭐ Action: {_generate_action(message, sentiment_result)}"
        
        # Combine all outputs
        full_response = f"{reply}\n\n{sentiment_info}\n\n{transform_output}\n{insight_output}\n{action_output}"
        
        return full_response, sentiment_info, f"User: {username} (Logged In)", "✅ Processed via Logged-In Flow"
        
    except Exception as e:
        error_msg = f"❌ Error in logged-in flow: {str(e)}"
        return error_msg, "", f"User: {username} (Error)", "❌ Flow Error"

def not_logged_in_flow(message: str) -> Tuple[str, str, str, str]:
    """
    Not Logged In Flow (Yellow box → Purple box)
    1. User not logged in (Yellow)
    2. Memory/Intent/Chat QA (Purple)
    """
    try:
        # Memory/Intent/Chat QA Processing
        if app_state.chatbot:
            # Basic chat response
            chat_response = app_state.chatbot.reply(message)
            reply = chat_response.get("reply", "No response")
            sentiment = chat_response.get("sentiment", "unknown")
            confidence = chat_response.get("confidence", 0.0)
        else:
            reply = "System not initialized"
            sentiment = "unknown"
            confidence = 0.0
        
        # Intent detection
        try:
            intent = intent_of(message)
            intent_info = f"Detected intent: {intent}"
        except:
            intent_info = "Intent detection unavailable"
        
        # Memory info (limited for non-logged users)
        memory_info = "Session memory: Limited (not logged in)"
        
        # Combine response
        full_response = f"{reply}\n\n{memory_info}\n{intent_info}"
        sentiment_info = f"Sentiment: {sentiment} (confidence: {confidence:.2f})"
        
        return full_response, sentiment_info, "Anonymous User (Not Logged In)", "⚠️ Processed via Not-Logged-In Flow"
        
    except Exception as e:
        error_msg = f"❌ Error in not-logged-in flow: {str(e)}"
        return error_msg, "", "Anonymous User (Error)", "❌ Flow Error"

def _generate_transform(message: str, sentiment: SentimentResult) -> str:
    """Generate transform output (Green circle in flowchart)"""
    transforms = {
        "positive": f"Amplified positive energy from: '{message[:50]}...'",
        "negative": f"Transformed negative sentiment: '{message[:50]}...' → constructive feedback",
        "neutral": f"Maintained balanced perspective on: '{message[:50]}...'"
    }
    return transforms.get(sentiment.label, f"Processed message: '{message[:50]}...'")

def _generate_insight(message: str, sentiment: SentimentResult, meta: Dict) -> str:
    """Generate insight output (Pink triangle in flowchart)"""
    insights = []
    
    if sentiment.backend == "azure":
        insights.append("Azure AI provided advanced sentiment analysis")
    else:
        insights.append("Local sentiment analysis applied")
    
    if len(message.split()) > 10:
        insights.append("Comprehensive message detected")
    else:
        insights.append("Concise message received")
    
    if meta:
        insights.append(f"Additional context available: {len(meta)} metadata items")
    
    return " | ".join(insights)

def _generate_action(message: str, sentiment: SentimentResult) -> str:
    """Generate action output (Blue star in flowchart)"""
    actions = {
        "positive": "Continue encouraging dialogue",
        "negative": "Provide supportive response and resources", 
        "neutral": "Maintain professional engagement"
    }
    base_action = actions.get(sentiment.label, "Standard response protocol")
    
    # Add message-specific actions
    if "?" in message:
        return f"{base_action} + Provide informative answer"
    elif "help" in message.lower():
        return f"{base_action} + Offer assistance"
    else:
        return f"{base_action} + Continue conversation"

def create_flowchart_ui():
    """Create the production UI following the exact flowchart structure"""
    
    # Custom CSS for flowchart-like appearance
    custom_css = """
    .main-bot { background: linear-gradient(45deg, #8B5CF6, #A855F7); color: white; }
    .logged-in { background: linear-gradient(45deg, #EC4899, #F97316); color: white; }
    .not-logged-in { background: linear-gradient(45deg, #EAB308, #F59E0B); color: white; }
    .sentiment-analysis { background: linear-gradient(45deg, #06B6D4, #0891B2); color: white; }
    .memory-intent { background: linear-gradient(45deg, #8B5CF6, #7C3AED); color: white; }
    .transform-box { background: linear-gradient(45deg, #DC2626, #EF4444); color: white; }
    .status-box { padding: 10px; border-radius: 8px; margin: 5px 0; }
    .flowchart-title { text-align: center; font-size: 24px; font-weight: bold; color: #8B5CF6; }
    """
    
    with gr.Blocks(css=custom_css, title="Agentic Chat Bot - Flowchart UI") as app:
        
        gr.Markdown("# 🤖 Agentic Chat Bot - Flowchart Production UI", elem_classes=["flowchart-title"])
        gr.Markdown("*Following the exact flowchart structure: Main Bot → Login Check → Branched Processing*")
        
        # Initialize system
        with gr.Row():
            init_btn = gr.Button("🚀 Initialize System", variant="primary", elem_classes=["main-bot"])
            init_status = gr.Textbox(label="System Status", interactive=False, elem_classes=["status-box"])
        
        # Main Bot Entry (Purple box)
        gr.Markdown("## 🟣 Main Bot Entry Point")
        with gr.Row():
            with gr.Column(scale=2):
                message_input = gr.Textbox(
                    label="Your Message", 
                    placeholder="Enter your message here...",
                    lines=3
                )
                username_input = gr.Textbox(
                    label="Username (optional - determines login status)", 
                    placeholder="Enter username to login, leave empty for anonymous",
                    lines=1
                )
                send_btn = gr.Button("🚀 Process via Main Bot", variant="primary", size="lg", elem_classes=["main-bot"])
            
            with gr.Column(scale=2):
                response_output = gr.Textbox(label="Bot Response", lines=8, interactive=False)
                sentiment_output = gr.Textbox(label="Sentiment Analysis Details", lines=2, interactive=False, elem_classes=["sentiment-analysis"])
        
        # Flow Status Display
        with gr.Row():
            user_status = gr.Textbox(label="User Status", interactive=False, elem_classes=["status-box"])
            flow_status = gr.Textbox(label="Flow Path", interactive=False, elem_classes=["status-box"])
        
        # Flowchart Visualization
        gr.Markdown("""
        ## 📊 Current Flow Path
        
        **Flowchart Logic:**
        1. 🟣 **Main Bot** (Entry Point)
        2. **Decision:** Logged In? 
           - 🟩 **Yes** → 🩷 Logged In → 🔵 Sentiment Analysis (Azure) → 🔴 Transform/Insight/Action → 🟢⚫🔵 (3 outputs)
           - 🟨 **No** → 🟨 Not Logged In → 🟣 Memory/Intent/Chat QA
        
        **To test different paths:**
        - **Logged In Path:** Enter a username and message
        - **Anonymous Path:** Leave username empty and enter message
        """)
        
        # Event handlers
        def initialize_system():
            success, msg = app_state.initialize()
            return f"{'✅' if success else '❌'} {msg}"
        
        def process_message(message, username):
            if not message.strip():
                return "Please enter a message", "", "No user", "No processing"
            
            response, sentiment, user_status, flow_status = main_bot_entry(message, username)
            return response, sentiment, user_status, flow_status
        
        # Wire up events
        init_btn.click(
            initialize_system,
            outputs=init_status
        )
        
        send_btn.click(
            process_message,
            inputs=[message_input, username_input],
            outputs=[response_output, sentiment_output, user_status, flow_status]
        )
        
        message_input.submit(
            process_message,
            inputs=[message_input, username_input], 
            outputs=[response_output, sentiment_output, user_status, flow_status]
        )
        
        # Example section
        with gr.Accordion("💡 Usage Examples", open=False):
            gr.Markdown("""
            ### Test the Flowchart Paths:
            
            **Logged-In User Path:**
            - Username: `john_doe`
            - Message: `I love this new feature!`
            - Expected: Sentiment Analysis (Azure) → Transform/Insight/Action outputs
            
            **Anonymous User Path:**
            - Username: *(leave empty)*
            - Message: `How does this work?`
            - Expected: Memory/Intent/Chat QA processing
            
            **Different Sentiments:**
            - Positive: `This is amazing and wonderful!`
            - Negative: `I hate this terrible experience`
            - Neutral: `Please provide the documentation`
            """)
        
        gr.Markdown("""
        ---
        *🔄 This UI strictly follows the provided flowchart structure with proper branching logic*
        """)
    
    return app

def main():
    """Launch the flowchart-based production UI"""
    print("🚀 Starting Flowchart-Based DEV UI...")

    # Initialize app state
    success, msg = app_state.initialize()
    if success:
        print(f"✅ {msg}")
    else:
        print(f"⚠️ {msg}")
    
    # Create and launch app
    app = create_flowchart_ui()
    
    print("🌟 Flowchart Production UI is ready!")
    print("📊 UI follows the exact flowchart structure:")
    print("   🟣 Main Bot → Login Check → Branched Processing")
    print("   🟩 Logged In: Sentiment (Azure) → Transform/Insight/Action")
    print("   🟨 Not Logged In: Memory/Intent/Chat QA")
    
    app.launch(
        server_name="0.0.0.0",
        server_port=7864,  # Different port
        share=False,
        show_error=True,
        auth=None,
        favicon_path=None,
        show_api=False
    )

if __name__ == "__main__":
    main()