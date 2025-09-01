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
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `YOUTUBE_API_KEY`: Your YouTube Data API key
   - `SECRET_KEY`: A secure secret key for session management

## Configuration

The application uses environment-based configuration with support for:
- Development, testing, staging, and production environments
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