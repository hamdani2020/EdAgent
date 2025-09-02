# EdAgent - AI-Powered Career Coaching Assistant

EdAgent is a conversational AI system designed to help beginners learn new skills and advance their careers through personalized guidance, skill assessments, and curated educational content recommendations.

## Project Structure

```
edagent/
├── __init__.py                 # Main package initialization
├── models/                     # Data models and schemas
│   └── __init__.py
├── services/                   # Business logic services
│   └── __init__.py
├── interfaces/                 # Abstract base classes and interfaces
│   ├── __init__.py
│   ├── ai_interface.py
│   ├── user_context_interface.py
│   ├── content_interface.py
│   └── conversation_interface.py
├── api/                        # REST API and WebSocket endpoints
│   └── __init__.py
├── database/                   # Database models and connection management
│   └── __init__.py
└── config/                     # Configuration and environment management
    ├── __init__.py
    ├── settings.py
    └── environment.py
```

## Setup

1. Copy `.env.example` to `.env` and configure your API keys:
   ```bash
   cp .env.example .env
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your environment variables in `.env`:
   - `GEMINI_API_KEY`: Your Google Gemini API key ([Get it here](https://makersuite.google.com/app/apikey))
   - `YOUTUBE_API_KEY`: Your YouTube Data API key ([Get it here](https://console.developers.google.com/))
   - `SECRET_KEY`: A secure secret key for session management (generate with `openssl rand -hex 32`)

### Getting API Keys

#### Google Gemini API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key to your `.env` file

#### YouTube Data API Key
1. Go to the [Google Cloud Console](https://console.developers.google.com/)
2. Create a new project or select an existing one
3. Enable the YouTube Data API v3
4. Go to "Credentials" and create an API key
5. Copy the key to your `.env` file

## Features

### Core AI Capabilities
- **Conversational AI**: Natural language interactions powered by Google Gemini
- **Skill Assessment**: Comprehensive evaluation of technical and soft skills
- **Learning Path Generation**: Personalized roadmaps based on goals and current skills
- **Content Recommendation**: Curated resources from YouTube and educational platforms
- **Career Coaching**: Resume analysis, interview preparation, and career guidance

### User Interface
- **Streamlit Web App**: Comprehensive web interface with interactive components
- **Real-time Chat**: WebSocket-powered live conversations with EdAgent
- **Interactive Dashboards**: Progress tracking, analytics, and learning insights
- **Mobile-Friendly**: Responsive design that works on all devices

### Technical Features
- **REST API**: Complete FastAPI backend with comprehensive endpoints
- **WebSocket Support**: Real-time bidirectional communication
- **Privacy Controls**: Comprehensive data management and privacy features
- **Docker Support**: Containerized deployment with Docker Compose

## Quick Start

### Option 1: Run Both Backend and Frontend
```bash
# Start both FastAPI backend and Streamlit frontend
python run_app.py
```

### Option 2: Run Components Separately
```bash
# Terminal 1: Start FastAPI backend
uvicorn main:app --reload

# Terminal 2: Start Streamlit frontend
./scripts/start_frontend.sh
```

### Option 3: Demo Mode (Frontend Only)
```bash
# Run Streamlit with mock data (no backend required)
./scripts/start_demo.sh
```

### Access Points
- **Streamlit Frontend**: http://localhost:8501
- **FastAPI Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Configuration

The application uses environment-based configuration with support for:
- Development, testing, staging, and production environments
- Streamlit frontend configuration
- WebSocket and real-time features
- Configurable AI model parameters
- Database connection settings
- Rate limiting and security options
- Logging configuration

## Architecture

EdAgent follows a modular architecture with clear separation of concerns:

- **Models**: Data structures and validation
- **Services**: Business logic and external integrations
- **Interfaces**: Abstract contracts for service implementations
- **API**: HTTP endpoints and WebSocket connections
- **Database**: Data persistence and migrations
- **Config**: Environment and application settings

## Development

This project follows Python best practices:
- Type hints for all functions and methods
- Async/await for I/O operations
- Comprehensive error handling
- Unit testing with pytest
- Code formatting with black and isort
- Linting with flake8 and mypy

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions, please:
- Check the [documentation](docs/)
- Search existing [issues](https://github.com/your-username/edagent/issues)
- Create a new issue if needed

## Acknowledgments

- Google Gemini API for conversational AI capabilities
- YouTube Data API for educational content discovery
- The open source community for the amazing tools and libraries that make this project possible