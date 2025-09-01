"""
Unit tests for user context and skill models
"""

import pytest
import json
from datetime import datetime, timedelta
from edagent.models.user_context import (
    SkillLevel, 
    UserPreferences, 
    UserContext,
    SkillLevelEnum,
    LearningStyleEnum
)


class TestSkillLevel:
    """Test cases for SkillLevel model"""
    
    def test_valid_skill_level_creation(self):
        """Test creating a valid skill level"""
        skill = SkillLevel(
            skill_name="Python",
            level=SkillLevelEnum.BEGINNER,
            confidence_score=0.7
        )
        
        assert skill.skill_name == "Python"
        assert skill.level == SkillLevelEnum.BEGINNER
        assert skill.confidence_score == 0.7
        assert isinstance(skill.last_updated, datetime)
    
    def test_skill_level_with_string_enum(self):
        """Test creating skill level with string enum value"""
        skill = SkillLevel(
            skill_name="JavaScript",
            level="intermediate",
            confidence_score=0.8
        )
        
        assert skill.level == SkillLevelEnum.INTERMEDIATE
    
    def test_invalid_skill_name(self):
        """Test validation with invalid skill name"""
        with pytest.raises(ValueError, match="Skill name cannot be empty"):
            SkillLevel(
                skill_name="",
                level=SkillLevelEnum.BEGINNER,
                confidence_score=0.5
            )
        
        with pytest.raises(ValueError, match="Skill name cannot be empty"):
            SkillLevel(
                skill_name="   ",
                level=SkillLevelEnum.BEGINNER,
                confidence_score=0.5
            )
    
    def test_invalid_skill_level(self):
        """Test validation with invalid skill level"""
        with pytest.raises(ValueError, match="Invalid skill level"):
            SkillLevel(
                skill_name="Python",
                level="expert",  # Invalid level
                confidence_score=0.5
            )
    
    def test_invalid_confidence_score(self):
        """Test validation with invalid confidence score"""
        with pytest.raises(ValueError, match="Confidence score must be between 0.0 and 1.0"):
            SkillLevel(
                skill_name="Python",
                level=SkillLevelEnum.BEGINNER,
                confidence_score=1.5
            )
        
        with pytest.raises(ValueError, match="Confidence score must be between 0.0 and 1.0"):
            SkillLevel(
                skill_name="Python",
                level=SkillLevelEnum.BEGINNER,
                confidence_score=-0.1
            )
    
    def test_skill_level_serialization(self):
        """Test serialization to dictionary"""
        now = datetime.now()
        skill = SkillLevel(
            skill_name="React",
            level=SkillLevelEnum.ADVANCED,
            confidence_score=0.9,
            last_updated=now
        )
        
        data = skill.to_dict()
        expected = {
            "skill_name": "React",
            "level": "advanced",
            "confidence_score": 0.9,
            "last_updated": now.isoformat()
        }
        
        assert data == expected
    
    def test_skill_level_deserialization(self):
        """Test deserialization from dictionary"""
        now = datetime.now()
        data = {
            "skill_name": "Vue.js",
            "level": "intermediate",
            "confidence_score": 0.75,
            "last_updated": now.isoformat()
        }
        
        skill = SkillLevel.from_dict(data)
        
        assert skill.skill_name == "Vue.js"
        assert skill.level == SkillLevelEnum.INTERMEDIATE
        assert skill.confidence_score == 0.75
        assert skill.last_updated == now


