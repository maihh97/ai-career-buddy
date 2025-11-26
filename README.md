# Career Buddy - AI Career Assistant 👔

A Streamlit-powered career coaching application that uses Microsoft Agent Framework and Azure OpenAI to provide intelligent career guidance, resume analysis, and job search support.

## Features

- 📄 **Resume Analysis**: Upload and analyze resumes for content quality, ATS compatibility, and improvement suggestions
- 🎯 **Career Guidance**: Get personalized career advice and development recommendations
- 💼 **Job Search Support**: Strategies for job hunting, interview preparation, and networking
- 📝 **Interview Preparation**: Tips and guidance for successful interviews
- 🔗 **LinkedIn Optimization**: Advice for improving your professional online presence
- 💰 **Salary Negotiation**: Guidance on compensation discussions
- 🎭 **Avatar Interview Practice** (NEW!): Realistic interview practice with AI avatars, speech recognition, and audio feedback

## Prerequisites

- Python 3.8 or higher
- Microsoft Foundry (formerly Azure AI Foundry) project with a deployed language model
- Azure credentials configured

## Setup Instructions

### 1. Install Dependencies

**Important**: The Microsoft Agent Framework is currently in preview, so the `--pre` flag is required:

```bash
pip install agent-framework-azure-ai --pre
pip install -r requirements.txt
```

### 2. Configure Azure Resources

1. **Create a Microsoft Foundry Project**:
   - Go to [Microsoft Foundry](https://ai.azure.com)
   - Create a new project or use an existing one
   - Note your project endpoint URL

2. **Deploy a Language Model**:
   - In your Foundry project, go to the Model Catalog
   - Deploy a model (recommended: GPT-4, GPT-4o, or similar)
   - Note the deployment name

3. **Set up Authentication**:
   - Ensure you have Azure credentials configured
   - Options include: Azure CLI (`az login`), service principal, or managed identity

### 3. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` file with your actual values:
   ```bash
   AZURE_AI_PROJECT_ENDPOINT=https://your-project.westus2.api.azureml.ms
   AZURE_AI_MODEL_DEPLOYMENT=gpt-4
   ```

### 4. Run the Application

```bash
streamlit run career_buddy_app.py
```

The application will be available at `http://localhost:8501`

## Usage Guide

### Uploading Resumes

1. **File Upload**: Support for `.txt`, `.pdf`, `.doc`, and `.docx` files
   - Text files are read directly
   - For PDF/Word documents, copy and paste the content into the text area

2. **Direct Input**: Paste resume content directly into the text area

### Asking Questions

Choose from predefined questions or ask custom questions:

- "Analyze my resume and provide feedback"
- "What skills should I develop for my career?"
- "Help me prepare for job interviews"
- "Review my resume for ATS compatibility"
- And more...

### Getting Responses

Career Buddy will analyze your query and any uploaded content to provide:
- Detailed feedback and suggestions
- Actionable advice
- Industry-specific guidance
- Best practices and tips

## 🎭 Avatar Interview Practice

The new Avatar Interview Practice feature provides a realistic interview experience with:

### Features
- **Realistic AI Avatars**: Visual representation of an interview coach
- **Speech Recognition**: Speak your answers naturally using Azure Speech-to-Text
- **Text-to-Speech**: Hear questions and feedback with Azure neural voices
- **Interactive Experience**: Real-time avatar animations and visual feedback
- **Customizable Characters**: Choose from different avatar personalities and styles

### Setup for Avatar Features

1. **Azure Speech Services**:
   ```bash
   # Add to your .env file
   AZURE_SPEECH_KEY=your_speech_key_here
   AZURE_SPEECH_REGION=your_region  # e.g., eastus, westus2
   ```

2. **Install Speech SDK**:
   ```bash
   pip install azure-cognitiveservices-speech
   ```

### Using Avatar Interview Practice

1. Navigate to the Interview Practice page
2. Configure your interview settings (job role, experience level)
3. Enable Avatar mode in the sidebar
4. Choose your preferred avatar character and style
5. Start the interview and interact using speech or text

### Avatar Characters Available
- **Lisa**: Professional, casual-sitting style
- **Jason**: Business professional, standing pose
- **Clara**: Friendly interviewer, professional setting
- **Sarah**: Senior manager persona
- **Nancy**: Technical interviewer specialist

## Architecture

The application uses:

- **Microsoft Agent Framework**: For AI agent orchestration and management
- **Azure OpenAI**: For intelligent language processing
- **Azure Speech Services**: For text-to-speech and speech recognition
- **Azure Text-to-Speech Avatar**: For realistic visual interview experience
- **Streamlit**: For the web interface with HTML components for avatar display
- **Azure Identity**: For secure authentication

## Security Considerations

- Never commit `.env` files with credentials to version control
- The application processes uploaded files locally and securely
- All AI processing happens through encrypted connections to Azure
- Consider data privacy when uploading sensitive resume information

## Troubleshooting

### Common Issues

1. **"Microsoft Agent Framework not installed"**:
   ```bash
   pip install agent-framework-azure-ai --pre
   ```

2. **"Azure endpoint not configured"**:
   - Check your `.env` file
   - Ensure `AZURE_AI_PROJECT_ENDPOINT` is set correctly

3. **Authentication errors**:
   - Run `az login` to authenticate with Azure CLI
   - Verify your Azure credentials have access to the Foundry project

4. **Model deployment issues**:
   - Verify the model is deployed in your Foundry project
   - Check that `AZURE_AI_MODEL_DEPLOYMENT` matches your deployment name

### Getting Help

- Check the [Microsoft Agent Framework documentation](https://github.com/microsoft/agent-framework)
- Review [Azure OpenAI documentation](https://docs.microsoft.com/azure/cognitive-services/openai/)
- Ensure your Azure subscription has the necessary permissions

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is provided as-is for educational and development purposes.