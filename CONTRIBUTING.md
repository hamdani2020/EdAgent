# Contributing to EdAgent

Thank you for your interest in contributing to EdAgent! This document provides guidelines and information for contributors.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/edagent.git`
3. Create a virtual environment: `python -m venv .venv`
4. Activate the virtual environment: `source .venv/bin/activate` (Linux/Mac) or `.venv\Scripts\activate` (Windows)
5. Install dependencies: `pip install -r requirements.txt`
6. Copy `.env.example` to `.env` and configure your API keys

## Development Guidelines

### Code Quality Standards
- Use Python 3.9+ with type hints
- Follow PEP 8 style guidelines
- Implement comprehensive error handling
- Write unit tests for all core functionality
- Use async/await for API calls

### API Integration Guidelines
- Use Google Gemini API for conversational AI
- Implement rate limiting and retry logic
- Store API keys in environment variables
- Log API usage for monitoring

### Educational Content Standards
- Prioritize free resources when available
- Verify course quality and ratings
- Include diverse learning formats (video, text, interactive)
- Maintain up-to-date course recommendations

## Making Changes

1. Create a new branch: `git checkout -b feature/your-feature-name`
2. Make your changes following the coding standards
3. Add or update tests as needed
4. Run tests: `pytest`
5. Commit your changes: `git commit -m "Add your descriptive commit message"`
6. Push to your fork: `git push origin feature/your-feature-name`
7. Create a Pull Request

## Testing

Run the test suite before submitting your changes:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=edagent

# Run specific test file
pytest tests/test_specific_file.py
```

## Documentation

- Update documentation for any new features
- Include docstrings for all functions and classes
- Update README.md if needed
- Add examples for new functionality

## Reporting Issues

When reporting issues, please include:
- Python version
- Operating system
- Steps to reproduce the issue
- Expected vs actual behavior
- Error messages or logs

## Feature Requests

We welcome feature requests! Please:
- Check existing issues first
- Provide a clear description of the feature
- Explain the use case and benefits
- Consider implementation complexity

## Questions?

Feel free to open an issue for questions or join our discussions.

Thank you for contributing to EdAgent!