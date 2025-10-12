#!/usr/bin/env python3
"""
Customer UI - Professional, user-friendly interface with document upload
"""

import gradio as gr
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime
import logging
import traceback

from logged_in_bot.tools import handle_logged_in_turn
from memory.sessions import SessionStore
from memory.rag.indexer import TfidfIndex, DEFAULT_INDEX_PATH, DocMeta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('customer_ui.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global state
class AppState:
    def __init__(self):
        self.username = None
        self.session_store = SessionStore()
        self.uploaded_docs = []
        
app_state = AppState()

def login(name: str) -> Tuple[str, bool, str]:
    """Handle user login"""
    logger.info(f"Login attempt: name='{name}'")
    if not name or not name.strip():
        logger.warning("Login failed: empty name")
        return "Please enter your name", False, ""
    app_state.username = name.strip()
    logger.info(f"Login successful: user='{app_state.username}'")
    return f"Welcome, {name}!", True, name

def logout() -> Tuple[str, bool, str]:
    """Handle logout"""
    logger.info(f"Logout: user='{app_state.username}'")
    app_state.username = None
    return "Logged out successfully", False, ""

def upload_document(file) -> str:
    """Upload and index document"""
    logger.info(f"Upload attempt: file={file}")
    if not file:
        logger.warning("Upload failed: no file selected")
        return "No file selected"
    
    try:
        # Read file
        file_path = Path(file.name)
        logger.info(f"Processing file: {file_path.name} (type: {file_path.suffix})")
        
        # Extract text based on file type
        if file_path.suffix == '.txt':
            text = file_path.read_text(encoding='utf-8', errors='ignore')
        elif file_path.suffix == '.pdf':
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = '\n'.join(page.extract_text() for page in reader.pages)
            except Exception as e:
                logger.error(f"PDF extraction failed: {e}")
                return "❌ PDF extraction failed. Install PyPDF2: pip install PyPDF2"
        elif file_path.suffix in ['.docx', '.doc']:
            try:
                from docx import Document
                doc = Document(file_path)
                text = '\n'.join(para.text for para in doc.paragraphs)
            except Exception as e:
                logger.error(f"DOCX extraction failed: {e}")
                return "❌ DOCX extraction failed. Install python-docx: pip install python-docx"
        else:
            logger.warning(f"Unsupported file type: {file_path.suffix}")
            return f"❌ Unsupported file type: {file_path.suffix}"
        
        logger.info(f"Extracted {len(text)} characters from {file_path.name}")
        
        # Index document
        idx = TfidfIndex.load(DEFAULT_INDEX_PATH)
        doc_id = f"uploaded_{file_path.name}_{datetime.now().timestamp()}"
        meta = DocMeta(doc_id=doc_id, source=file_path.name, title=file_path.name)
        idx.add_text(doc_id, text, meta)
        idx.save(DEFAULT_INDEX_PATH)
        
        # Clear cache so new document is immediately available
        from memory.rag.indexer import clear_index_cache
        clear_index_cache(DEFAULT_INDEX_PATH)
        
        # Track uploaded doc
        app_state.uploaded_docs.append(file_path.name)
        
        logger.info(f"Successfully indexed: {file_path.name}")
        return f"✅ Uploaded and indexed: {file_path.name}"
    except Exception as e:
        logger.error(f"Upload error: {e}\n{traceback.format_exc()}")
        return f"❌ Error: {str(e)}"

def chat(message: str, history: List[List[str]]) -> Tuple[List[List[str]], str]:
    """Process chat message"""
    logger.info(f"Chat request: user='{app_state.username}', message='{message}', history_len={len(history) if history else 0}")
    
    if not app_state.username:
        logger.warning("Chat blocked: user not logged in")
        return history or [], "Please log in first"
    
    if not message or not message.strip():
        logger.info("Empty message received")
        return history or [], ""
    
    try:
        user = {"id": app_state.username, "name": app_state.username}
        logger.info(f"Calling handle_logged_in_turn with user: {user}")
        
        response = handle_logged_in_turn(message, history, user)
        logger.info(f"Response received: type={type(response)}, content={str(response)[:200]}...")
        
        reply = response.get("reply", "No response") if isinstance(response, dict) else str(response)
        
        new_history = (history or []) + [[message, reply]]
        logger.info(f"Chat successful: reply_len={len(reply)}, new_history_len={len(new_history)}")
        
        return new_history, ""
    except Exception as e:
        logger.error(f"Chat error: {e}\n{traceback.format_exc()}")
        return history or [], f"Error: {str(e)}"

def get_docs_list() -> str:
    """Get list of uploaded documents"""
    if not app_state.uploaded_docs:
        return "No documents uploaded yet"
    return "\n".join(f"📄 {doc}" for doc in app_state.uploaded_docs)

def create_ui():
    """Create customer UI"""
    
    css = """
    .container { max-width: 1400px; margin: auto; }
    .header { text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; margin-bottom: 20px; }
    .chat-container { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    .sidebar { background: #f8f9fa; border-radius: 10px; padding: 15px; }
    .quick-btn { margin: 5px; }
    """
    
    with gr.Blocks(css=css, title="AI Assistant", theme=gr.themes.Soft()) as app:
        
        # State
        logged_in = gr.State(False)
        username_state = gr.State("")
        
        # Header
        gr.Markdown("""
        <div class="header">
            <h1>🤖 AI Assistant</h1>
            <p>Your intelligent helper for questions, documents, and more</p>
        </div>
        """)
        
        with gr.Row():
            # Sidebar
            with gr.Column(scale=1):
                gr.Markdown("### 👤 User Profile")
                
                with gr.Group():
                    name_input = gr.Textbox(label="Your Name", placeholder="Enter your name")
                    login_btn = gr.Button("🔐 Login", variant="primary")
                    logout_btn = gr.Button("🚪 Logout", visible=False)
                    status_text = gr.Markdown("Status: Not logged in")
                
                gr.Markdown("### 📁 Upload Documents")
                with gr.Group():
                    file_upload = gr.File(label="Upload .txt, .pdf, or .docx", file_types=[".txt", ".pdf", ".docx"])
                    upload_btn = gr.Button("📤 Upload & Index")
                    upload_status = gr.Textbox(label="Upload Status", interactive=False)
                
                gr.Markdown("### 📚 Your Documents")
                docs_list = gr.Textbox(label="Uploaded Files", value="No documents yet", interactive=False, lines=5)
                refresh_docs_btn = gr.Button("🔄 Refresh List")
                
                gr.Markdown("### 💡 Quick Questions")
                with gr.Column():
                    q1_btn = gr.Button("What products can I buy?", size="sm")
                    q2_btn = gr.Button("What are the parking rules?", size="sm")
                    q3_btn = gr.Button("What should I wear?", size="sm")
                    q4_btn = gr.Button("Help", size="sm")
            
            # Main chat area
            with gr.Column(scale=3):
                gr.Markdown("### 💬 Chat")
                
                chatbot = gr.Chatbot(height=500, label="Conversation")
                
                with gr.Row():
                    msg_input = gr.Textbox(
                        label="Message",
                        placeholder="Type your message here...",
                        scale=4
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)
                
                with gr.Row():
                    clear_btn = gr.Button("🗑️ Clear Chat")
                    export_btn = gr.Button("💾 Export Chat")
                
                export_output = gr.Textbox(label="Export", visible=False)
        
        # Event handlers
        def handle_login(name):
            msg, success, user = login(name)
            if success:
                return (
                    gr.update(value=msg),
                    gr.update(visible=False),
                    gr.update(visible=True),
                    success,
                    user,
                    gr.update(value="")
                )
            return msg, gr.update(), gr.update(), False, "", gr.update()
        
        def handle_logout():
            msg, success, user = logout()
            return (
                gr.update(value=msg),
                gr.update(visible=True),
                gr.update(visible=False),
                success,
                user,
                []
            )
        
        def handle_upload(file):
            result = upload_document(file)
            docs = get_docs_list()
            return result, docs
        
        def handle_quick_question():
            return "What products can I buy?"
        
        def handle_q2():
            return "What are the parking rules?"
        
        def handle_q3():
            return "What should I wear?"
        
        def handle_q4():
            return "help"
        
        def export_chat(history):
            if not history:
                return gr.update(value="No chat to export", visible=True)
            
            export_text = f"Chat Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            for user_msg, bot_msg in history:
                export_text += f"You: {user_msg}\n"
                export_text += f"Bot: {bot_msg}\n\n"
            
            return gr.update(value=export_text, visible=True)
        
        # Wire up events
        login_btn.click(
            handle_login,
            inputs=[name_input],
            outputs=[status_text, login_btn, logout_btn, logged_in, username_state, name_input]
        )
        
        logout_btn.click(
            handle_logout,
            outputs=[status_text, login_btn, logout_btn, logged_in, username_state, chatbot]
        )
        
        upload_btn.click(
            handle_upload,
            inputs=[file_upload],
            outputs=[upload_status, docs_list]
        )
        
        refresh_docs_btn.click(
            get_docs_list,
            outputs=[docs_list]
        )
        
        # Chat
        send_btn.click(chat, inputs=[msg_input, chatbot], outputs=[chatbot, msg_input])
        msg_input.submit(chat, inputs=[msg_input, chatbot], outputs=[chatbot, msg_input])
        
        # Quick questions
        q1_btn.click(handle_quick_question, outputs=[msg_input]).then(
            chat, inputs=[msg_input, chatbot], outputs=[chatbot, msg_input]
        )
        q2_btn.click(handle_q2, outputs=[msg_input]).then(
            chat, inputs=[msg_input, chatbot], outputs=[chatbot, msg_input]
        )
        q3_btn.click(handle_q3, outputs=[msg_input]).then(
            chat, inputs=[msg_input, chatbot], outputs=[chatbot, msg_input]
        )
        q4_btn.click(handle_q4, outputs=[msg_input]).then(
            chat, inputs=[msg_input, chatbot], outputs=[chatbot, msg_input]
        )
        
        clear_btn.click(lambda: [], outputs=[chatbot])
        export_btn.click(export_chat, inputs=[chatbot], outputs=[export_output])
    
    return app

if __name__ == "__main__":
    logger.info("Starting Customer UI...")
    app = create_ui()
    logger.info("Launching on port 7862")
    app.launch(server_name="0.0.0.0", server_port=7861, share=False)
