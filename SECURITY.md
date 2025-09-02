# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability, please follow these steps:

1. **Do not** create a public GitHub issue for the vulnerability
2. Email us at [security@edagent.dev] with details of the vulnerability
3. Include steps to reproduce the issue
4. Allow us reasonable time to address the issue before public disclosure

## Security Best Practices

When using EdAgent:

1. **API Keys**: Never commit API keys to version control
   - Use environment variables for all sensitive configuration
   - Rotate API keys regularly
   - Use the principle of least privilege for API access

2. **Database Security**: 
   - Use strong passwords for database connections
   - Enable SSL/TLS for database connections in production
   - Regularly backup and secure your database

3. **Network Security**:
   - Use HTTPS in production
   - Implement proper CORS policies
   - Use secure WebSocket connections (WSS) in production

4. **Authentication**:
   - Use strong session secrets
   - Implement proper session management
   - Consider implementing rate limiting

## Dependencies

We regularly update dependencies to address security vulnerabilities. Please keep your installation up to date.

## Responsible Disclosure

We appreciate security researchers who responsibly disclose vulnerabilities. We will:

- Acknowledge your report within 48 hours
- Provide regular updates on our progress
- Credit you in our security advisories (if desired)
- Work with you to understand and resolve the issue

Thank you for helping keep EdAgent secure!