# Automatic Empathy & Conversation Training System

## Overview

The Socializer app now includes an **automatic training system** that helps users improve their empathy and conversation skills through natural, subtle guidance. The system operates in the background while users interact with the AI, tracking progress and providing personalized feedback.

## Key Features

### 1. **Automatic Training Plan Creation** ✅
- Every user automatically receives a default training plan on first login
- Default training includes:
  - **Empathy Training** (30-day program)
  - **Conversation/Active Listening Training** (30-day program)
- Training plans are **encrypted** and stored securely per user

### 2. **Progress Tracking Every 5th Message** ✅
- System monitors user messages automatically
- Every **5th message** triggers a skill evaluation
- Uses `SkillEvaluator` tool to analyze:
  - Empathy demonstration
  - Active listening
  - Clear communication
  - Engagement quality

### 3. **Subtle Training Approach** ✅
- AI provides **examples and hints** naturally in conversation
- No explicit "training mode" - feels like helpful advice
- AI models good empathy and communication in its responses
- Uses **positive reinforcement** and encouraging language

### 4. **Cultural & Political Standards Checking** ✅
- New `CulturalStandardsChecker` tool monitors chat room messages
- Checks for:
  - Culturally sensitive topics
  - Potentially offensive language
  - Political correctness
- Uses **web search** to get latest cultural standards
- Provides suggestions for more respectful phrasing

### 5. **Login/Logout Lifecycle** ✅
- **Login**: User receives personalized training reminder
- **During Chat**: Progress tracked automatically
- **Logout**: All progress saved to encrypted storage

### 6. **Encrypted Data** ✅
- All training data stored via `SecureMemoryManager`
- Each user has unique encryption key
- Complete isolation between users
- Training progress inaccessible to other users or agents

---

## Architecture

### Components Created

```
training/
├── __init__.py
└── training_plan_manager.py       # Main training plan logic

tools/communication/
└── cultural_checker_tool.py       # Cultural sensitivity checker
```

### Key Classes

#### `TrainingPlanManager`
**Location**: `training/training_plan_manager.py`

**Purpose**: Manages all automatic training functionality

**Methods**:
- `get_or_create_training_plan(user)` - Load or create training plan
- `increment_message_count(user)` - Track messages for 5th-message check
- `should_check_progress(user)` - Determine if it's time to evaluate
- `update_training_progress(user, analysis)` - Update skill levels
- `get_login_reminder(user)` - Generate login message
- `get_training_context_for_prompt(user)` - Add training to AI prompt
- `save_logout_progress(user)` - Save on logout

**Data Structure**:
```python
{
    "user_id": 123,
    "created_at": "2025-11-30T17:00:00",
    "message_count": 7,
    "last_progress_check": "2025-11-30T17:05:00",
    "trainings": {
        "empathy_training": {
            "skill_id": 1,
            "skill_name": "empathy",
            "current_level": 3,
            "target_level": 10,
            "progress_percent": 30,
            "status": "active",
            "next_milestone": "Asking follow-up questions about feelings"
        },
        "conversation_training": {...}
    }
}
```

#### `CulturalStandardsChecker`
**Location**: `tools/communication/cultural_checker_tool.py`

**Purpose**: Check cultural/political sensitivity in messages

**Features**:
- Detects sensitive topics (religion, politics, race, gender, etc.)
- Identifies potentially offensive terms
- Uses web search for latest cultural standards
- Returns sensitivity score (0-10)
- Provides alternative phrasing suggestions

---

## Integration Points

### AiChatagent (`ai_chatagent.py`)

#### `__init__` Method
```python
# Training plan loaded on agent creation
self.training_manager = training_plan_manager
self.training_plan = self.training_manager.get_or_create_training_plan(user)
self.message_counter = self.training_plan.get("message_count", 0)
```

#### `chatbot` Method
```python
# 1. Increment message count
if hasattr(last_message, 'type') and last_message.type == 'human':
    self.message_counter += 1
    self.training_manager.increment_message_count(self.user)
    
    # Check every 5th message
    if self.message_counter % 5 == 0:
        should_check_training = True

# 2. Training context added to system prompt
system_prompt = f"""...
{self.training_manager.get_training_context_for_prompt(self.user)}
..."""

# 3. Progress check after response
if should_check_training:
    skill_analysis = self.skill_evaluator_tool._run(user_id=self.user.id, ...)
    updated_training = self.training_manager.update_training_progress(
        self.user, skill_analysis
    )
```

