# Local LLM Configuration Feature

## Overview

This feature allows users to configure custom local LLM servers (like LM Studio or Ollama) by entering the IP address and port through a user-friendly interface. Users can now connect to their own LLM instances running on local networks or custom endpoints.

## Implementation Summary

### ✅ Completed Components

#### 1. **Database Model Updates**
- **File**: `datamanager/data_model.py`
- **Changes**: Added three new fields to the `User` model:
  - `llm_provider`: Stores the selected provider (e.g., 'lm_studio', 'ollama', 'openai')
  - `llm_endpoint`: Stores the complete endpoint URL (e.g., 'http://192.168.1.100:1234')
  - `llm_model`: Stores the model name (e.g., 'llama-3.2', 'local-model')
- **Nullable**: All fields are optional (nullable=True) to maintain backward compatibility

#### 2. **API Schemas**
- **File**: `app/schemas/__init__.py`
- **New Schemas**:
  - `LLMConfigBase`: Base schema with provider, endpoint, and model fields
  - `LLMConfigCreate`: Request schema with validation for endpoint URL and provider
  - `LLMConfigResponse`: Response schema with user_id
- **Validation**:
  - Endpoint must start with `http://` or `https://`
  - Endpoint must include a port number
  - Provider must be one of: lm_studio, ollama, openai, gemini, claude

#### 3. **Backend API Routes**
- **File**: `app/routers/ai.py`
- **Endpoints**:
  - `GET /api/ai/llm-config` - Retrieve user's LLM configuration
  - `POST /api/ai/llm-config` - Create or update LLM configuration
  - `DELETE /api/ai/llm-config` - Clear LLM configuration
- **Features**:
  - Full authentication required
  - Comprehensive error handling
  - Logging for debugging and monitoring
  - Swagger/OpenAPI documentation

#### 4. **AI Chat Integration**
- **File**: `app/routers/ai.py` (chat endpoint)
- **Functionality**:
  - Checks user's custom LLM configuration before initializing AI
  - Uses custom endpoint if configured
  - Falls back to default configuration if not set
  - Supports both local and cloud providers

#### 5. **Frontend UI**
- **File**: `templates/new-chat.html`
- **Components**:
  - LLM Configuration Modal with:
    - Provider selection dropdown
    - IP address input field
    - Port number input field
    - Model name input field
    - Live endpoint preview
    - Save, Clear, and Cancel buttons
  - LLM button in chat interface to open configuration modal

#### 6. **Frontend JavaScript**
- **File**: `static/js/chat.js`
- **Class**: `LLMConfigManager`
- **Features**:
  - OOP design with clear separation of concerns
  - Async/await for all API calls
  - Comprehensive error handling
  - Real-time endpoint preview
  - Form validation
  - Status messages for user feedback
  - Auto-population of default ports based on provider

#### 7. **Comprehensive Tests**
- **File**: `tests/test_llm_config_endpoints.py`
- **Test Coverage**:
  - GET requests (with and without configuration)
  - POST requests (create, update, validation)
  - DELETE requests (clear configuration)
  - Authentication and authorization
  - Endpoint URL validation
  - Provider validation
  - Full lifecycle integration tests
- **Test Classes**:
  - `TestLLMConfigEndpoints`: Main endpoint tests
  - `TestLLMConfigPersistence`: Persistence and session tests

#### 8. **Database Migration**
- **File**: `migrations/add_llm_config_fields.py`
- **Features**:
  - Safe migration with existence checks
  - Verification step after migration
  - Detailed logging
  - Error handling and rollback support

## Usage Guide

### For Users

#### Configuring a Local LLM

1. **Open Configuration Modal**:
   - Click the "LLM" button in the chat interface (CPU icon)

2. **Enter Configuration**:
   - **Provider**: Select from dropdown (LM Studio, Ollama, etc.)
   - **IP Address**: Enter the IP or hostname (e.g., `192.168.1.100` or `localhost`)
   - **Port**: Enter the port number (e.g., `1234` for LM Studio, `11434` for Ollama)
   - **Model**: Optionally enter the model name (e.g., `llama-3.2`)

3. **Preview**: The endpoint preview shows the complete URL that will be used

4. **Save**: Click "Save Configuration" to store your settings

5. **Clear**: Use "Clear Config" to remove configuration and revert to defaults

#### Example Configurations

**LM Studio (Local)**:
```
Provider: LM Studio (local)
IP: localhost
Port: 1234
Model: local-model
Endpoint: http://localhost:1234
```

**Ollama (Local Network)**:
```
Provider: Ollama (local)
IP: 192.168.1.100
Port: 11434
Model: llama3.2
Endpoint: http://192.168.1.100:11434
```

**Custom Setup**:
```
Provider: LM Studio (local)
IP: 10.0.0.50
Port: 8080
Model: mistral-7b
Endpoint: http://10.0.0.50:8080
```

### For Developers

#### Running Tests

```bash
# Run all LLM configuration tests
pytest tests/test_llm_config_endpoints.py -v

# Run specific test class
pytest tests/test_llm_config_endpoints.py::TestLLMConfigEndpoints -v

# Run with coverage
pytest tests/test_llm_config_endpoints.py --cov=app.routers.ai
```

