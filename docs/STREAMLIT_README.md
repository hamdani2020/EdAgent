# EdAgent Streamlit Frontend

A comprehensive web interface for the EdAgent AI-powered career coaching assistant, built with Streamlit.

## 🌟 Features

### Core Functionality
- **💬 Real-time Chat Interface**: Interactive chat with EdAgent using WebSocket connections
- **📊 Skill Assessments**: Comprehensive skill evaluation with interactive widgets
- **🛤️ Learning Path Builder**: Personalized learning roadmaps with milestone tracking
- **👤 User Profile Management**: Complete profile customization and preferences
- **🔒 Privacy Controls**: Data export, deletion, and privacy settings management
- **📈 Analytics Dashboard**: Progress tracking and learning analytics visualization

### Advanced Features
- **🎤 Interview Preparation**: Practice questions and interview coaching
- **📄 Resume Analysis**: AI-powered resume feedback and optimization
- **🗺️ Career Roadmaps**: Visual career progression paths
- **📚 Resource Recommendations**: Personalized learning resource suggestions
- **🏆 Achievement System**: Gamified learning progress tracking
- **🔥 Learning Streaks**: Motivation through streak tracking

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- FastAPI backend running on `http://localhost:8000`
- Required Python packages (see `streamlit_requirements.txt`)

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r streamlit_requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export EDAGENT_API_URL="http://localhost:8000/api/v1"
   export EDAGENT_WS_URL="ws://localhost:8000/api/v1/ws"
   export USE_MOCK_DATA="true"  # For development/demo
   ```

3. **Run the application:**
   ```bash
   streamlit run streamlit_app.py
   ```

4. **Or use the startup script:**
   ```bash
   python run_app.py
   ```

### Docker Deployment

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose -f docker-compose.frontend.yml up --build
   ```

2. **Access the application:**
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 📱 User Interface

### Main Navigation
The application features a tabbed interface with the following sections:

1. **💬 Chat**: Real-time conversation with EdAgent
2. **📊 Assessments**: Skill evaluation and testing
3. **🛤️ Learning Paths**: Personalized learning roadmaps
4. **👤 Profile**: User profile and preferences management
5. **🔒 Privacy**: Data management and privacy controls
6. **📈 Analytics**: Progress tracking and insights
7. **🎤 Interview Prep**: Interview preparation tools
8. **📄 Resume Help**: Resume analysis and improvement

### Authentication
- Simple user ID-based authentication
- Session management with JWT tokens
- User registration with preferences setup
- Secure API communication

## 🔧 Configuration

### Environment Variables
```bash
# API Configuration
EDAGENT_API_URL=http://localhost:8000/api/v1
EDAGENT_WS_URL=ws://localhost:8000/api/v1/ws

# Development Settings
USE_MOCK_DATA=true  # Enable mock data for development
```

### Feature Flags
Configure features in `streamlit_config.py`:
```python
FEATURES = {
    "websocket_chat": True,
    "real_time_updates": True,
    "file_upload": True,
    "data_export": True,
    "analytics_dashboard": True,
    "interview_prep": True,
    "resume_analysis": True
}
```

## 🏗️ Architecture

### File Structure
```
├── streamlit_app.py           # Main application entry point
├── streamlit_config.py        # Configuration and settings
├── streamlit_components.py    # Custom UI components
├── streamlit_websocket.py     # WebSocket client implementation
├── streamlit_requirements.txt # Python dependencies
├── run_app.py                # Startup script for both backend and frontend
├── Dockerfile.streamlit      # Docker configuration for frontend
└── docker-compose.frontend.yml # Complete application stack
```

### Key Components

#### `streamlit_app.py`
- Main application logic
- Page routing and navigation
- Session state management
- API integration

#### `streamlit_components.py`
- Reusable UI components
- Interactive widgets
- Data visualization components
- Form handlers

#### `streamlit_websocket.py`
- WebSocket client implementation
- Real-time message handling
- Connection management
- Async/sync bridge for Streamlit