### API Endpoints (`app/routers/ai.py`)

#### GET `/api/ai/training/login-reminder`
Returns personalized training reminder for login screen.

**Response**:
```json
{
    "message": "Welcome back, John! 🎯\n\nYour Active Trainings:\n• Empathy: Level 3/10 - Next: Asking follow-up questions about feelings\n• Active Listening: Level 5/10 - Next: Building on others' ideas"
}
```

#### POST `/api/ai/training/logout`
Saves all training progress when user logs out.

**Response**:
```json
{
    "status": "success",
    "message": "Training progress saved"
}
```

---

## User Experience Flow

### 1. First Login (New User)
```
User logs in
    ↓
GET /api/ai/training/login-reminder
    ↓
System creates default training plan:
  - Empathy Training (Level 0/10)
  - Active Listening Training (Level 0/10)
    ↓
Display: "Welcome, John! 🎯 You're starting your empathy and conversation training!"
```

### 2. During Chat
```
User: "My colleague was rude to me."
AI: "That sounds frustrating. How did that make you feel?" 
     ↑ (Subtly teaching empathy without mentioning it)

[Behind scenes after 5th message:]
  - SkillEvaluator analyzes messages
  - Detects empathy keywords: "feel", "frustrating"
  - Updates: Empathy Level 0 → 1
  - Next milestone: "Recognizing emotions in text" ✓
```

### 3. Multi-User Chat Room
```
User A (German): "Diese Politik ist dumm"
User B (English): "What?"
    ↓
AI: "Let me help clarify. User A said 'This policy is stupid'. 
     Note: In German culture, direct criticism is common. 
     User A might consider: 'I have concerns about this policy because...'"
     ↑ (Uses CulturalStandardsChecker + ClarifyCommunication tools)
```

### 4. Logout
```
User logs out
    ↓
POST /api/ai/training/logout
    ↓
System saves:
  - Final skill levels
  - Message count
  - Training progress
  - All encrypted to user's secure storage
```

---

## System Prompt Enhancement

The AI's system prompt now includes training context:

```
🎯 **ACTIVE TRAINING PLAN**
User John is currently training in:
• **Empathy** (Level 3/10): Understanding and sharing feelings of others
  Next milestone: Asking follow-up questions about feelings
• **Active Listening** (Level 5/10): Active listening and engaging conversation
  Next milestone: Building on others' ideas

**YOUR TRAINING APPROACH:**
- Provide subtle examples and hints (not explicit training instructions)
- Model good empathy and conversation skills in your responses
- Gently guide user toward better communication patterns
- Make training feel like natural, helpful conversation
- Use encouraging, positive reinforcement
```

---

## Testing

### Manual Testing Steps

1. **Test Login Reminder**
   ```bash
   curl -X GET http://localhost:8000/api/ai/training/login-reminder \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

2. **Test Chat with Training**
   - Send 5 messages
   - Check logs for "🎯 Training progress check triggered"
   - Verify skill levels update in database

3. **Test Cultural Checker**
   - Send message with sensitive topic
   - AI should use `check_cultural_standards` tool
   - Verify suggestions appear

4. **Test Logout**
   ```bash
   curl -X POST http://localhost:8000/api/ai/training/logout \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

### Automated Tests

Create test file: `tests/test_training_system.py`

```python
def test_training_plan_creation(test_user):
    """Test automatic training plan creation"""
    manager = TrainingPlanManager(dm)
    plan = manager.get_or_create_training_plan(test_user)
    
    assert "trainings" in plan
    assert "empathy_training" in plan["trainings"]
    assert plan["trainings"]["empathy_training"]["current_level"] == 0

def test_message_count_increment(test_user):
    """Test message counting for 5th-message trigger"""
    manager = TrainingPlanManager(dm)
    
    for i in range(5):
        manager.increment_message_count(test_user)
    
    plan = manager._load_encrypted_training_data(test_user)
    assert plan["message_count"] == 5

def test_cultural_checker():
    """Test cultural sensitivity checking"""
    checker = CulturalStandardsChecker()
    result = checker._run(
        message="This is stupid and retarded",
        cultural_context="Western"
    )
    
    assert result["message_safe"] == False
    assert result["sensitivity_score"] > 5
    assert len(result["warnings"]) > 0
```

---

## Security & Privacy

