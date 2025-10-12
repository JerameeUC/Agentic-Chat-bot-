#!/usr/bin/env python3
"""
Gradio App for Agentic Chat Bot
Provides a comprehensive interface to test all functionality including:
- Basic chat with sentiment analysis
- Logged-in bot with memory and RAG
- PII redaction capabilities
- Intent detection
- System capabilities overview
"""

import gradio as gr
import json
import os
from typing import Dict, Any, Optional, List, Tuple
import traceback

# Import core functionality
try:
    from agenticcore.chatbot.services import ChatBot
    from logged_in_bot.tools import handle_logged_in_turn, capabilities, redact_text, intent_of
    from memory.sessions import SessionStore
    from core.config import settings
    from app.app import _handle_text
except ImportError as e:
    print(f"Warning: Some imports failed: {e}")
    print("Make sure all dependencies are installed and the project is properly set up")

# Global instances
chatbot = None
session_store = None

def initialize_components():
    """Initialize chatbot and session store"""
    global chatbot, session_store
    try:
        chatbot = ChatBot(system_prompt="You are a helpful AI assistant with sentiment analysis capabilities.")
        session_store = SessionStore()
        return "✅ Components initialized successfully"
    except Exception as e:
        return f"❌ Initialization error: {str(e)}"

def basic_chat(message: str) -> Tuple[str, str]:
    """Basic chat functionality with sentiment analysis"""
    if not message.strip():
        return "Please enter a message", ""
    
    try:
        if not chatbot:
            return "❌ Chatbot not initialized", ""
        
        response = chatbot.reply(message)
        reply = response.get("reply", "No response")
        sentiment = response.get("sentiment", "unknown")
        confidence = response.get("confidence", 0.0)
        
        metadata = f"Sentiment: {sentiment} (confidence: {confidence})"
        return reply, metadata
    except Exception as e:
        return f"❌ Error: {str(e)}", f"Exception: {traceback.format_exc()}"

def advanced_chat(message: str, user_id: str) -> Tuple[str, str]:
    """Advanced chat with memory, RAG, and full logging"""
    if not message.strip():
        return "Please enter a message", ""
    
    if not user_id.strip():
        user_id = "demo_user"
    
    try:
        # Create mock user object
        user = {"id": user_id, "name": f"User {user_id}"}
        
        # Get conversation history from session store
        history = None
        if session_store:
            try:
                history = session_store.get_history(user_id)
            except:
                pass  # History might not exist yet
        
        # Process the message
        response = handle_logged_in_turn(message, history, user)
        
        if isinstance(response, dict):
            reply = response.get("reply", "No response")
            meta = response.get("meta", {})
            metadata = f"Meta: {json.dumps(meta, indent=2)}"
        else:
            reply = str(response)
            metadata = "No metadata available"
        
        return reply, metadata
    except Exception as e:
        return f"❌ Error: {str(e)}", f"Exception: {traceback.format_exc()}"

def test_pii_redaction(text: str) -> str:
    """Test PII redaction functionality"""
    if not text.strip():
        return "Please enter text to redact"
    
    try:
        redacted = redact_text(text)
        return f"Original: {text}\n\nRedacted: {redacted}"
    except Exception as e:
        return f"❌ Error: {str(e)}\n{traceback.format_exc()}"

def test_intent_detection(text: str) -> str:
    """Test intent detection functionality"""
    if not text.strip():
        return "Please enter text for intent detection"
    
    try:
        intent = intent_of(text)
        return f"Detected intent: {intent}"
    except Exception as e:
        return f"❌ Error: {str(e)}\n{traceback.format_exc()}"

def get_system_capabilities() -> str:
    """Get system capabilities information"""
    try:
        caps = capabilities()
        return json.dumps(caps, indent=2)
    except Exception as e:
        return f"❌ Error: {str(e)}\n{traceback.format_exc()}"

def simple_text_handler(text: str) -> str:
    """Test the simple text handler from app.py"""
    try:
        return _handle_text(text)
    except Exception as e:
        return f"❌ Error: {str(e)}"

