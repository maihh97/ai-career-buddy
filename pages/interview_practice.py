import streamlit as st
import streamlit.components.v1 as components
import openai
import os
from dotenv import load_dotenv
from typing import Optional, List, Dict
from datetime import datetime
import asyncio
import json
import time
import uuid
import requests
import logging

# Azure Cognitive Services imports
try:
    import azure.cognitiveservices.speech as speechsdk
    from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer, AudioConfig
    from azure.cognitiveservices.speech import SpeechRecognizer, ResultReason
    SPEECH_SDK_AVAILABLE = True
except ImportError:
    SPEECH_SDK_AVAILABLE = False

# Load environment variables
load_dotenv()

# Azure Avatar Configuration
SPEECH_ENDPOINT = os.getenv('SPEECH_ENDPOINT', 'https://eastus2.api.cognitive.microsoft.com')
AVATAR_API_VERSION = '2024-04-15-preview'

# Interview Practice Configuration
INTERVIEW_COACH_SYSTEM_PROMPT = """
You are an Expert Interview Coach and Hiring Manager with 15+ years of experience. Your role is to:

1. **Conduct Realistic Mock Interviews**: 
   - Ask industry-appropriate questions based on job role, experience level, and company type
   - Follow natural interview flow with follow-up questions
   - Adapt difficulty based on candidate responses
   - Include various question types: behavioral, technical, situational, cultural fit

2. **Provide Detailed Feedback**:
   - Rate responses on content, clarity, confidence, and relevance (1-10 scale)
   - Give specific improvement suggestions
   - Highlight strengths and areas to develop
   - Suggest better ways to structure answers (STAR method for behavioral questions)

3. **Question Categories**:
   - **Opening**: "Tell me about yourself", "Why this role/company?"
   - **Behavioral**: "Tell me about a time when...", "How did you handle..."
   - **Technical**: Role-specific skills and knowledge
   - **Situational**: "What would you do if...", problem-solving scenarios
   - **Closing**: "Questions for us?", "Why should we hire you?"

4. **Interview Modes**:
   - **Practice Mode**: One question at a time with immediate feedback
   - **Full Interview**: Complete 30-45 minute interview simulation
   - **Quick Prep**: 5-10 common questions rapid fire

Always maintain a professional, encouraging tone. Provide constructive feedback that helps candidates improve while building their confidence.
Keep the interview realistic and professional, matching the tone and expectations of real hiring managers.

**Important: Your response will be read by Speech services so don't return a lot of symbols like !, ?, etc.**
"""

