# Privacy Controls Documentation

## Overview

EdAgent implements comprehensive data privacy controls to ensure user data is handled securely and in compliance with privacy regulations. Users have full control over their data with options to export, delete, and manage privacy settings.

## Features

### 1. Data Export
Users can export all their data in a structured JSON format including:
- User profile and preferences
- Skills and assessments
- Conversation history
- Learning paths and milestones
- Session information (excluding sensitive tokens)
- API key metadata (excluding sensitive hashes)

**API Endpoint:** `POST /api/v1/privacy/export`

### 2. Data Deletion
Users can delete their data selectively or completely:
- **Selective deletion**: Delete specific data types (conversations, skills, learning paths, etc.)
- **Complete deletion**: Delete all user data including profile
- **Confirmation required**: All deletions must be explicitly confirmed

**API Endpoint:** `DELETE /api/v1/privacy/data`

### 3. Privacy Settings
Users can configure privacy preferences:
- Data retention periods
- Analytics data collection consent
- Personalization features consent
- Marketing communications consent
- Auto-deletion of old conversations

**API Endpoints:** 
- `GET /api/v1/privacy/settings`
- `PUT /api/v1/privacy/settings`

### 4. Consent Management
Track and manage user consent for different types of data processing:
- Data processing consent
- Analytics consent
- Marketing consent
- Personalization consent

**API Endpoint:** `POST /api/v1/privacy/consent`

### 5. Audit Logging
All privacy-related actions are logged for compliance:
- Data exports
- Data deletions
- Consent changes
- Data access events

**API Endpoint:** `GET /api/v1/privacy/audit-log`

### 6. Data Summary
Users can view a summary of what data exists in their profile:
- Count of conversations, skills, learning paths, etc.
- Account creation and last activity dates
- Data retention information

**API Endpoint:** `GET /api/v1/privacy/data-summary`

## Authentication

All privacy endpoints require authentication via:
- JWT session token in Authorization header: `Bearer <token>`
- API key in X-API-Key header: `X-API-Key: <api_key>`

## Usage Examples

### Export User Data
```bash
curl -X POST "http://localhost:8000/api/v1/privacy/export" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"include_sensitive": false, "format": "json"}'
```

### Delete Conversations
```bash
curl -X DELETE "http://localhost:8000/api/v1/privacy/data" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "data_types": ["conversations"],
    "confirm_deletion": true,
    "reason": "User request"
  }'
```

### Update Privacy Settings
```bash
curl -X PUT "http://localhost:8000/api/v1/privacy/settings" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "allow_analytics": false,
    "auto_delete_conversations": true,
    "conversation_retention_days": 90
  }'
```

### Get Data Summary
```bash
curl -X GET "http://localhost:8000/api/v1/privacy/data-summary" \
  -H "Authorization: Bearer <your_token>"
```

## Security Considerations

1. **Authentication Required**: All endpoints require valid authentication
2. **Explicit Confirmation**: Data deletion requires explicit confirmation
3. **Audit Logging**: All privacy actions are logged for compliance
4. **Sensitive Data Exclusion**: Exported data excludes sensitive information like password hashes and API key secrets
5. **Rate Limiting**: Endpoints are subject to rate limiting to prevent abuse

## Compliance

The privacy controls are designed to support compliance with:
- GDPR (General Data Protection Regulation)
- CCPA (California Consumer Privacy Act)
- Other data protection regulations

Key compliance features:
- Right to data portability (export)
- Right to erasure (deletion)
- Consent management
- Audit trails
- Data minimization principles

## Database Schema

The privacy system uses additional database tables:
- `privacy_audit_log`: Tracks all privacy-related actions
- `user_privacy_settings`: Stores user privacy preferences
- `user_consent_records`: Records user consent for different data processing types

## Error Handling

The privacy system includes comprehensive error handling:
- User not found errors
- Confirmation required errors
- Authentication failures
- Database operation failures
- Graceful degradation when services are unavailable

## Testing

The privacy functionality includes comprehensive tests:
- Unit tests for service logic
- Integration tests with database
- API endpoint tests
- Error handling tests
- Compliance scenario tests