class TestUserPreferences:
    """Test cases for UserPreferences model"""
    
    def test_valid_preferences_creation(self):
        """Test creating valid user preferences"""
        prefs = UserPreferences(
            learning_style=LearningStyleEnum.VISUAL,
            time_commitment="3-4 hours/week",
            budget_preference="free",
            preferred_platforms=["YouTube", "Coursera"],
            content_types=["video", "interactive"],
            difficulty_preference="gradual"
        )
        
        assert prefs.learning_style == LearningStyleEnum.VISUAL
        assert prefs.time_commitment == "3-4 hours/week"
        assert prefs.budget_preference == "free"
        assert prefs.preferred_platforms == ["YouTube", "Coursera"]
        assert prefs.content_types == ["video", "interactive"]
        assert prefs.difficulty_preference == "gradual"
    
    def test_default_preferences(self):
        """Test default values for preferences"""
        prefs = UserPreferences(
            learning_style=LearningStyleEnum.AUDITORY,
            time_commitment="2 hours/week"
        )
        
        assert prefs.budget_preference == "free"
        assert prefs.preferred_platforms == []
        assert prefs.content_types == ["video", "article", "interactive"]
        assert prefs.difficulty_preference == "gradual"
    
    def test_preferences_with_string_enum(self):
        """Test creating preferences with string enum value"""
        prefs = UserPreferences(
            learning_style="kinesthetic",
            time_commitment="5 hours/week"
        )
        
        assert prefs.learning_style == LearningStyleEnum.KINESTHETIC
    
    def test_invalid_learning_style(self):
        """Test validation with invalid learning style"""
        with pytest.raises(ValueError, match="Invalid learning style"):
            UserPreferences(
                learning_style="invalid_style",
                time_commitment="2 hours/week"
            )
    
    def test_invalid_budget_preference(self):
        """Test validation with invalid budget preference"""
        with pytest.raises(ValueError, match="Budget preference must be"):
            UserPreferences(
                learning_style=LearningStyleEnum.VISUAL,
                time_commitment="2 hours/week",
                budget_preference="expensive"
            )
    
    def test_invalid_content_type(self):
        """Test validation with invalid content type"""
        with pytest.raises(ValueError, match="Invalid content type"):
            UserPreferences(
                learning_style=LearningStyleEnum.VISUAL,
                time_commitment="2 hours/week",
                content_types=["video", "invalid_type"]
            )
    
    def test_empty_time_commitment(self):
        """Test validation with empty time commitment"""
        with pytest.raises(ValueError, match="Time commitment cannot be empty"):
            UserPreferences(
                learning_style=LearningStyleEnum.VISUAL,
                time_commitment=""
            )
    
    def test_preferences_serialization(self):
        """Test serialization to dictionary"""
        prefs = UserPreferences(
            learning_style=LearningStyleEnum.READING,
            time_commitment="1-2 hours/day",
            budget_preference="low_cost",
            preferred_platforms=["Udemy"],
            content_types=["article", "book"],
            difficulty_preference="challenging"
        )
        
        data = prefs.to_dict()
        expected = {
            "learning_style": "reading",
            "time_commitment": "1-2 hours/day",
            "budget_preference": "low_cost",
            "preferred_platforms": ["Udemy"],
            "content_types": ["article", "book"],
            "difficulty_preference": "challenging"
        }
        
        assert data == expected
    
    def test_preferences_deserialization(self):
        """Test deserialization from dictionary"""
        data = {
            "learning_style": "auditory",
            "time_commitment": "30 minutes/day",
            "budget_preference": "any",
            "preferred_platforms": ["Spotify", "Audible"],
            "content_types": ["video"],
            "difficulty_preference": "mixed"
        }
        
        prefs = UserPreferences.from_dict(data)
        
        assert prefs.learning_style == LearningStyleEnum.AUDITORY
        assert prefs.time_commitment == "30 minutes/day"
        assert prefs.budget_preference == "any"
        assert prefs.preferred_platforms == ["Spotify", "Audible"]
        assert prefs.content_types == ["video"]
        assert prefs.difficulty_preference == "mixed"


