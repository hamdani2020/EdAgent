---
inclusion: fileMatch
fileMatchPattern: '*gemini*'
---

# Gemini API Integration Guidelines

## Authentication
- Use `GEMINI_API_KEY` environment variable
- Implement proper error handling for authentication failures
- Never log or expose API keys in code

## Model Configuration
- Use `gemini-1.5-flash` for fast responses
- Use `gemini-1.5-pro` for complex reasoning tasks
- Set appropriate temperature (0.7 for coaching, 0.3 for factual responses)

## Prompt Engineering
- Use system prompts to establish EdAgent personality
- Include context about user's learning goals
- Structure prompts for consistent response format

## Rate Limiting
- Implement exponential backoff for rate limit errors
- Cache responses when appropriate
- Monitor usage to stay within quotas

## Response Processing
- Parse structured responses (JSON when needed)
- Handle partial responses gracefully
- Validate response content before presenting to user