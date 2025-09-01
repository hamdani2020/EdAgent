# EdAgent REST API

This is the REST API for the EdAgent conversational AI career coaching assistant.

## Features

- **Conversation Management**: Send messages and get AI responses
- **User Management**: Create and manage user profiles and preferences
- **Skill Assessment**: Interactive skill assessments with personalized feedback
- **Learning Paths**: Generate and track personalized learning paths
- **Content Recommendations**: Get curated educational content

## API Documentation

Once the server is running, you can access:

- **Interactive API Documentation**: http://localhost:8000/docs
- **Alternative Documentation**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Quick Start

1. **Start the server**:
   ```bash
   python main.py
   ```

2. **Health Check**:
   ```bash
   curl http://localhost:8000/health
   ```

3. **Create a user**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/users/" \
        -H "Content-Type: application/json" \
        -d '{
          "user_id": "user123",
          "career_goals": ["become a software developer"],
          "learning_preferences": {
            "learning_style": "visual",
            "time_commitment": "2-3 hours/week",
            "budget_preference": "free"
          }
        }'
   ```

4. **Send a message**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/conversations/message" \
        -H "Content-Type: application/json" \
        -d '{
          "user_id": "user123",
          "message": "Hi, I want to learn Python programming"
        }'
   ```

## API Endpoints

### Health
- `GET /health` - Health check

### Users
- `POST /api/v1/users/` - Create a new user
- `GET /api/v1/users/{user_id}` - Get user profile
- `PUT /api/v1/users/{user_id}/preferences` - Update user preferences
- `PUT /api/v1/users/{user_id}/skills` - Update user skills
- `GET /api/v1/users/{user_id}/goals` - Get user goals
- `PUT /api/v1/users/{user_id}/goals` - Update user goals
- `DELETE /api/v1/users/{user_id}` - Delete user

### Conversations
- `POST /api/v1/conversations/message` - Send message to AI
- `GET /api/v1/conversations/{user_id}/history` - Get conversation history
- `DELETE /api/v1/conversations/{user_id}/history` - Clear conversation history
- `GET /api/v1/conversations/{user_id}/context` - Get conversation context

### Assessments
- `POST /api/v1/assessments/start` - Start skill assessment
- `GET /api/v1/assessments/{assessment_id}` - Get assessment details
- `POST /api/v1/assessments/{assessment_id}/respond` - Submit assessment response
- `POST /api/v1/assessments/{assessment_id}/complete` - Complete assessment
- `GET /api/v1/assessments/user/{user_id}` - Get user assessments
- `GET /api/v1/assessments/{assessment_id}/progress` - Get assessment progress
- `DELETE /api/v1/assessments/{assessment_id}` - Delete assessment

### Learning Paths
- `POST /api/v1/learning/paths` - Create learning path
- `GET /api/v1/learning/paths/{path_id}` - Get learning path details
- `GET /api/v1/learning/paths/user/{user_id}` - Get user learning paths
- `PUT /api/v1/learning/paths/{path_id}/milestones/{milestone_id}/status` - Update milestone status
- `GET /api/v1/learning/paths/{path_id}/progress` - Get learning path progress
- `DELETE /api/v1/learning/paths/{path_id}` - Delete learning path
- `GET /api/v1/learning/milestones/{milestone_id}` - Get milestone details
- `GET /api/v1/learning/milestones/{milestone_id}/resources` - Get milestone resources

## Configuration

The API uses environment variables for configuration. See `.env.example` for available options:

- `GEMINI_API_KEY` - Google Gemini API key (required)
- `YOUTUBE_API_KEY` - YouTube Data API key (required)
- `DATABASE_URL` - Database connection URL
- `SECRET_KEY` - Secret key for session management
- `API_HOST` - API server host (default: 0.0.0.0)
- `API_PORT` - API server port (default: 8000)
- `API_DEBUG` - Enable debug mode (default: false)

## Rate Limiting

The API includes rate limiting:
- 60 requests per minute per IP address
- Burst limit of 10 requests in 10 seconds
- Rate limit headers included in responses

## Error Handling

All errors return JSON responses with the following structure:
```json
{
  "error": {
    "message": "Error description",
    "type": "ErrorType",
    "details": {}
  }
}
```

## Security

- CORS middleware configured
- Security headers added to responses
- Input validation and sanitization
- Rate limiting protection
- Request/response logging

## Development

To run in development mode:
```bash
export API_DEBUG=true
python main.py
```

This enables:
- Auto-reload on code changes
- Detailed error messages
- SQL query logging
- Enhanced debugging information