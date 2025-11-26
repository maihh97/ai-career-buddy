import streamlit as st
import openai
import os
from dotenv import load_dotenv
from typing import Optional, List, Dict
from datetime import datetime
import io
from docx import Document
import pdfplumber


# Load environment variables
load_dotenv()

# Career Buddy Configuration
CAREER_BUDDY_SYSTEM_PROMPT = """
You are a Career Buddy, an expert career advisor and resume analyst. Your role is to:

1. **Resume Analysis**: Analyze uploaded resumes and provide detailed feedback on:
   - Content quality and relevance
   - Formatting and structure
   - Skills assessment
   - Achievement quantification
   - ATS (Applicant Tracking System) compatibility

2. **Career Guidance**: Provide personalized career advice including:
   - Career path recommendations
   - Skill development suggestions
   - Industry insights and trends
   - Interview preparation tips
   - Networking strategies

3. **Job Search Support**: Help with:
   - Job search strategies
   - Cover letter guidance
   - LinkedIn profile optimization
   - Salary negotiation advice

Always provide actionable, specific, and encouraging advice. When analyzing files, be thorough and constructive in your feedback.
Keep your responses conversational and engaging, as you're having an ongoing chat with the user.
"""

class CareerBuddyChat:
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Azure OpenAI client"""
        try:
            # Get configuration from environment variables
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
            
            if not azure_endpoint or not api_key:
                st.error("Please set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in your environment variables")
                return False
            
            # Create Azure OpenAI client
            self.client = openai.AzureOpenAI(
                azure_endpoint=azure_endpoint,
                api_key=api_key,
                api_version=api_version
            )
            
            return True
            
        except Exception as e:
            st.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
            return False
    
    def get_response(self, messages: List[Dict], model_name: str = "gpt-4") -> str:
        """Get response from Azure OpenAI"""
        if not self.client:
            return "Azure OpenAI client is not initialized. Please check your configuration."
        
        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                stream=False
            )
            
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content or "No response generated."
            else:
                return "No response received from the model. Please try again."
            
        except Exception as e:
            return f"Error getting response: {str(e)}"
    
    def get_streaming_response(self, messages: List[Dict], model_name: str = "gpt-4"):
        """Get streaming response from Azure OpenAI"""
        if not self.client:
            yield "Azure OpenAI client is not initialized. Please check your configuration."
            return
        
        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                stream=True
            )
            
            has_content = False
            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta_content = chunk.choices[0].delta.content
                    if delta_content is not None:
                        has_content = True
                        yield delta_content
            
            if not has_content:
                yield "No response generated. Please try again with a different question."
            
        except Exception as e:
            yield f"Error getting response: {str(e)}. Please check your model deployment name and try again."


def extract_text_content(uploaded_file) -> List[str]:
    """
    Extract text content line by line from DOCX, PDF, or TXT.
    Returns a list of strings (each line).
    """
    try:
        file_name = uploaded_file.name
        ext = file_name.lower().split('.')[-1]

        if ext == 'docx':
            doc = Document(io.BytesIO(uploaded_file.read()))
            return [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        elif ext == 'pdf':
            lines = []
            with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    page_lines = [line.strip() for line in text.splitlines() if line.strip()]
                    lines.extend(page_lines)
            return lines
        elif ext == 'txt':
            content = uploaded_file.read().decode("utf-8", errors="ignore")
            return [line.strip() for line in content.splitlines() if line.strip()]

        else:
            return [f"Unsupported file type: {ext}. Please upload .docx, .pdf, or .txt."]
    except Exception as e:
        return [f"Error reading file {file_name} ({ext}): {str(e)}"]

def initialize_session_state():
    """Initialize Streamlit session state"""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hello! I'm Career Buddy, your AI career advisor. I'm here to help with resume analysis, career guidance, job search strategies, and more. How can I assist you today?",
                "timestamp": datetime.now()
            }
        ]
    
    if "career_buddy" not in st.session_state:
        st.session_state.career_buddy = CareerBuddyChat()
    
    if "uploaded_content" not in st.session_state:
        st.session_state.uploaded_content = None

def display_chat_message(message, is_user=False):
    """Display a chat message with proper styling"""
    if is_user:
        
        st.markdown(
            f"""
            <div style="
                display: flex;
                justify-content: flex-end;
                margin: 1rem 0;
            ">
                <div style="
                    background-color: #007ACC;
                    color: white;
                    padding: 0.75rem 1rem;
                    border-radius: 1rem 1rem 0.25rem 1rem;
                    max-width: 70%;
                    word-wrap: break-word;
                ">
                    {message['content']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f"""
            <div style="
                display: flex;
                justify-content: flex-start;
                margin: 1rem 0;
            ">
                <div style="
                    background-color: #f1f3f4;
                    color: #333;
                    padding: 0.75rem 1rem;
                    border-radius: 1rem 1rem 1rem 0.25rem;
                    max-width: 70%;
                    word-wrap: break-word;
                    border-left: 3px solid #007ACC;
                ">
                    {message['content']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

def main():
    # Page configuration
    st.set_page_config(
        page_title="Career Buddy",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.title("💼 Career Buddy Chat")
    st.markdown("*Have an interactive conversation with your AI career advisor*")
    
    # Navigation
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🎯 Interview Practice", type="secondary", use_container_width=True):
            st.switch_page("interview_practice.py")
    with col2:
        st.markdown("") # spacing
    
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        
        # File upload section
        st.header("📤 Upload Resume")
        uploaded_file = st.file_uploader(
            "Upload your resume",
            type=['txt', 'pdf', 'doc', 'docx'],
            help="Upload for analysis in chat"
        )
        
        if uploaded_file:
            file_content = extract_text_content(uploaded_file)
            st.session_state.uploaded_content = file_content
            st.success(f"✅ {uploaded_file.name} uploaded!")
            st.write(file_content)
            if st.button("📋 Analyze Resume"):
                # Add resume analysis to chat with the actual content
                st.session_state.messages.append({
                    "role": "user",
                    "content": f"📄 Please analyze my resume: {uploaded_file.name}\n\nResume Content:\n{file_content}",
                    "timestamp": datetime.now()
                })
                # Trigger rerun to show the new message and get response
                st.rerun()
        
        # Resume text input
        st.header("📝 Resume Text")
        resume_text = st.text_area(
            "Or paste resume content:",
            height=150,
            placeholder="Paste your resume here..."
        )
        
        if resume_text and st.button("📋 Analyze Text"):
            st.session_state.uploaded_content = resume_text
            st.session_state.messages.append({
                "role": "user",
                "content": f"📄 Please analyze my resume (pasted text)\n\nResume Content:\n{resume_text}",
                "timestamp": datetime.now()
            })
            st.rerun()
        
        st.markdown("---")
        
        st.header("⚙️ Configuration")
        
        # Check environment variables
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
        
        if endpoint and api_key:
            st.success("✅ Azure OpenAI configured")
            st.info(f"API Version: {api_version}")
            
            # Model selection with custom input option
            model_options = ["gpt-4", "gpt 4.1", "DeepSeek-R1", "gpt-4.1-mini", "Phi-4"]
            selected_model = st.selectbox(
                "Select Model:",
                model_options,
                help="Choose the Azure OpenAI model deployment name"
            )
            
            if selected_model == "Custom...":
                model_name = st.text_input(
                    "Custom Model Deployment Name:",
                    value="gpt-4.1",
                    help="Enter your exact Azure OpenAI model deployment name"
                )
            else:
                model_name = selected_model
            
            # Warning about model deployment
            st.warning("⚠️ Make sure the model name matches your Azure OpenAI deployment exactly!")
        else:
            st.error("❌ Azure OpenAI not configured")
            model_name = "gpt-4.1"
        
        st.markdown("---")
        
        # Chat controls
        st.header("🔧 Chat Controls")
        
        # Test connection button
        if st.button("🔍 Test Connection", use_container_width=True):
            with st.spinner("Testing Azure OpenAI connection..."):
                test_messages = [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Hello, connection test successful!'"}
                ]
                
                response = st.session_state.career_buddy.get_response(test_messages, model_name)
                
                if "Error" in response:
                    st.error(f"❌ Connection failed: {response}")
                    st.markdown("""
                    **Troubleshooting tips:**
                    - Check your model deployment name in Azure OpenAI
                    - Verify your API key is correct
                    - Ensure your endpoint URL is correct
                    """)
                else:
                    st.success(f"✅ Connection successful! Response: {response}")
        
        if st.button("🗑️ Clear Chat", type="secondary", use_container_width=True):
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "Hello! I'm Career Buddy, your AI career advisor. How can I assist you today?",
                    "timestamp": datetime.now()
                }
            ]
            st.session_state.uploaded_content = None
            st.rerun()
    
    # Main chat interface    
    # Quick actions
    st.header("💬 Quick asks")
    
    quick_prompts = [
        "What skills should I develop?",
        "Help with interview prep",
        "Review my LinkedIn profile tips",
        "Salary negotiation advice",
        "Career change guidance"
    ]
    
    for prompt in quick_prompts:
        if st.button(prompt, key=f"quick_{prompt}", use_container_width=True):
            # Include uploaded content if it exists and the prompt is relevant
            content = prompt
            if st.session_state.uploaded_content and any(word in prompt.lower() for word in ['skills', 'resume', 'career']):
                content = f"{prompt}\n\nHere's my resume for context:\n{st.session_state.uploaded_content}"
            
            st.session_state.messages.append({
                "role": "user",
                "content": content,
                "timestamp": datetime.now()
            })
            st.rerun()
    
    # Create chat container
    chat_container = st.container()
    
    with chat_container:
        # Display chat messages
        for message in st.session_state.messages:
            display_chat_message(message, is_user=(message["role"] == "user"))
    
    # Handle new assistant response if last message is from user
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
        with st.spinner("Career Buddy is thinking..."):
            # Prepare messages for API
            api_messages = [{"role": "system", "content": CAREER_BUDDY_SYSTEM_PROMPT}]
            
            for msg in st.session_state.messages:
                if msg["role"] in ["user", "assistant"]:
                    api_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Get response from Career Buddy
            response_placeholder = st.empty()
            full_response = ""
            
            # Stream the response
            for chunk in st.session_state.career_buddy.get_streaming_response(api_messages, model_name):
                full_response += chunk
                with response_placeholder.container():
                    display_chat_message({
                        "role": "assistant",
                        "content": full_response + "▋",
                        "timestamp": datetime.now()
                    })
            
            # Add the complete response to chat history
            st.session_state.messages.append({
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.now()
            })
            
            # Clear the placeholder and show final message
            response_placeholder.empty()
            display_chat_message({
                "role": "assistant",
                "content": full_response,
                "timestamp": datetime.now()
            })
    
    # Chat input
    st.markdown("---")
    
    # Show if resume content is loaded
    if st.session_state.uploaded_content:
        st.info(f"📄 Resume content loaded ({len(st.session_state.uploaded_content)} characters) - Will be included in relevant questions")
    
    # Create columns for chat input
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "Type your message:",
            key="user_input",
            placeholder="Ask me about your career, resume, job search, or anything else...",
            label_visibility="collapsed"
        )
        
        # Option to attach resume to current message
        if st.session_state.uploaded_content:
            attach_resume = st.checkbox("📎 Include my resume with this message", key="attach_resume")
        else:
            attach_resume = False
    
    with col2:
        send_button = st.button("Send 💬", type="primary", use_container_width=True)
    
    # Handle sending message
    if send_button and user_input:
        # Prepare message content
        message_content = user_input
        if attach_resume and st.session_state.uploaded_content:
            message_content = f"{user_input}\n\nHere's my resume for context:\n{st.session_state.uploaded_content}"
        
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user",
            "content": message_content,
            "timestamp": datetime.now()
        })
        
        # Clear input and rerun to get response
        st.rerun()
    
    # Handle Enter key press
    if user_input and user_input != st.session_state.get("last_input", ""):
        st.session_state.last_input = user_input
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"""
        <div style="text-align: center; color: #666666; font-size: 0.8rem;">
            <p>💬 Career Buddy Chat - Powered by Azure OpenAI | 
            Messages: {len(st.session_state.messages)} | 
            Model: {model_name}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()