class InterviewPracticeEngine:
    def __init__(self):
        self.openai_client = None
        self.speech_config = None
        self.synthesizer = None
        self.recognizer = None
        self.audio_config = None
        self.tts_task = None
        self.is_speaking = False
        
        # Avatar configuration
        self.avatar_enabled = False
        self.avatar_character = "lisa"  # Default avatar
        self.avatar_style = "casual-sitting"  # Default style
        
        # Speech control
        self.should_stop_speech = False
        
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize Azure OpenAI and Speech services clients"""
        try:
            # Initialize Azure OpenAI
            azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            api_key = os.getenv("AZURE_OPENAI_API_KEY")
            api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
            
            if azure_endpoint and api_key:
                self.openai_client = openai.AzureOpenAI(
                    azure_endpoint=azure_endpoint,
                    api_key=api_key,
                    api_version=api_version
                )
            
            # Initialize Azure Speech Services
            if SPEECH_SDK_AVAILABLE:
                speech_key = os.getenv("AZURE_SPEECH_KEY")
                speech_region = os.getenv("AZURE_SPEECH_REGION")
                
                if speech_key and speech_region:
                    self.speech_config = speechsdk.SpeechConfig(
                        subscription=speech_key, 
                        region=speech_region
                    )
                    
                    # Configure speech synthesis
                    self.speech_config.speech_synthesis_voice_name = "en-US-AriaNeural"
                    self.synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)
                    
                    # Configure speech recognition language
                    self.speech_config.speech_recognition_language = "en-US"
                    
                    # Configure speech recognition timeouts for longer responses
                    self.speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "5000")
                    self.speech_config.set_property(speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs, "5000")
                    
                    # Don't create persistent recognizer - create fresh one for each recognition
            
        except Exception as e:
            st.error(f"Error initializing services: {str(e)}")
    
    def get_interview_response(self, messages: List[Dict], model_name: str = "gpt-4") -> str:
        """Get response from interview coach"""
        if not self.openai_client:
            return "Interview coach is not available. Please check your Azure OpenAI configuration."
        
        try:
            response = self.openai_client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.5,  # Slightly higher for more varied questions
                max_tokens=500
            )
            
            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content or "No response generated."
            else:
                return "No response received. Please try again."
                
        except Exception as e:
            return f"Error getting interview response: {str(e)}"
    
    def text_to_speech(self, text: str) -> bool:
        """Convert text to speech using Azure TTS"""
        if not self.synthesizer:
            st.error("Azure Text-to-Speech not available. Please check your configuration.")
            return False
        
        try:
            self.is_speaking = True
            self.should_stop_speech = False
            
            # Start synthesis asynchronously
            self.tts_task = self.synthesizer.speak_text_async(text)
            
            # Poll for completion or stop signal
            import threading
            import time as time_module
            
            def check_completion():
                try:
                    result = self.tts_task.get()
                    return result
                except:
                    return None
            
            # Wait with interruption capability
            start_time = time_module.time()
            while time_module.time() - start_time < 30:  # 30 second timeout
                if self.should_stop_speech:
                    # User requested stop - cancel task
                    try:
                        self.synthesizer.stop_speaking_async()
                    except:
                        pass
                    return False
                
                # Check if task is complete
                if self.tts_task and hasattr(self.tts_task, 'get'):
                    try:
                        # Non-blocking check
                        result = self.tts_task.get()
                        if result:
                            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                                return True
                            elif result.reason == speechsdk.ResultReason.Canceled:
                                cancellation_details = result.cancellation_details
                                if cancellation_details.reason != speechsdk.CancellationReason.EndOfStream:
                                    if not self.should_stop_speech:
                                        st.warning(f"Speech synthesis stopped: {cancellation_details.reason}")
                                return False
                            else:
                                return False
                    except:
                        # Task not ready yet, continue waiting
                        pass
                
                # Brief pause
                time_module.sleep(0.2)
            
            # Timeout reached
            return False
                
        except Exception as e:
            if not self.should_stop_speech:
                st.error(f"Text-to-speech error: {str(e)}")
            return False
        finally:
            self.is_speaking = False
            self.tts_task = None
            self.should_stop_speech = False
    
    def stop_speech(self) -> bool:
        """Stop ongoing text-to-speech"""
        try:
            if self.is_speaking or self.tts_task:
                # Set stop flag to interrupt the polling loop
                self.should_stop_speech = True
                
                # Try to stop the synthesizer directly
                if self.synthesizer:
                    try:
                        # This is the correct method for Azure Speech SDK
                        self.synthesizer.stop_speaking_async()
                    except Exception as e:
                        # If direct stop fails, try recreating the synthesizer
                        try:
                            if self.speech_config:
                                # Close and recreate synthesizer to force stop
                                old_synthesizer = self.synthesizer
                                self.synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)
                                try:
                                    old_synthesizer.close()
                                except:
                                    pass
                        except:
                            pass
                
                # Clean up task
                if self.tts_task:
                    try:
                        self.tts_task = None
                    except:
                        pass
                
                # Reset state immediately
                self.is_speaking = False
                
                return True
            return False
        except Exception as e:
            st.error(f"Error stopping speech: {str(e)}")
            # Force reset state even if there's an error
            self.should_stop_speech = True
            self.is_speaking = False
            self.tts_task = None
            return False
    
    def text_to_speech_avatar(self, text: str, avatar_enabled: bool = True) -> bool:
        """Convert text to speech with avatar if enabled, fallback to audio-only"""
        if avatar_enabled and SPEECH_SDK_AVAILABLE:
            return self._synthesize_with_avatar(text)
        else:
            return self.text_to_speech(text)
    
    def _synthesize_with_avatar(self, text: str) -> bool:
        """Private method to handle Azure Avatar batch synthesis"""
        try:
            # Display avatar interface while processing
            avatar_placeholder = st.empty()
            with avatar_placeholder.container():
                st.markdown("""
                <div style="
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 10px;
                    color: white;
                    text-align: center;
                ">
                    <div style="font-size: 48px; margin-bottom: 15px;">🎭</div>
                    <div style="font-size: 18px; font-weight: bold;">Interview Coach Avatar</div>
                    <div style="margin: 10px 0; font-size: 14px;">Generating personalized avatar response...</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Submit avatar synthesis job
            job_id = self._create_avatar_job_id()
            success = self._submit_avatar_synthesis(job_id, text)
            
            if success:
                # Monitor synthesis progress
                video_url = self._monitor_avatar_synthesis(job_id)
                
                if video_url == "SKIP_TO_AUDIO":
                    # User chose to skip to audio-only
                    avatar_placeholder.empty()
                    st.info("🔊 Continuing with audio-only as requested...")
                elif video_url:
                    # Display the generated avatar video
                    avatar_placeholder.empty()
                    try:
                        st.video(video_url)
                        st.success("✅ Avatar response generated successfully!")
                        # Add a small delay to ensure video loads
                        time.sleep(1)
                        return True
                    except Exception as e:
                        st.error(f"Failed to display video: {str(e)}")
                        st.info("🔊 Falling back to audio-only...")
                else:
                    avatar_placeholder.empty()
                    st.warning("⏰ Avatar synthesis taking longer than expected. Using audio-only.")
            else:
                avatar_placeholder.empty()
                st.warning("⚠️ Avatar synthesis failed. Using audio-only.")
            
            # Fallback to regular TTS
            return self.text_to_speech(text)
            
        except Exception as e:
            st.error(f"Avatar synthesis error: {str(e)}")
            # Fallback to regular TTS
            return self.text_to_speech(text)
    
    def _create_avatar_job_id(self) -> str:
        """Generate unique job ID for avatar synthesis"""
        return str(uuid.uuid4())
    
    def _authenticate_avatar_api(self) -> dict:
        """Authenticate with Azure Speech service for avatar synthesis"""
        subscription_key = os.getenv("AZURE_SPEECH_KEY")
        if subscription_key:
            return {'Ocp-Apim-Subscription-Key': subscription_key}
        else:
            st.error("Azure Speech key not found. Please check your configuration.")
            return {}
    
    def _submit_avatar_synthesis(self, job_id: str, text: str) -> bool:
        """Submit avatar synthesis job to Azure"""
        url = f'{SPEECH_ENDPOINT}/avatar/batchsyntheses/{job_id}?api-version={AVATAR_API_VERSION}'
        
        header = {
            'Content-Type': 'application/json'
        }
        header.update(self._authenticate_avatar_api())
        
        if not header.get('Ocp-Apim-Subscription-Key'):
            return False
        
        payload = {
            'synthesisConfig': {
                'voice': 'en-US-AvaMultilingualNeural',
            },
            'inputKind': 'plainText',
            'inputs': [
                {
                    'content': text[:1000],  # Limit text length for demo
                },
            ],
            'avatarConfig': {
                'customized': False,
                'talkingAvatarCharacter': self.avatar_character or 'Lisa',
                'talkingAvatarStyle': self.avatar_style or 'casual-sitting',
                'videoFormat': 'mp4',
                'videoCodec': 'h264',
                'subtitleType': 'soft_embedded',
                'backgroundColor': '#FFFFFFFF',
            }
        }
        
        try:
            response = requests.put(url, json.dumps(payload), headers=header, timeout=30)
            if response.status_code < 400:
                st.success(f"✅ Avatar synthesis job submitted successfully (ID: {job_id[:8]}...)")
                return True
            else:
                st.error(f"❌ Failed to submit avatar synthesis: [{response.status_code}] {response.text[:200]}...")
                return False
        except requests.RequestException as e:
            st.error(f"❌ Request failed: {str(e)}")
            return False
    
    def _monitor_avatar_synthesis(self, job_id: str, timeout: int = 180) -> Optional[str]:
        """Monitor avatar synthesis job and return video URL when complete"""
        url = f'{SPEECH_ENDPOINT}/avatar/batchsyntheses/{job_id}?api-version={AVATAR_API_VERSION}'
        header = self._authenticate_avatar_api()
        
        if not header.get('Ocp-Apim-Subscription-Key'):
            return None
        
        start_time = time.time()
        progress_bar = st.progress(0, text="🎭 Generating avatar video...")
        
        # Create placeholders for skip button
        skip_container = st.empty()
        # Create unique button key using timestamp and job_id
        button_key = f"skip_avatar_{job_id}_{int(start_time * 1000)}"
        
        try:
            while time.time() - start_time < timeout:
                response = requests.get(url, headers=header, timeout=10)
                
                if response.status_code < 400:
                    job_data = response.json()
                    status = job_data.get('status', 'Unknown')
                    
                    # Update progress
                    elapsed = time.time() - start_time
                    progress = min(elapsed / timeout, 0.95)
                    progress_bar.progress(progress, text=f"🎭 Status: {status}...")
                    
                    # Show skip button after 15 seconds
                    if elapsed > 15:
                        with skip_container.container():
                            st.markdown("---")
                            col1, col2, col3 = st.columns([1, 2, 1])
                            with col2:
                                if st.button("⏭️ Skip to Audio-Only", 
                                           type="secondary", 
                                           use_container_width=True,
                                           key=button_key,
                                           help="Stop waiting for avatar and use regular text-to-speech instead"):
                                    progress_bar.empty()
                                    skip_container.empty()
                                    st.info("🔊 Switching to audio-only mode...")
                                    return "SKIP_TO_AUDIO"
                            st.caption("🎭 Avatar generation can take 1-3 minutes. You can continue with audio-only if needed.")
                    
                    if status == 'Succeeded':
                        video_url = job_data.get('outputs', {}).get('result')
                        progress_bar.progress(1.0, text="✅ Avatar video ready!")
                        skip_container.empty()
                        time.sleep(1)  # Brief pause to show completion
                        progress_bar.empty()
                        return video_url
                    elif status == 'Failed':
                        error_detail = job_data.get('error', {}).get('message', 'Unknown error')
                        st.error(f"❌ Avatar synthesis failed: {error_detail}")
                        progress_bar.empty()
                        skip_container.empty()
                        return None
                    
                    # Wait before next check
                    time.sleep(3)
                else:
                    st.error(f"❌ Failed to check synthesis status: {response.text[:200]}...")
                    progress_bar.empty()
                    skip_container.empty()
                    return None
            
            # Timeout reached
            progress_bar.empty()
            skip_container.empty()
            st.warning("⏰ Avatar synthesis timeout. This may take longer for complex requests.")
            return None
            
        except requests.RequestException as e:
            progress_bar.empty()
            skip_container.empty()
            st.error(f"❌ Monitoring failed: {str(e)}")
            return None
    
    def speech_to_text(self) -> Optional[str]:
        """Convert speech to text using Azure STT"""
        if not self.speech_config:
            st.error("Azure Speech-to-Text not available. Please check your configuration.")
            return None
        
        # Create a fresh recognizer for each recognition to avoid state issues
        recognizer = None
        try:
            # Create new recognizer instance
            recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config)
            
            st.info("🎤 Listening... Speak now! Take your time to give a complete answer.")
            
            # Use recognize_once_async with timeout for better control
            result = recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                if result.text and result.text.strip():
                    return result.text.strip()
                else:
                    st.warning("No speech was detected. Please try again.")
                    return None
            elif result.reason == speechsdk.ResultReason.NoMatch:
                st.warning("No speech could be recognized. Please speak clearly and try again.")
                return None
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    st.error(f"Speech recognition error: {cancellation_details.error_details}")
                else:
                    st.warning("Speech recognition was canceled.")
                return None
            else:
                st.warning("Unexpected result from speech recognition.")
                return None
                
        except Exception as e:
            st.error(f"Speech-to-text error: {str(e)}")
            return None
        
        finally:
            # Clean up the recognizer
            if recognizer:
                try:
                    recognizer = None
                except:
                    pass

