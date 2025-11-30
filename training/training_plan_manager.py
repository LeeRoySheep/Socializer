"""
Training Plan Manager - Automatic Empathy & Conversation Training

LOCATION: training/training_plan_manager.py
PURPOSE: Manage automatic training plans for users with encrypted storage

FEATURES:
    - Auto-create default empathy + conversation training plans
    - Track progress every 5th message
    - Generate training reminders for login
    - Update training data on logout
    - All data encrypted via SecureMemoryManager

DESIGN:
    - Uses existing Training and UserSkill database models
    - Integrates with SecureMemoryManager for encryption
    - Works with SkillEvaluator for skill tracking
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from datamanager.data_manager import DataManager
from datamanager.data_model import User, Training, UserSkill, Skill
from memory.secure_memory_manager import SecureMemoryManager
from app.ote_logger import get_logger

logger = get_logger()


class TrainingPlanManager:
    """
    Manages automatic training plans for users.
    
    This class handles:
    - Creating default empathy + conversation training plans
    - Loading training plans into AI agent context
    - Tracking message count for progress checks (every 5th message)
    - Generating login messages with training reminders
    - Saving progress on logout
    - Encrypting all training data
    
    Attributes:
        dm: DataManager instance for database operations
        memory_manager: SecureMemoryManager for encrypted storage
        
    Example:
        >>> manager = TrainingPlanManager(data_manager)
        >>> plan = manager.get_or_create_training_plan(user)
        >>> reminder = manager.get_login_reminder(user)
    """
    
    # Default training plan structure
    DEFAULT_TRAINING = {
        "empathy_training": {
            "skill_name": "empathy",
            "description": "Understanding and sharing feelings of others",
            "duration_days": 30,
            "milestones": [
                {"level": 2, "description": "Recognizing emotions in text"},
                {"level": 4, "description": "Responding with empathetic phrases"},
                {"level": 6, "description": "Asking follow-up questions about feelings"},
                {"level": 8, "description": "Providing emotional support naturally"},
                {"level": 10, "description": "Mastery: Authentic empathetic communication"}
            ],
            "priority": "high",
            "auto_start": True
        },
        "conversation_training": {
            "skill_name": "active_listening",
            "description": "Active listening and engaging conversation",
            "duration_days": 30,
            "milestones": [
                {"level": 2, "description": "Using acknowledgment phrases"},
                {"level": 4, "description": "Asking clarifying questions"},
                {"level": 6, "description": "Summarizing what others said"},
                {"level": 8, "description": "Building on others' ideas"},
                {"level": 10, "description": "Mastery: Natural conversational flow"}
            ],
            "priority": "high",
            "auto_start": True
        }
    }
    
    def __init__(self, data_manager: DataManager):
        """
        Initialize TrainingPlanManager.
        
        Args:
            data_manager: DataManager instance for database operations
        """
        self.dm = data_manager
        # Note: SecureMemoryManager created per-user when needed (requires user object)
        logger.logger.info("✅ TrainingPlanManager initialized")
    
    def get_or_create_training_plan(self, user: User) -> Dict[str, Any]:
        """
        Get existing training plan or create a new one for user.
        
        This is called when user logs in to ensure they have a training plan.
        Creates default empathy + conversation training if none exists.
        
        Args:
            user: User object from database
            
        Returns:
            Dictionary containing training plan with current progress
            
        Example:
            {
                "empathy_training": {
                    "current_level": 3,
                    "target_level": 10,
                    "progress_percent": 30,
                    "next_milestone": "Asking follow-up questions about feelings",
                    "status": "active"
                },
                "conversation_training": {...},
                "message_count": 3,  # For tracking 5th message
                "last_check": "2025-11-30T17:00:00"
            }
        """
        logger.logger.info(f"Loading training plan for user {user.id} ({user.username})")
        
        try:
            # Try to load encrypted training data from memory
            training_data = self._load_encrypted_training_data(user)
            
            if training_data:
                logger.logger.info(f"✅ Loaded existing training plan for user {user.id}")
                return training_data
            
            # No training plan exists - create default one
            logger.logger.info(f"🆕 Creating default training plan for user {user.id}")
            training_data = self._create_default_training_plan(user)
            
            # Save encrypted training data
            self._save_encrypted_training_data(user, training_data)
            
            return training_data
            
        except Exception as e:
            logger.logger.error(f"Error loading/creating training plan: {e}", exc_info=True)
            return self._get_empty_training_plan()
    
    def _create_default_training_plan(self, user: User) -> Dict[str, Any]:
        """
        Create default training plan with empathy + conversation training.
        
        Args:
            user: User object
            
        Returns:
            Dictionary with default training plan structure
        """
        training_data = {
            "user_id": user.id,
            "created_at": datetime.utcnow().isoformat(),
            "message_count": 0,
            "last_progress_check": None,
            "trainings": {}
        }
        
        # Create training entries for default skills
        for training_key, training_config in self.DEFAULT_TRAINING.items():
            skill_name = training_config["skill_name"]
            
            # Get or create skill in database
            skill = self.dm.get_or_create_skill(skill_name)
            
            if skill:
                # Get current skill level
                current_level = self.dm.get_skilllevel_for_user(user.id, skill.id) or 0
                
                # Create training record in database
                training = Training(
                    user_id=user.id,
                    skill_id=skill.id,
                    status="active" if training_config.get("auto_start") else "pending",
                    progress=current_level / 10.0,  # Convert level (0-10) to progress (0.0-1.0)
                    notes=f"Auto-started: {training_config['description']}"
                )
                self.dm.add_training(training)
                
                # Add to training data
                training_data["trainings"][training_key] = {
                    "skill_id": skill.id,
                    "skill_name": skill_name,
                    "description": training_config["description"],
                    "current_level": current_level,
                    "target_level": 10,
                    "progress_percent": current_level * 10,
                    "status": training.status,
                    "started_at": training.started_at.isoformat() if training.started_at else None,
                    "milestones": training_config["milestones"],
                    "next_milestone": self._get_next_milestone(current_level, training_config["milestones"])
                }
        
        logger.logger.info(f"✅ Created default training plan with {len(training_data['trainings'])} trainings")
        return training_data
    
    def _get_next_milestone(self, current_level: int, milestones: List[Dict]) -> Optional[str]:
        """
        Get next milestone description based on current level.
        
        Args:
            current_level: Current skill level (0-10)
            milestones: List of milestone dictionaries
            
        Returns:
            Description of next milestone or None if completed
        """
        for milestone in milestones:
            if current_level < milestone["level"]:
                return milestone["description"]
        return None  # All milestones completed
    
    def should_check_progress(self, user: User) -> bool:
        """
        Check if it's time to evaluate progress (every 5th message).
        
        Args:
            user: User object
            
        Returns:
            True if progress check should happen, False otherwise
        """
        try:
            training_data = self._load_encrypted_training_data(user)
            if not training_data:
                return False
            
            message_count = training_data.get("message_count", 0)
            
            # Check every 5th message
            if message_count > 0 and message_count % 5 == 0:
                logger.logger.info(f"✅ Progress check triggered for user {user.id} (message #{message_count})")
                return True
            
            return False
            
        except Exception as e:
            logger.logger.error(f"Error checking progress: {e}")
            return False
    
    def increment_message_count(self, user: User):
        """
        Increment message count for progress tracking.
        
        Call this for every user message.
        
        Args:
            user: User object
        """
        try:
            training_data = self._load_encrypted_training_data(user)
            if training_data:
                training_data["message_count"] = training_data.get("message_count", 0) + 1
                self._save_encrypted_training_data(user, training_data)
                logger.logger.debug(f"Message count for user {user.id}: {training_data['message_count']}")
        except Exception as e:
            logger.logger.error(f"Error incrementing message count: {e}")
    
    def update_training_progress(self, user: User, skill_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update training progress based on skill analysis.
        
        Called every 5th message to check progress.
        
        Args:
            user: User object
            skill_analysis: Results from SkillEvaluator
            
        Returns:
            Updated training data with new progress
        """
        logger.logger.info(f"Updating training progress for user {user.id}")
        
        try:
            training_data = self._load_encrypted_training_data(user)
            if not training_data:
                return {}
            
            # Update last progress check timestamp
            training_data["last_progress_check"] = datetime.utcnow().isoformat()
            
            # Update each active training based on skill analysis
            skills_updated = skill_analysis.get("skills_updated", [])
            
            for skill_update in skills_updated:
                skill_name = skill_update.get("skill")
                new_level = skill_update.get("new_level", 0)
                
                # Find matching training
                for training_key, training_info in training_data["trainings"].items():
                    if training_info["skill_name"] == skill_name:
                        training_info["current_level"] = new_level
                        training_info["progress_percent"] = new_level * 10
                        training_info["next_milestone"] = self._get_next_milestone(
                            new_level, 
                            training_info["milestones"]
                        )
                        
                        # Update database
                        skill = self.dm.get_or_create_skill(skill_name)
                        if skill:
                            self.dm.update_training_status(
                                user.id, 
                                skill.id, 
                                "completed" if new_level >= 10 else "active"
                            )
                        
                        logger.logger.info(f"✅ Updated {skill_name}: level {new_level}/10")
            
            # Save updated training data
            self._save_encrypted_training_data(user, training_data)
            
            return training_data
            
        except Exception as e:
            logger.logger.error(f"Error updating training progress: {e}", exc_info=True)
            return {}
    
    def get_login_reminder(self, user: User) -> str:
        """
        Generate login message with training reminders.
        
        Args:
            user: User object
            
        Returns:
            Formatted login message with training status
            
        Example:
            "Welcome back, John! 🎯
            
            Your Active Trainings:
            • Empathy: Level 3/10 - Keep practicing empathetic responses!
            • Active Listening: Level 5/10 - Great progress on clarifying questions!"
        """
        try:
            training_data = self._load_encrypted_training_data(user)
            if not training_data or not training_data.get("trainings"):
                return f"Welcome back, {user.username}! 👋"
            
            reminder_parts = [f"Welcome back, {user.username}! 🎯\n"]
            
            active_trainings = [
                t for t in training_data["trainings"].values() 
                if t.get("status") == "active"
            ]
            
            if active_trainings:
                reminder_parts.append("\n**Your Active Trainings:**")
                for training in active_trainings:
                    level = training["current_level"]
                    name = training["skill_name"].replace("_", " ").title()
                    next_milestone = training.get("next_milestone")
                    
                    if next_milestone:
                        reminder_parts.append(
                            f"• **{name}**: Level {level}/10 - Next: {next_milestone}"
                        )
                    else:
                        reminder_parts.append(
                            f"• **{name}**: Level {level}/10 - 🎉 Almost mastered!"
                        )
            
            return "\n".join(reminder_parts)
            
        except Exception as e:
            logger.logger.error(f"Error generating login reminder: {e}")
            return f"Welcome back, {user.username}! 👋"
    
    def get_training_context_for_prompt(self, user: User) -> str:
        """
        Get training plan context to add to AI system prompt.
        
        Args:
            user: User object
            
        Returns:
            Formatted string with training context for system prompt
        """
        try:
            training_data = self._load_encrypted_training_data(user)
            if not training_data or not training_data.get("trainings"):
                return ""
            
            context_parts = [
                "\n🎯 **ACTIVE TRAINING PLAN**",
                f"User {user.username} is currently training in:"
            ]
            
            for training_key, training_info in training_data["trainings"].items():
                if training_info.get("status") == "active":
                    skill_name = training_info["skill_name"].replace("_", " ").title()
                    level = training_info["current_level"]
                    next_milestone = training_info.get("next_milestone")
                    
                    context_parts.append(
                        f"• **{skill_name}** (Level {level}/10): {training_info['description']}"
                    )
                    if next_milestone:
                        context_parts.append(f"  Next milestone: {next_milestone}")
            
            context_parts.extend([
                "\n**YOUR TRAINING APPROACH:**",
                "- Provide subtle examples and hints (not explicit training instructions)",
                "- Model good empathy and conversation skills in your responses",
                "- Gently guide user toward better communication patterns",
                "- Make training feel like natural, helpful conversation",
                "- Use encouraging, positive reinforcement"
            ])
            
            return "\n".join(context_parts)
            
        except Exception as e:
            logger.logger.error(f"Error getting training context: {e}")
            return ""
    
    def save_logout_progress(self, user: User, final_analysis: Optional[Dict] = None):
        """
        Save all progress data on logout.
        
        Args:
            user: User object
            final_analysis: Optional final skill analysis from conversation
        """
        logger.logger.info(f"Saving logout progress for user {user.id}")
        
        try:
            training_data = self._load_encrypted_training_data(user)
            if not training_data:
                return
            
            # Add logout timestamp
            training_data["last_logout"] = datetime.utcnow().isoformat()
            
            # If final analysis provided, update once more
            if final_analysis:
                self.update_training_progress(user, final_analysis)
            
            # Save encrypted
            self._save_encrypted_training_data(user, training_data)
            
            logger.logger.info(f"✅ Logout progress saved for user {user.id}")
            
        except Exception as e:
            logger.logger.error(f"Error saving logout progress: {e}", exc_info=True)
    
    def _load_encrypted_training_data(self, user: User) -> Optional[Dict[str, Any]]:
        """
        Load encrypted training data from SecureMemoryManager.
        
        Args:
            user: User object
            
        Returns:
            Decrypted training data or None if not found
        """
        try:
            # Create SecureMemoryManager for this user
            memory_manager = SecureMemoryManager(self.dm, user)
            
            # Load from memory system (already encrypted)
            memory_data = memory_manager.load_memory(user)
            
            if memory_data and "training_plan" in memory_data:
                return memory_data["training_plan"]
            
            return None
            
        except Exception as e:
            logger.logger.error(f"Error loading encrypted training data: {e}")
            return None
    
    def _save_encrypted_training_data(self, user: User, training_data: Dict[str, Any]):
        """
        Save training data encrypted via SecureMemoryManager.
        
        Args:
            user: User object
            training_data: Training data to encrypt and save
        """
        try:
            # Create SecureMemoryManager for this user
            memory_manager = SecureMemoryManager(self.dm, user)
            
            # Load existing memory
            memory_data = memory_manager.load_memory(user) or {}
            
            # Update training plan section
            memory_data["training_plan"] = training_data
            
            # Save encrypted
            memory_manager.save_memory(user, memory_data)
            
            logger.logger.debug(f"✅ Encrypted training data saved for user {user.id}")
            
        except Exception as e:
            logger.logger.error(f"Error saving encrypted training data: {e}", exc_info=True)
    
    def _get_empty_training_plan(self) -> Dict[str, Any]:
        """Return empty training plan structure."""
        return {
            "trainings": {},
            "message_count": 0,
            "last_progress_check": None
        }
