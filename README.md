# AI Career Buddy - Career Coaching Platform [WIP]

A comprehensive Streamlit-powered career coaching platform featuring advanced AI chat assistance and immersive interview practice with Azure Text-to-Speech Avatars. Built with Azure OpenAI and Azure Speech Services for a complete career development experience.

## Main Features

### **AI Career Chat Assistant**
- **Intelligent Resume Analysis**: Upload and analyze resumes (.pdf, .docx, .txt) with detailed feedback
- **Career Guidance**: Personalized career advice and development roadmaps
- **Job Search Strategy**: Comprehensive job hunting strategies and market insights
- **LinkedIn Optimization**: Professional profile enhancement recommendations
- **Salary Negotiation**: Compensation discussion strategies and market data
- **Interactive Chat**: Ongoing conversational support with context awareness

### **Advanced Interview Practice Studio**
- **Azure Avatar Integration**: Realistic AI interviewer with video responses
- **Speech Recognition**: Natural voice interaction with Azure Speech-to-Text
- **Text-to-Speech**: Neural voice synthesis for questions and feedback
- **Real-time Scoring**: Instant feedback with performance metrics
- **Multiple Interview Modes**: Practice, Full Interview, and Quick Prep options
- **Customizable Experience**: Job role-specific questions and difficulty levels

## Prerequisites

- **Python**: 3.8 or higher
- **Azure OpenAI**: Deployed GPT-4/GPT-4o model
- **Azure Speech Services**: For avatar and speech features (optional)
- **Azure Credentials**: Properly configured authentication

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/maihh97/ai-career-buddy.git
cd ai-career-buddy
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Edit the `.env` file in the root directory:
```bash
# Required - Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_API_VERSION=your_api_version
AZURE_OPENAI_DEPLOYMENT_NAME=your_model_name

# Optional - For Avatar Interview Practice
AZURE_SPEECH_KEY=your_speech_key_here
AZURE_SPEECH_REGION=your_speech_region
SPEECH_ENDPOINT=https://<speech_region>.api.cognitive.microsoft.com
```

### 3. Launch Application

```bash
streamlit run career_buddy_chat.py
```

**Access**: Open [http://localhost:8501](http://localhost:8501)

## User Guide

### **Career Chat Assistant**

**Main Chat Interface (`career_buddy_chat.py`)**
- **File Upload**: Drag & drop resumes (PDF, DOCX, TXT formats)
- **Quick Actions**: Pre-built prompts for common career questions
- **Smart Conversation**: Context-aware discussions about your career
- **Document Analysis**: Real-time resume parsing and feedback

**Sample Conversations:**
- "Analyze my resume for this software engineer position"
- "What skills should I develop for data science?"
- "Help me prepare for behavioral interviews"
- "Review my LinkedIn profile strategy"

### **Interview Practice Studio**

**Advanced Practice Mode (`pages/interview_practice.py`)**

#### Configuration Options:
- **Job Roles**: Software Engineer, Data Scientist, Product Manager, etc.
- **Experience Levels**: Entry, Mid, Senior, Executive
- **Company Types**: Startup, Tech Giant, Fortune 500, etc.
- **Interview Modes**: Practice (1-on-1), Full Interview, Quick Prep

#### Interactive Features:
- ** Voice Input**: Speak your answers naturally
- ** Audio Feedback**: Hear questions and feedback
- ** Avatar Mode**: Visual AI interviewer with video responses
- ** Scoring System**: Real-time performance metrics
- **⏭ Skip Options**: Flexible pacing controls

## Architecture

### **Core Technologies**
- **Frontend**: Streamlit with interactive components and responsive design
- **AI Engine**: Azure OpenAI (GPT-4/GPT-4o) for intelligent conversations
- **Speech Processing**: Azure Speech Services (STT/TTS/Avatar)
- **Document Processing**: PyPDF, python-docx for resume parsing
- **Authentication**: Environment-based configuration

### **Application Structure**
```
ai-career-buddy/
├── career_buddy_chat.py      # Main chat interface
├── pages/
│   └── interview_practice.py # Interview practice studio
├── requirements.txt          # Dependencies
├── .env                     # Configuration
└── README.md               # Documentation
```

### **Azure Services Integration**
- **Azure OpenAI**: Chat completions and intelligent responses
- **Azure Speech-to-Text**: Voice input processing
- **Azure Text-to-Speech**: Neural voice synthesis
- **Azure Avatar API**: Video-based AI interviewer synthesis

### **Documentation**
- **Azure OpenAI**: [Documentation](https://docs.microsoft.com/azure/cognitive-services/openai/)
- **Azure Speech**: [Speech Services Docs](https://docs.microsoft.com/azure/cognitive-services/speech-service/)
- **Streamlit**: [Community Forum](https://discuss.streamlit.io/)

## **Future Roadmap**

- [ ] **Multi-language Support**: Interview practice in multiple languages
- [ ] **Advanced Analytics**: Detailed performance tracking and trends
- [ ] **Team Features**: Collaborative interview preparation
- [ ] **Mobile App**: Native mobile experience
- [ ] **API Integration**: Connect with job boards and ATS systems