# Create Gradio interface
def create_gradio_app():
    """Create and configure the Gradio application"""
    
    with gr.Blocks(title="Agentic Chat Bot - Test Interface") as app:
        gr.Markdown("# 🤖 Agentic Chat Bot - Comprehensive Testing Interface")
        gr.Markdown("This interface allows you to test all functionality of the Agentic Chat Bot project.")
        
        # Initialization section
        with gr.Row():
            with gr.Column():
                gr.Markdown("## 🚀 System Initialization")
                init_btn = gr.Button("Initialize Components", variant="primary")
                init_status = gr.Textbox(label="Initialization Status", interactive=False)
        
        init_btn.click(initialize_components, outputs=init_status)
        
        # Basic Chat Section
        with gr.Tab("💬 Basic Chat"):
            gr.Markdown("### Simple chat with sentiment analysis")
            with gr.Row():
                with gr.Column(scale=2):
                    basic_input = gr.Textbox(
                        label="Your message",
                        placeholder="Type your message here...",
                        lines=2
                    )
                    basic_submit = gr.Button("Send", variant="primary")
                with gr.Column(scale=2):
                    basic_output = gr.Textbox(label="Bot Response", lines=3)
                    basic_meta = gr.Textbox(label="Sentiment Analysis", lines=2)
            
            basic_submit.click(
                basic_chat,
                inputs=basic_input,
                outputs=[basic_output, basic_meta]
            )
            basic_input.submit(
                basic_chat,
                inputs=basic_input,
                outputs=[basic_output, basic_meta]
            )
        
        # Advanced Chat Section
        with gr.Tab("🧠 Advanced Chat"):
            gr.Markdown("### Chat with memory, RAG, and full logging capabilities")
            with gr.Row():
                with gr.Column(scale=2):
                    adv_user_id = gr.Textbox(
                        label="User ID",
                        value="demo_user",
                        placeholder="Enter user ID for session management"
                    )
                    adv_input = gr.Textbox(
                        label="Your message",
                        placeholder="Type your message here...",
                        lines=3
                    )
                    adv_submit = gr.Button("Send", variant="primary")
                with gr.Column(scale=2):
                    adv_output = gr.Textbox(label="Bot Response", lines=4)
                    adv_meta = gr.Textbox(label="Metadata & Analysis", lines=6)
            
            adv_submit.click(
                advanced_chat,
                inputs=[adv_input, adv_user_id],
                outputs=[adv_output, adv_meta]
            )
            adv_input.submit(
                advanced_chat,
                inputs=[adv_input, adv_user_id],
                outputs=[adv_output, adv_meta]
            )
        
        # PII Redaction Section
        with gr.Tab("🔒 PII Redaction"):
            gr.Markdown("### Test Personal Identifiable Information redaction")
            with gr.Row():
                with gr.Column():
                    pii_input = gr.Textbox(
                        label="Text with PII",
                        placeholder="Enter text that may contain PII (emails, phone numbers, etc.)",
                        lines=4
                    )
                    pii_submit = gr.Button("Redact PII", variant="primary")
                with gr.Column():
                    pii_output = gr.Textbox(label="Redaction Results", lines=6)
            
            pii_submit.click(test_pii_redaction, inputs=pii_input, outputs=pii_output)
        
        # Intent Detection Section
        with gr.Tab("🎯 Intent Detection"):
            gr.Markdown("### Test intent detection capabilities")
            with gr.Row():
                with gr.Column():
                    intent_input = gr.Textbox(
                        label="User message",
                        placeholder="Enter a message to analyze its intent",
                        lines=3
                    )
                    intent_submit = gr.Button("Detect Intent", variant="primary")
                with gr.Column():
                    intent_output = gr.Textbox(label="Detected Intent", lines=4)
            
            intent_submit.click(test_intent_detection, inputs=intent_input, outputs=intent_output)
        
        # Simple Text Handler Section
        with gr.Tab("📝 Simple Text Handler"):
            gr.Markdown("### Test the basic text handler from app.py")
            gr.Markdown("Supports commands like 'reverse <text>', 'help', or just echoes your message")
            with gr.Row():
                with gr.Column():
                    simple_input = gr.Textbox(
                        label="Your input",
                        placeholder="Try: 'help', 'reverse hello', or any text",
                        lines=2
                    )
                    simple_submit = gr.Button("Process", variant="primary")
                with gr.Column():
                    simple_output = gr.Textbox(label="Response", lines=3)
            
            simple_submit.click(simple_text_handler, inputs=simple_input, outputs=simple_output)
            simple_input.submit(simple_text_handler, inputs=simple_input, outputs=simple_output)
        
        # System Info Section
        with gr.Tab("ℹ️ System Info"):
            gr.Markdown("### System capabilities and configuration")
            caps_btn = gr.Button("Get System Capabilities", variant="primary")
            caps_output = gr.Textbox(label="System Capabilities", lines=10)
            
            caps_btn.click(get_system_capabilities, outputs=caps_output)
        
        # Instructions
        with gr.Accordion("📋 Usage Instructions", open=False):
            gr.Markdown("""
            ### How to use this interface:
            
            1. **Initialize Components**: Click the "Initialize Components" button first to set up the chatbot and session store.
            
            2. **Basic Chat**: Simple chat with sentiment analysis. Good for testing basic functionality.
            
            3. **Advanced Chat**: Full-featured chat with:
               - Memory and session management
               - RAG (Retrieval-Augmented Generation) capabilities  
               - Intent detection
               - PII redaction
               - Comprehensive metadata
            
            4. **PII Redaction**: Test the system's ability to identify and redact personal information.
            
            5. **Intent Detection**: Analyze what the system thinks the user intends to do.
            
            6. **Simple Text Handler**: Test basic text processing (reverse text, help commands, etc.)
            
            7. **System Info**: View system capabilities and configuration.
            
            ### Tips:
            - Try different types of messages to test sentiment analysis
            - Use the same User ID in Advanced Chat to test memory persistence
            - Test PII redaction with emails, phone numbers, names, etc.
            - The system supports various intents like questions, commands, greetings, etc.
            """)
    
    return app

if __name__ == "__main__":
    app = create_gradio_app()
    print("🚀 Starting Gradio app for Agentic Chat Bot...")
    print("📝 Make sure to click 'Initialize Components' first!")
    app.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False,
        debug=True,
        show_error=True
    )