class TestUserContext:
    """Test cases for UserContext model"""
    
    def test_valid_user_context_creation(self):
        """Test creating a valid user context"""
        prefs = UserPreferences(
            learning_style=LearningStyleEnum.VISUAL,
            time_commitment="2 hours/week"
        )
        
        context = UserContext(
            user_id="user123",
            career_goals=["become a data scientist"],
            learning_preferences=prefs
        )
        
        assert context.user_id == "user123"
        assert context.career_goals == ["become a data scientist"]
        assert context.learning_preferences == prefs
        assert context.current_skills == {}
        assert context.conversation_history == []
        assert context.assessment_results is None
        assert isinstance(context.created_at, datetime)
        assert isinstance(context.last_active, datetime)
    
    def test_invalid_user_id(self):
        """Test validation with invalid user ID"""
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            UserContext(user_id="")
        
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            UserContext(user_id="   ")
    
    def test_add_skill(self):
        """Test adding a skill to user context"""
        context = UserContext(user_id="user123")
        original_last_active = context.last_active
        
        # Add a small delay to ensure timestamp difference
        import time
        time.sleep(0.001)
        
        context.add_skill("Python", SkillLevelEnum.INTERMEDIATE, 0.8)
        
        assert "Python" in context.current_skills
        skill = context.current_skills["Python"]
        assert skill.skill_name == "Python"
        assert skill.level == SkillLevelEnum.INTERMEDIATE
        assert skill.confidence_score == 0.8
        assert context.last_active > original_last_active
    
    def test_get_skill_level(self):
        """Test getting skill level"""
        context = UserContext(user_id="user123")
        context.add_skill("JavaScript", SkillLevelEnum.BEGINNER, 0.6)
        
        skill = context.get_skill_level("JavaScript")
        assert skill is not None
        assert skill.skill_name == "JavaScript"
        assert skill.level == SkillLevelEnum.BEGINNER
        
        # Test non-existent skill
        assert context.get_skill_level("NonExistent") is None
    
    def test_update_last_active(self):
        """Test updating last active timestamp"""
        context = UserContext(user_id="user123")
        original_last_active = context.last_active
        
        import time
        time.sleep(0.001)
        
        context.update_last_active()
        assert context.last_active > original_last_active
    
    def test_user_context_serialization(self):
        """Test serialization to dictionary"""
        prefs = UserPreferences(
            learning_style=LearningStyleEnum.KINESTHETIC,
            time_commitment="1 hour/day"
        )
        
        context = UserContext(
            user_id="user456",
            career_goals=["learn web development"],
            learning_preferences=prefs
        )
        context.add_skill("HTML", SkillLevelEnum.ADVANCED, 0.95)
        
        data = context.to_dict()
        
        assert data["user_id"] == "user456"
        assert data["career_goals"] == ["learn web development"]
        assert "learning_preferences" in data
        assert "current_skills" in data
        assert "HTML" in data["current_skills"]
        assert isinstance(data["created_at"], str)
        assert isinstance(data["last_active"], str)
    
    def test_user_context_deserialization(self):
        """Test deserialization from dictionary"""
        now = datetime.now()
        data = {
            "user_id": "user789",
            "current_skills": {
                "CSS": {
                    "skill_name": "CSS",
                    "level": "intermediate",
                    "confidence_score": 0.7,
                    "last_updated": now.isoformat()
                }
            },
            "career_goals": ["become a frontend developer"],
            "learning_preferences": {
                "learning_style": "visual",
                "time_commitment": "3 hours/week",
                "budget_preference": "free",
                "preferred_platforms": [],
                "content_types": ["video", "article", "interactive"],
                "difficulty_preference": "gradual"
            },
            "conversation_history": [],
            "assessment_results": None,
            "created_at": now.isoformat(),
            "last_active": now.isoformat()
        }
        
        context = UserContext.from_dict(data)
        
        assert context.user_id == "user789"
        assert context.career_goals == ["become a frontend developer"]
        assert context.learning_preferences is not None
        assert context.learning_preferences.learning_style == LearningStyleEnum.VISUAL
        assert "CSS" in context.current_skills
        assert context.current_skills["CSS"].level == SkillLevelEnum.INTERMEDIATE
    
    def test_json_serialization_roundtrip(self):
        """Test JSON serialization and deserialization roundtrip"""
        prefs = UserPreferences(
            learning_style=LearningStyleEnum.AUDITORY,
            time_commitment="2-3 hours/week",
            budget_preference="low_cost"
        )
        
        original_context = UserContext(
            user_id="roundtrip_user",
            career_goals=["master machine learning"],
            learning_preferences=prefs
        )
        original_context.add_skill("Statistics", SkillLevelEnum.INTERMEDIATE, 0.75)
        
        # Serialize to JSON
        json_str = original_context.to_json()
        
        # Deserialize from JSON
        restored_context = UserContext.from_json(json_str)
        
        # Verify all data is preserved
        assert restored_context.user_id == original_context.user_id
        assert restored_context.career_goals == original_context.career_goals
        assert restored_context.learning_preferences.learning_style == original_context.learning_preferences.learning_style
        assert "Statistics" in restored_context.current_skills
        assert restored_context.current_skills["Statistics"].confidence_score == 0.75


if __name__ == "__main__":
    pytest.main([__file__])