### Encryption
- All training data stored via `SecureMemoryManager`
- Uses Fernet encryption with user-specific keys
- Keys stored in `users.encryption_key` (unique per user)

### Isolation
- Each user's training data completely isolated
- No cross-user access possible
- AI agent cannot access other users' training plans

### Data Structure
```python
# In user.conversation_memory (encrypted)
{
    "training_plan": {
        "user_id": 123,
        "trainings": {...},
        "message_count": 7,
        ...
    },
    "messages": [...],
    "ai_conversation": [...],
    ...
}
```

---

## Configuration

### Default Training Skills

Edit `training/training_plan_manager.py`:

```python
DEFAULT_TRAINING = {
    "empathy_training": {
        "skill_name": "empathy",
        "duration_days": 30,
        "priority": "high",
        "auto_start": True  # Starts automatically
    },
    "custom_skill": {
        "skill_name": "public_speaking",
        "duration_days": 60,
        "priority": "medium",
        "auto_start": False  # Starts only when user requests
    }
}
```

### Adjust Progress Check Frequency

In `ai_chatagent.py`:

```python
# Check every 5th message (default)
if self.message_counter % 5 == 0:
    should_check_training = True

# Change to every 10th message
if self.message_counter % 10 == 0:
    should_check_training = True
```

---

## API Reference

### GET `/api/ai/training/login-reminder`
Get training reminder for login.

**Auth**: Required  
**Returns**: `{"message": "Welcome back..."}`

### POST `/api/ai/training/logout`
Save training progress on logout.

**Auth**: Required  
**Returns**: `{"status": "success", "message": "Training progress saved"}`

### Tool: `check_cultural_standards`
AI tool for checking cultural sensitivity.

**Args**:
- `message` (str): Message to check
- `cultural_context` (Optional[str]): Cultural context
- `user_country` (Optional[str]): User's country

**Returns**:
```python
{
    "status": "success",
    "message_safe": True,
    "sensitivity_score": 3,
    "warnings": [...],
    "suggestions": [...],
    "sensitive_topics": ["religion"],
    "overall_assessment": "✅ Message appears culturally appropriate"
}
```

---

## Troubleshooting

### Training plan not loading
**Check**: Is `training_plan_manager` initialized in `ai_chatagent.py`?
```python
# Should be after imports
training_plan_manager = TrainingPlanManager(dm)
```

### Progress not updating
**Check**: Is `should_check_training` being set correctly?
```bash
# Look for in logs:
"📊 Message count: 5"
"🎯 Training progress check triggered (message #5)"
```

### Cultural checker not working
**Check**: Is Tavily API key set?
```bash
# In .env
TAVILY_API_KEY=your_key_here
```

### Data not encrypted
**Check**: Does user have encryption key?
```sql
SELECT id, username, encryption_key FROM users WHERE id=123;
```

If null, run migration:
```bash
python migrations/add_encryption_keys.py
```

---

## Future Enhancements

### Planned Features
- [ ] Custom training plans (user-requested skills)
- [ ] Training reports/dashboards
- [ ] Gamification (badges, streaks)
- [ ] Training difficulty adjustment based on performance
- [ ] Multi-language training support
- [ ] Export training progress as PDF

### Potential Tools
- `TrainingReportTool` - Generate progress reports
- `SkillRecommendationTool` - Suggest new skills to learn
- `TrainingGoalsTool` - Set and track custom goals

---

## Summary

The automatic training system provides:

✅ **Automatic** empathy + conversation training  
✅ **Subtle** guidance (no explicit "training mode")  
✅ **Progress tracking** every 5th message  
✅ **Cultural sensitivity** checking  
✅ **Encrypted** user data  
✅ **Login reminders** with progress  
✅ **Logout** progress saving  

Users experience natural, helpful conversations while improving their social skills in the background. The system respects cultural differences and promotes respectful communication across diverse chat rooms.

---

## Files Modified/Created

### Created
- `training/__init__.py`
- `training/training_plan_manager.py`
- `tools/communication/cultural_checker_tool.py`
- `docs/AUTOMATIC_TRAINING_SYSTEM.md`

### Modified
- `ai_chatagent.py` - Added training initialization and progress tracking
- `app/routers/ai.py` - Added login/logout endpoints
- `tools/communication/__init__.py` - Exported `CulturalStandardsChecker`

---

**Built with ❤️ for Socializer**