#### `streamlit_config.py`
- Application configuration
- Feature flags
- Mock data for development
- API settings

## 🎨 UI Components

### Chat Interface
- Real-time messaging with WebSocket support
- Message history with user/assistant distinction
- Quick action buttons for common tasks
- Typing indicators and response streaming

### Assessment Widgets
- Interactive skill assessment forms
- Progress tracking and scoring
- Question generation and response handling
- Results visualization

### Learning Path Builder
- Step-by-step path creation wizard
- Milestone tracking and progress bars
- Resource recommendations
- Timeline and difficulty estimation

### Analytics Dashboard
- Progress metrics and KPIs
- Interactive charts and visualizations
- Activity heatmaps
- Achievement tracking

## 🔌 API Integration

### REST API Endpoints
The frontend integrates with all backend endpoints:

- **Authentication**: `/api/v1/auth/*`
- **Users**: `/api/v1/users/*`
- **Assessments**: `/api/v1/assessments/*`
- **Learning Paths**: `/api/v1/learning/*`
- **Privacy**: `/api/v1/privacy/*`

### WebSocket Communication
- Real-time chat: `/api/v1/ws/chat/{user_id}`
- Live updates and notifications
- Connection management and reconnection
- Message queuing and delivery

### Error Handling
- Graceful API error handling
- User-friendly error messages
- Fallback to mock data when API unavailable
- Connection status indicators

## 🧪 Development Mode

### Mock Data
Enable mock data for development without backend:
```bash
export USE_MOCK_DATA=true
```

Mock data includes:
- Sample user profiles
- Learning paths and milestones
- Assessment history
- Chat conversations
- Analytics data

### Testing
Run the application in development mode:
```bash
streamlit run streamlit_app.py --server.runOnSave=true
```

## 🚀 Deployment

### Production Configuration
1. **Set production environment variables:**
   ```bash
   export EDAGENT_API_URL="https://your-api-domain.com/api/v1"
   export EDAGENT_WS_URL="wss://your-api-domain.com/api/v1/ws"
   export USE_MOCK_DATA="false"
   ```

2. **Configure Streamlit for production:**
   ```toml
   # .streamlit/config.toml
   [server]
   port = 8501
   address = "0.0.0.0"
   
   [browser]
   gatherUsageStats = false
   ```

### Docker Deployment
Use the provided Docker configuration:
```bash
docker-compose -f docker-compose.frontend.yml up -d
```

### Nginx Reverse Proxy
Configure Nginx for production deployment:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔒 Security

### Authentication
- JWT token-based authentication
- Secure session management
- API key validation
- User context isolation

### Data Protection
- Input sanitization
- XSS prevention
- CSRF protection
- Secure API communication

### Privacy
- Data export functionality
- Data deletion controls
- Privacy settings management
- Audit logging

## 📊 Monitoring

### Health Checks
- Application health monitoring
- API connectivity checks
- WebSocket connection status
- Performance metrics

### Logging
- Application event logging
- Error tracking and reporting
- User interaction analytics
- Performance monitoring

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Install dependencies: `pip install -r streamlit_requirements.txt`
3. Set up environment variables
4. Run the application: `streamlit run streamlit_app.py`

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Document functions and classes
- Write unit tests for components

### Adding Features
1. Update feature flags in `streamlit_config.py`
2. Add components to `streamlit_components.py`
3. Integrate with main app in `streamlit_app.py`
4. Update documentation

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the API documentation at `/docs`
- Review the configuration settings
- Enable debug mode for detailed logging
- Check WebSocket connection status

## 🔄 Updates

### Version 1.0.0
- Initial release with core functionality
- Real-time chat interface
- Skill assessments and learning paths
- User profile management
- Privacy controls and analytics

### Planned Features
- Mobile-responsive design improvements
- Offline mode support
- Advanced analytics and reporting
- Integration with external learning platforms
- Multi-language support