def initialize_interview_session():
    """Initialize interview session state"""
    if "interview_messages" not in st.session_state:
        st.session_state.interview_messages = []
    
    if "interview_engine" not in st.session_state:
        st.session_state.interview_engine = InterviewPracticeEngine()
    
    if "interview_mode" not in st.session_state:
        st.session_state.interview_mode = "practice"
    
    if "current_question" not in st.session_state:
        st.session_state.current_question = None
    
    if "interview_started" not in st.session_state:
        st.session_state.interview_started = False
    
    if "question_count" not in st.session_state:
        st.session_state.question_count = 0
    
    if "interview_scores" not in st.session_state:
        st.session_state.interview_scores = []
    
    if "is_speaking" not in st.session_state:
        st.session_state.is_speaking = False

def display_interview_message(message, is_user=False):
    """Display interview message with styling"""
    if is_user:
        st.markdown(
            f"""
            <div style="
                display: flex;
                justify-content: flex-end;
                margin: 1rem 0;
            ">
                <div style="
                    background-color: #2E8B57;
                    color: white;
                    padding: 0.75rem 1rem;
                    border-radius: 1rem 1rem 0.25rem 1rem;
                    max-width: 70%;
                    word-wrap: break-word;
                ">
                    <strong>🎯 You:</strong><br>{message['content']}
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
                    background-color: #4A4A4A;
                    color: white;
                    padding: 0.75rem 1rem;
                    border-radius: 1rem 1rem 1rem 0.25rem;
                    max-width: 70%;
                    word-wrap: break-word;
                    border-left: 3px solid #FFA500;
                ">
                    <strong>👨‍💼 Interviewer:</strong><br>{message['content']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

def get_job_specific_context(job_role, experience_level, company_type):
    """Generate job-specific context for the interview"""
    return f"""
    Interview Context:
    - Job Role: {job_role}
    - Experience Level: {experience_level}
    - Company Type: {company_type}
    
    Please conduct an interview appropriate for this role and level. Start with an opening question.
    """

def main():
    # Page configuration
    st.set_page_config(
        page_title="Interview Practice - Career Buddy",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session
    initialize_interview_session()
    
    # Header
    st.title("🎯 Interview Practice Studio")
    st.markdown("*Practice interviews with AI coaching, speech recognition, realistic avatars, and feedback*")
    
    # Navigation
    if st.button("← Back to Career Chat", type="secondary"):
        st.switch_page("career_buddy_chat.py")
    
    # Sidebar Configuration
    with st.sidebar:
        st.header("🎛️ Interview Setup")
        
        # Service Status
        st.subheader("Service Status")
        
        # Check Azure OpenAI
        if st.session_state.interview_engine.openai_client:
            st.success("✅ Azure OpenAI Connected")
        else:
            st.error("❌ Azure OpenAI Not Connected")
        
        # Check Azure Speech Services
        if SPEECH_SDK_AVAILABLE and st.session_state.interview_engine.speech_config:
            st.success("✅ Azure Speech Services Connected")
        else:
            st.error("❌ Azure Speech Services Not Available")
            st.info("Install: pip install azure-cognitiveservices-speech")
        
        st.markdown("---")
        
        # Interview Configuration
        st.subheader("Interview Configuration")
        
        job_role = st.selectbox(
            "Job Role",
            [
                "Software Engineer",
                "Data Scientist",
                "Product Manager", 
                "Marketing Manager",
                "Sales Representative",
                "Business Analyst",
                "UX Designer",
                "Project Manager",
                "Customer Success Manager",
                "Other"
            ]
        )
        
        if job_role == "Other":
            job_role = st.text_input("Specify job role:")
        
        experience_level = st.select_slider(
            "Experience Level",
            options=["Entry Level", "Mid Level", "Senior Level", "Executive Level"]
        )
        
        company_type = st.selectbox(
            "Company Type",
            [
                "Tech Startup",
                "Large Tech Company",
                "Fortune 500",
                "Small Business",
                "Non-Profit",
                "Government",
                "Consulting",
                "Healthcare",
                "Financial Services"
            ]
        )
        
        interview_mode = st.radio(
            "Interview Mode",
            [
                "Practice Mode (One question at a time)",
                "Full Interview (30-45 minutes)",
                "Quick Prep (5-10 questions)"
            ]
        )
        
        st.session_state.interview_mode = interview_mode
        
        st.markdown("---")
        
        # Model Selection
        st.subheader("AI Configuration")
        model_name = st.selectbox(
            "AI Model",
            ["gpt-4", "gpt-4-turbo", "gpt-35-turbo", "gpt-4o"],
            help="Choose your Azure OpenAI model"
        )
        
        # Audio Settings
        st.subheader("Audio Settings")
        use_speech = st.checkbox("Enable Speech-to-Text", value=True)
        use_tts = st.checkbox("Enable Text-to-Speech", value=True)
        
        # TTS Controls
        if use_tts and SPEECH_SDK_AVAILABLE:
            st.markdown("**Speech Controls:**")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🛑 Stop Speech", use_container_width=True, key="sidebar_stop_speech"):
                    if st.session_state.interview_engine.stop_speech():
                        st.success("Speech stopped!")
                    else:
                        st.info("No speech to stop")
            
            with col2:
                # Show speech status
                if st.session_state.interview_engine.is_speaking:
                    st.markdown("🔊 **Speaking...**")
                else:
                    st.markdown("🔇 *Silent*")
            
            # Avatar Settings
            st.markdown("** Avatar Settings:**")
            
            # Check if avatar prerequisites are met
            speech_key = os.getenv("AZURE_SPEECH_KEY")
            speech_endpoint = os.getenv('SPEECH_ENDPOINT') or SPEECH_ENDPOINT
            
            if not speech_key:
                st.warning("⚠️ Azure Speech Key required for Avatar functionality")
                use_avatar = False
            else:
                use_avatar = st.checkbox(
                    "Enable Avatar", 
                    value=False, 
                    help=f"Enable realistic avatar with speech synthesis.\nEndpoint: {speech_endpoint[:50]}..."
                )
            
            if use_avatar:
                col1, col2 = st.columns(2)
                with col1:
                    avatar_character = st.selectbox(
                        "Character",
                        ["lisa", "jason", "clara", "sarah", "nancy"],
                        help="Avatar character"
                    )
                
                with col2:
                    avatar_style = st.selectbox(
                        "Style",
                        ["casual-sitting", "business-standing", "professional-sitting"],
                        help="Avatar presentation style"
                    )
                
                # Update engine settings
                st.session_state.interview_engine.avatar_enabled = use_avatar
                st.session_state.interview_engine.avatar_character = avatar_character
                st.session_state.interview_engine.avatar_style = avatar_style
        
        st.markdown("---")
        
        # Interview Controls
        st.subheader("Interview Controls")
        
        if not st.session_state.interview_started:
            if st.button("🚀 Start Interview", type="primary", use_container_width=True):
                # Initialize interview
                context = get_job_specific_context(job_role, experience_level, company_type)
                st.session_state.interview_messages = [
                    {"role": "system", "content": INTERVIEW_COACH_SYSTEM_PROMPT + "\n" + context}
                ]
                st.session_state.interview_started = True
                st.session_state.question_count = 0
                st.rerun()
        else:
            if st.button("🔄 Reset Interview", type="secondary", use_container_width=True):
                st.session_state.interview_messages = []
                st.session_state.interview_started = False
                st.session_state.question_count = 0
                st.session_state.interview_scores = []
                st.rerun()
        
        if st.session_state.interview_started:
            st.info(f"Questions Asked: {st.session_state.question_count}")
            
            if st.session_state.interview_scores:
                avg_score = sum(st.session_state.interview_scores) / len(st.session_state.interview_scores)
                st.metric("Average Score", f"{avg_score:.1f}/10")
    
    # Main Interview Area
    if not st.session_state.interview_started:
        # Welcome Screen
        st.header("Welcome to Interview Practice Studio")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 🎯 Practice Mode
            - One question at a time
            - Immediate feedback
            - Perfect for targeting specific skills
            - Build confidence gradually
            """)
        
        with col2:
            st.markdown("""
            ### 🎪 Full Interview
            - Complete interview simulation
            - 30-45 minutes duration
            - Comprehensive evaluation
            - Real interview experience
            """)
        
        with col3:
            st.markdown("""
            ### ⚡ Quick Prep
            - 5-10 rapid questions
            - Fast feedback loop
            - Perfect for last-minute prep
            - Common questions focus
            """)
        
        st.markdown("---")
        
        st.markdown("""
        ### 🚀 Features Available:
        - **AI-Powered Questions**: Industry-specific questions tailored to your role
        - **Speech Recognition**: Answer questions by speaking naturally
        - **Text-to-Speech**: Hear questions read aloud
        - **🎭 Azure Avatar Beta**: Realistic AI interviewer with video responses
        - **Real-time Feedback**: Get scored feedback on every response
        - **Multiple Formats**: Behavioral, technical, and situational questions
        - **Progress Tracking**: Monitor your improvement over time
        """)
        
        # Show avatar status if configured
        if os.getenv("AZURE_SPEECH_KEY"):
            st.success("Azure Avatar functionality available!")
        else:
            st.info("💡 Add AZURE_SPEECH_KEY to .env file to enable Avatar features")
        
        st.info("👆 Configure your interview settings in the sidebar, then click 'Start Interview' to begin!")
        
    else:
        # Active Interview
        st.header(f"🎯 {interview_mode}")
        
        # Display conversation
        interview_container = st.container()
        
        # Show prominent stop button and visual indicator when speech is active
        if hasattr(st.session_state.interview_engine, 'is_speaking') and st.session_state.interview_engine.is_speaking:
            st.warning("🔊 AI is currently speaking...")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🛑 Stop AI Speech", type="primary", use_container_width=True, key="main_stop_button"):
                    st.session_state.interview_engine.stop_speech()
                    st.rerun()
        
        with interview_container:
            for message in st.session_state.interview_messages:
                if message["role"] in ["user", "assistant"]:
                    display_interview_message(message, is_user=(message["role"] == "user"))
        
        # Handle TTS for the latest assistant message if it hasn't been spoken yet
        if (st.session_state.interview_messages and 
            st.session_state.interview_messages[-1]["role"] == "assistant" and
            use_tts and SPEECH_SDK_AVAILABLE and
            not hasattr(st.session_state, 'last_spoken_message_id')):
            
            # Get the latest assistant message
            latest_message = st.session_state.interview_messages[-1]
            message_id = id(latest_message)  # Use object id as unique identifier
            
            # Check if this message has already been spoken
            if not hasattr(st.session_state, 'spoken_message_ids'):
                st.session_state.spoken_message_ids = set()
            
            if message_id not in st.session_state.spoken_message_ids:
                avatar_enabled = getattr(st.session_state.interview_engine, 'avatar_enabled', False)
                if avatar_enabled:
                    # Use avatar TTS
                    st.session_state.interview_engine.text_to_speech_avatar(latest_message['content'], True)
                else:
                    # Use regular TTS
                    st.session_state.interview_engine.text_to_speech(latest_message['content'])
                
                # Mark this message as spoken
                st.session_state.spoken_message_ids.add(message_id)
        
        # Generate first question if just started
        if len(st.session_state.interview_messages) == 1:  # Only system message
            with st.spinner("Interview coach is preparing your first question..."):
                first_question_prompt = "Please start the interview with an appropriate opening question."
                
                # Prepare clean API messages (only role and content, no timestamp)
                api_messages = [{"role": msg["role"], "content": msg["content"]} 
                               for msg in st.session_state.interview_messages 
                               if "role" in msg and "content" in msg]
                api_messages.append({"role": "user", "content": first_question_prompt})
                
                response = st.session_state.interview_engine.get_interview_response(api_messages, model_name)
                
                # Ensure we have a complete response before proceeding
                if response and response.strip():
                    st.session_state.interview_messages.append({
                        "role": "assistant",
                        "content": response,
                        "timestamp": datetime.now()
                    })
                    
                    st.session_state.question_count += 1
                    
                    # Force rerun to display the message before TTS
                    st.rerun()
                else:
                    st.error("Failed to generate opening question. Please try again.")
                    return
            
            # This will be handled after rerun in the TTS section below
        
        # Get user response if last message is from assistant
        if (st.session_state.interview_messages and 
            st.session_state.interview_messages[-1]["role"] == "assistant"):
            
            st.markdown("---")
            st.subheader("Your Response")
            
            # Response input methods
            response_method = st.radio(
                "How would you like to respond?",
                ["Type Response", "Speak Response"] if use_speech and SPEECH_SDK_AVAILABLE else ["Type Response"],
                horizontal=True
            )
            
            user_response = None
            
            if response_method == "Type Response":
                col1, col2 = st.columns([4, 1])
                with col1:
                    typed_response = st.text_area(
                        "Type your answer:",
                        height=100,
                        placeholder="Share your response here..."
                    )
                with col2:
                    st.write("")  # spacing
                    if st.button("Submit", type="primary"):
                        if typed_response.strip():
                            user_response = typed_response
            
            elif response_method == "Speak Response":
                # Initialize speech recording state
                if "is_recording" not in st.session_state:
                    st.session_state.is_recording = False
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    # Disable button while recording to prevent multiple concurrent calls
                    if st.button(
                        "🎤 Start Recording" if not st.session_state.is_recording else "🎤 Recording...", 
                        type="primary", 
                        use_container_width=True,
                        disabled=st.session_state.is_recording
                    ):
                        st.session_state.is_recording = True
                        try:
                            with st.spinner("🎤 Listening for your response... Speak now!"):
                                spoken_response = st.session_state.interview_engine.speech_to_text()
                                if spoken_response and spoken_response.strip():
                                    user_response = spoken_response
                                    st.success(f"✅ Recorded: {spoken_response[:100]}{'...' if len(spoken_response) > 100 else ''}")
                                else:
                                    st.warning("No speech was detected. Please try again.")
                        except Exception as e:
                            st.error(f"Recording failed: {str(e)}")
                        finally:
                            st.session_state.is_recording = False
                
                with col2:
                    st.info("💡 **Tips for better recognition:**\n- Speak clearly and at normal pace\n- Ensure good microphone access\n- Minimize background noise\n- Pause briefly when you finish speaking")
            
            # Process user response
            if user_response:
                # Add user message
                st.session_state.interview_messages.append({
                    "role": "user",
                    "content": user_response,
                    "timestamp": datetime.now()
                })
                
                # Get feedback and next question
                with st.spinner("Getting feedback and next question..."):
                    feedback_prompt = f"""
                    Please provide detailed feedback on this response and then ask the next appropriate interview question.
                    Your response will be read so don't return symbols like #, ?, / or any other non-verbal characters.
                    Response to evaluate: "{user_response}"
                    
                    Include:
                    1. Feedback with score (1-10) for content, clarity, and overall effectiveness
                    2. Specific improvement suggestions
                    3. What they did well
                    4. Next interview question appropriate for the flow
                    """
                    
                    # Prepare clean API messages (only role and content, no timestamp)
                    api_messages = [{"role": msg["role"], "content": msg["content"]} 
                                   for msg in st.session_state.interview_messages 
                                   if "role" in msg and "content" in msg]
                    api_messages.append({"role": "user", "content": feedback_prompt})
                    
                    coach_response = st.session_state.interview_engine.get_interview_response(api_messages, model_name)
                    
                    # Ensure we have a complete response before proceeding
                    if coach_response and coach_response.strip():
                        st.session_state.interview_messages.append({
                            "role": "assistant", 
                            "content": coach_response,
                            "timestamp": datetime.now()
                        })
                        
                        st.session_state.question_count += 1
                        
                        # Extract score if present (simple regex for score tracking)
                        import re
                        score_match = re.search(r'score[:\s]*([0-9]+)', coach_response.lower())
                        if score_match:
                            score = int(score_match.group(1))
                            st.session_state.interview_scores.append(score)
                        
                        # Force rerun to display the message before TTS
                        st.rerun()
                    else:
                        st.error("Failed to generate feedback. Please try again.")

if __name__ == "__main__":
    main()