#### Running Migration

```bash
# Execute database migration
python migrations/add_llm_config_fields.py
```

#### API Documentation

Access Swagger UI at: `http://localhost:8000/docs`

Navigate to the "AI/LLM" section to see:
- GET `/api/ai/llm-config`
- POST `/api/ai/llm-config`
- DELETE `/api/ai/llm-config`

#### Code Examples

**Fetching Configuration (JavaScript)**:
```javascript
const response = await fetch('/api/ai/llm-config', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
const config = await response.json();
console.log(config.provider, config.endpoint, config.model);
```

**Saving Configuration (JavaScript)**:
```javascript
const config = {
    provider: 'lm_studio',
    endpoint: 'http://192.168.1.100:1234',
    model: 'llama-3.2'
};

const response = await fetch('/api/ai/llm-config', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(config)
});
```

**Using in Python Backend**:
```python
from llm_manager import LLMManager

# User's custom configuration is automatically used
if current_user.llm_provider and current_user.llm_endpoint:
    llm = LLMManager.get_llm(
        provider=current_user.llm_provider,
        model=current_user.llm_model or "local-model",
        base_url=current_user.llm_endpoint
    )
```

## Architecture

### OOP Design Principles

1. **Single Responsibility**: Each class handles one concern
   - `LLMConfigManager`: Frontend configuration management
   - `LLMConfigCreate`: Request validation
   - `LLMConfigResponse`: Response serialization

2. **Encapsulation**: Private methods prefixed with `_`
   - `_setupEventListeners()`: Internal event setup
   - `_updateEndpointPreview()`: Internal UI update
   - `_makeAuthenticatedRequest()`: Internal API calls

3. **Separation of Concerns**:
   - Database layer: `data_model.py`
   - API layer: `routers/ai.py`
   - Frontend logic: `chat.js`
   - Validation: `schemas/__init__.py`

### Error Handling

- **Frontend**: Try-catch blocks with user-friendly messages
- **Backend**: HTTPException with appropriate status codes
- **Database**: Transaction rollback on errors
- **Validation**: Pydantic validators with clear error messages

### Security

- **Authentication**: JWT token required for all endpoints
- **Authorization**: Users can only access their own configuration
- **Validation**: Input sanitization and URL validation
- **HTTPS Support**: Accepts both HTTP and HTTPS endpoints

## Testing Strategy

### Test-Driven Development (TDD)

Tests were written following TDD principles:
1. ✅ Written before implementation
2. ✅ Cover all happy paths
3. ✅ Cover edge cases and error conditions
4. ✅ Test authentication and authorization
5. ✅ Integration tests for full lifecycle

### Test Coverage

- **Unit Tests**: Individual endpoint behavior
- **Integration Tests**: Full CRUD lifecycle
- **Validation Tests**: Input validation and error cases
- **Authentication Tests**: Token validation
- **Persistence Tests**: Database storage and retrieval

## Future Enhancements

### Potential Improvements

1. **Connection Testing**: Add "Test Connection" button to verify LLM endpoint
2. **Multiple Configurations**: Allow users to save multiple configurations
3. **Auto-Discovery**: Scan local network for LLM servers
4. **Performance Metrics**: Track response times per configuration
5. **Configuration Sharing**: Share configurations with team members
6. **Provider Templates**: Pre-filled templates for popular setups
7. **SSL/TLS Support**: Add certificate configuration for HTTPS endpoints

## Troubleshooting

### Common Issues

**Configuration not saving**:
- Check browser console for errors
- Verify authentication token is valid
- Ensure endpoint format is correct (http://IP:PORT)

**LLM not connecting**:
- Verify LLM server is running
- Check IP and port are correct
- Ensure firewall allows connections
- Test endpoint in browser or with curl

**Validation errors**:
- Endpoint must start with http:// or https://
- Port number must be included
- Provider must be from the supported list

### Debug Mode

Enable detailed logging:
```javascript
// In browser console
localStorage.setItem('debug', 'true');
```

Check backend logs for LLM configuration:
```bash
# Look for [LLM Config] entries
tail -f logs/app.log | grep "LLM Config"
```

## Files Modified/Created

### Modified Files
- `datamanager/data_model.py` - Added LLM config fields to User model
- `app/schemas/__init__.py` - Added LLM config schemas
- `app/routers/ai.py` - Added LLM config endpoints and chat integration
- `templates/new-chat.html` - Added LLM config modal and button
- `static/js/chat.js` - Added LLMConfigManager class

### New Files
- `tests/test_llm_config_endpoints.py` - Comprehensive test suite
- `migrations/add_llm_config_fields.py` - Database migration script
- `docs/LLM_CONFIGURATION_FEATURE.md` - This documentation

## Summary

This feature provides a complete, production-ready solution for custom LLM configuration:
- ✅ Well-documented code with comments
- ✅ Comprehensive test coverage
- ✅ OOP best practices
- ✅ User-friendly interface
- ✅ Robust error handling
- ✅ Secure authentication
- ✅ Database migration support
- ✅ Swagger API documentation

The implementation follows TDD principles and maintains high code quality standards throughout.
