# Data Manager Package

This package provides functionality for managing data models and their interactions with the database for the Skills
Training API.

## Components

### DataManager Class

The `DataManager` class is the main interface for database operations, handling:

- User management (create, read, update, delete)
- Skills management
- Training management
- Session handling

## Testing

The package includes comprehensive tests in `test_data_model.py`. Run tests with:

```bash
python -m unittest datamanager.test_data_model
```

## Usage Example

```python
import datetime
from datamanager.data_manager import DataManager
from datamanager.data_model import User, Skill, Training

# Initialize data manager
data_manager = DataManager()

# Create a user
user = User(
    username="new_user",
    hashed_password="hashed_pw",
    role="user"
)
user = data_manager.add_user(user)

# Add a skill for the user
skill = Skill(
    user_id=user.id,
    skill_name="Python",
)
skill = data_manager.add_skill(skill)

# Add a training for the skill
training = Training(
    user_id=user.id,
    skill_id=skill.id,
    body="Learning Python basics",
    status="pending",
    started_at=datetime.datetime.now().date()
)
training = data_manager.add_training(training)
```
