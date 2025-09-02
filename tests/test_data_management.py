"""
Test data management utilities for EdAgent integration tests
Provides fixtures, factories, and cleanup utilities for comprehensive testing
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock
import json
import tempfile
import os

from edagent.models.user_context import UserContext, SkillLevel, SkillLevelEnum, UserPreferences, LearningStyleEnum
from edagent.models.conversation import Message, ConversationResponse, MessageType
from edagent.models.learning import LearningPath, Milestone, DifficultyLevel, SkillAssessment
from edagent.models.content import ContentRecommendation, Platform, ContentType


class TestDataFactory:
    """Factory for creating test data objects"""
    
    @staticmethod
    def create_user_context(
        user_id: str = None,
        skill_level: SkillLevelEnum = SkillLevelEnum.BEGINNER,
        career_goals: List[str] = None,
        learning_style: LearningStyleEnum = LearningStyleEnum.VISUAL,
        time_commitment: str = "part-time",
        budget_preference: str = "free"
    ) -> UserContext:
        """Create a test user context with specified parameters"""
        
        if user_id is None:
            user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        
        if career_goals is None:
            career_goals = ["become a software developer"]
        
        preferences = UserPreferences(
            learning_style=learning_style,
            time_commitment=time_commitment,
            budget_preference=budget_preference
        )
        
        context = UserContext(
            user_id=user_id,
            career_goals=career_goals,
            learning_preferences=preferences,
            conversation_history=[]
        )
        
        # Add some default skills based on level
        if skill_level == SkillLevelEnum.BEGINNER:
            context.add_skill("basic_computer_skills", SkillLevelEnum.INTERMEDIATE, 0.8)
        elif skill_level == SkillLevelEnum.INTERMEDIATE:
            context.add_skill("programming_basics", SkillLevelEnum.INTERMEDIATE, 0.7)
            context.add_skill("html", SkillLevelEnum.INTERMEDIATE, 0.6)
        elif skill_level == SkillLevelEnum.ADVANCED:
            context.add_skill("programming_basics", SkillLevelEnum.ADVANCED, 0.9)
            context.add_skill("html", SkillLevelEnum.ADVANCED, 0.8)
            context.add_skill("css", SkillLevelEnum.ADVANCED, 0.8)
            context.add_skill("javascript", SkillLevelEnum.INTERMEDIATE, 0.7)
        
        return context
    
    @staticmethod
    def create_skill_assessment(
        user_id: str = None,
        skill_area: str = "Web Development",
        overall_level: DifficultyLevel = DifficultyLevel.BEGINNER,
        confidence_score: float = 0.6
    ) -> SkillAssessment:
        """Create a test skill assessment"""
        
        if user_id is None:
            user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        
        return SkillAssessment(
            user_id=user_id,
            skill_area=skill_area,
            overall_level=overall_level,
            confidence_score=confidence_score,
            strengths=[
                "Eager to learn",
                "Good problem-solving mindset",
                "Strong motivation"
            ],
            weaknesses=[
                "Limited technical experience",
                "Needs more practice with fundamentals",
                "Could improve debugging skills"
            ],
            recommendations=[
                "Start with HTML and CSS basics",
                "Practice coding daily",
                "Build small projects to reinforce learning",
                "Join online coding communities"
            ],
            detailed_scores={
                "html": 0.4 if overall_level == DifficultyLevel.BEGINNER else 0.7,
                "css": 0.3 if overall_level == DifficultyLevel.BEGINNER else 0.6,
                "javascript": 0.2 if overall_level == DifficultyLevel.BEGINNER else 0.5,
                "problem_solving": confidence_score,
                "debugging": confidence_score - 0.2
            }
        )
    
    @staticmethod
    def create_learning_path(
        goal: str = "become a web developer",
        difficulty: DifficultyLevel = DifficultyLevel.BEGINNER,
        num_milestones: int = 3
    ) -> LearningPath:
        """Create a test learning path with specified number of milestones"""
        
        milestones = []
        
        # Create milestones based on difficulty and goal
        if "web developer" in goal.lower():
            milestone_templates = [
                ("HTML Fundamentals", ["html_basics", "semantic_html", "forms"], 14),
                ("CSS Styling", ["css_basics", "flexbox", "responsive_design"], 21),
                ("JavaScript Basics", ["js_syntax", "dom_manipulation", "events"], 28),
                ("Frontend Frameworks", ["react_basics", "component_design", "state_management"], 35),
                ("Backend Development", ["nodejs", "express", "databases"], 42)
            ]
        elif "data scientist" in goal.lower():
            milestone_templates = [
                ("Python Fundamentals", ["python_basics", "data_types", "control_flow"], 21),
                ("Data Analysis", ["pandas", "numpy", "data_cleaning"], 28),
                ("Statistics & Math", ["statistics", "probability", "linear_algebra"], 35),
                ("Machine Learning", ["sklearn", "supervised_learning", "model_evaluation"], 42),
                ("Advanced ML", ["deep_learning", "neural_networks", "model_deployment"], 49)
            ]
        else:
            milestone_templates = [
                ("Foundation Skills", ["basics", "fundamentals"], 14),
                ("Intermediate Concepts", ["intermediate_skills"], 21),
                ("Advanced Topics", ["advanced_skills"], 28)
            ]
        
        # Create the requested number of milestones
        for i in range(min(num_milestones, len(milestone_templates))):
            title, skills, duration_days = milestone_templates[i]
            
            milestone = Milestone(
                title=title,
                description=f"Learn {title.lower()} to build a strong foundation",
                skills_to_learn=skills,
                estimated_duration=timedelta(days=duration_days),
                difficulty_level=difficulty if i == 0 else DifficultyLevel.INTERMEDIATE,
                assessment_criteria=[
                    f"Complete exercises for {title.lower()}",
                    f"Build a project demonstrating {title.lower()}",
                    "Pass knowledge assessment"
                ],
                order_index=i
            )
            
            # Add resources to each milestone
            milestone.add_resource(
                title=f"{title} Course",
                url=f"https://example.com/{title.lower().replace(' ', '-')}-course",
                resource_type="course",
                is_free=True,
                duration=timedelta(hours=20)
            )
            
            milestone.add_resource(
                title=f"{title} Documentation",
                url=f"https://docs.example.com/{title.lower().replace(' ', '-')}",
                resource_type="documentation",
                is_free=True,
                duration=timedelta(hours=5)
            )
            
            milestones.append(milestone)
        
        # Calculate total duration
        total_duration = sum((m.estimated_duration for m in milestones), timedelta())
        
        return LearningPath(
            title=f"Complete {goal.title()} Path",
            description=f"Comprehensive learning path to {goal}",
            goal=goal,
            milestones=milestones,
            estimated_duration=total_duration,
            difficulty_level=difficulty,
            target_skills=[skill for milestone in milestones for skill in milestone.skills_to_learn],
            prerequisites=["Basic computer literacy", "Motivation to learn"] if difficulty == DifficultyLevel.BEGINNER else []
        )
    
    @staticmethod
    def create_conversation_history(
        user_id: str,
        num_messages: int = 5,
        conversation_type: str = "general"
    ) -> List[Message]:
        """Create a conversation history for testing"""
        
        messages = []
        
        if conversation_type == "skill_assessment":
            message_pairs = [
                ("I want to learn web development", "Great! Let's start by assessing your current skills."),
                ("I have no programming experience", "That's perfectly fine! Everyone starts somewhere."),
                ("What should I learn first?", "I recommend starting with HTML to understand web structure."),
                ("How long will it take to learn?", "With consistent practice, you can learn basics in 2-3 months."),
                ("Do you have any free resources?", "Yes! I can recommend excellent free courses and tutorials.")
            ]
        elif conversation_type == "learning_path":
            message_pairs = [
                ("I want to become a data scientist", "Excellent choice! Data science is a growing field."),
                ("What skills do I need?", "You'll need Python, statistics, and machine learning knowledge."),
                ("Can you create a learning plan?", "Absolutely! Let me create a personalized learning path."),
                ("How much time should I dedicate?", "I recommend 10-15 hours per week for steady progress."),
                ("What about job prospects?", "Data science has excellent job prospects across many industries.")
            ]
        else:  # general conversation
            message_pairs = [
                ("Hello!", "Hi there! I'm EdAgent, your AI career coaching assistant."),
                ("I'm new to programming", "Welcome! I'm here to help you on your programming journey."),
                ("What can you help me with?", "I can help with learning paths, skill assessments, and career advice."),
                ("That sounds great!", "I'm excited to work with you! What would you like to explore first?"),
                ("Let's start learning!", "Perfect! Let's begin your learning adventure together.")
            ]
        
        # Create messages from the pairs
        for i, (user_msg, assistant_msg) in enumerate(message_pairs[:num_messages]):
            # User message
            messages.append(Message(
                content=user_msg,
                message_type=MessageType.USER,
                timestamp=datetime.now() - timedelta(minutes=(num_messages - i) * 2)
            ))
            
            # Assistant message
            messages.append(Message(
                content=assistant_msg,
                message_type=MessageType.ASSISTANT,
                timestamp=datetime.now() - timedelta(minutes=(num_messages - i) * 2 - 1)
            ))
        
        return messages
    
    @staticmethod
    def create_content_recommendations(
        skill: str = "python",
        level: str = "beginner",
        num_recommendations: int = 5,
        include_paid: bool = False
    ) -> List[ContentRecommendation]:
        """Create test content recommendations"""
        
        recommendations = []
        
        # Base content templates
        content_templates = [
            {
                "title": f"{skill.title()} for Beginners",
                "platform": "youtube",
                "content_type": "video",
                "duration_hours": 3,
                "rating": 4.8,
                "is_free": True
            },
            {
                "title": f"Complete {skill.title()} Course",
                "platform": "freecodecamp",
                "content_type": "interactive",
                "duration_hours": 20,
                "rating": 4.9,
                "is_free": True
            },
            {
                "title": f"{skill.title()} Documentation",
                "platform": "other",
                "content_type": "documentation",
                "duration_hours": 10,
                "rating": 4.7,
                "is_free": True
            },
            {
                "title": f"Learn {skill.title()} by Building Projects",
                "platform": "github",
                "content_type": "tutorial",
                "duration_hours": 15,
                "rating": 4.6,
                "is_free": True
            },
            {
                "title": f"{skill.title()} Masterclass",
                "platform": "udemy",
                "content_type": "course",
                "duration_hours": 40,
                "rating": 4.5,
                "is_free": False
            }
        ]
        
        for i, template in enumerate(content_templates[:num_recommendations]):
            if not include_paid and not template["is_free"]:
                continue
            
            recommendation = ContentRecommendation(
                title=template["title"],
                url=f"https://example.com/{skill}-{level}-{i}",
                platform=Platform(template["platform"]),
                content_type=ContentType(template["content_type"]),
                duration=timedelta(hours=template["duration_hours"]),
                rating=template["rating"],
                is_free=template["is_free"],
                skill_match_score=0.9 - (i * 0.1),  # Decreasing relevance
                difficulty_level=level,
                description=f"Learn {skill} with this comprehensive {template['content_type']}",
                tags=[skill, level, template["content_type"]]
            )
            
            recommendations.append(recommendation)
        
        return recommendations


class TestDatabaseManager:
    """Manage test database operations and cleanup"""
    
    def __init__(self):
        self.created_users: List[str] = []
        self.created_sessions: List[str] = []
        self.created_conversations: List[str] = []
        self.created_learning_paths: List[str] = []
        self.created_assessments: List[str] = []
        self.temp_files: List[str] = []
    
    def create_temp_database(self) -> str:
        """Create a temporary database file for testing"""
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_db.close()
        self.temp_files.append(temp_db.name)
        return temp_db.name
    
    def track_user(self, user_id: str):
        """Track a user for cleanup"""
        self.created_users.append(user_id)
    
    def track_session(self, session_id: str):
        """Track a session for cleanup"""
        self.created_sessions.append(session_id)
    
    def track_conversation(self, conversation_id: str):
        """Track a conversation for cleanup"""
        self.created_conversations.append(conversation_id)
    
    def track_learning_path(self, path_id: str):
        """Track a learning path for cleanup"""
        self.created_learning_paths.append(path_id)
    
    def track_assessment(self, assessment_id: str):
        """Track an assessment for cleanup"""
        self.created_assessments.append(assessment_id)
    
    async def cleanup_all(self):
        """Clean up all tracked test data"""
        # In a real implementation, this would execute database cleanup queries
        # For now, we'll just clear the tracking lists and remove temp files
        
        self.created_users.clear()
        self.created_sessions.clear()
        self.created_conversations.clear()
        self.created_learning_paths.clear()
        self.created_assessments.clear()
        
        # Remove temporary files
        for temp_file in self.temp_files:
            try:
                os.unlink(temp_file)
            except FileNotFoundError:
                pass
        self.temp_files.clear()
    
    def get_cleanup_summary(self) -> Dict[str, int]:
        """Get summary of items to be cleaned up"""
        return {
            "users": len(self.created_users),
            "sessions": len(self.created_sessions),
            "conversations": len(self.created_conversations),
            "learning_paths": len(self.created_learning_paths),
            "assessments": len(self.created_assessments),
            "temp_files": len(self.temp_files)
        }


class MockServiceManager:
    """Manage mock services for integration testing"""
    
    def __init__(self):
        self.ai_service_mock = None
        self.content_recommender_mock = None
        self.user_context_manager_mock = None
        self.conversation_manager_mock = None
    
    def setup_ai_service_mock(self, response_delay: float = 0.1):
        """Set up AI service mock with realistic behavior"""
        mock = MagicMock()
        
        async def mock_generate_response(message: str, context: UserContext = None):
            await asyncio.sleep(response_delay)  # Simulate API call delay
            
            # Generate contextual responses based on message content
            if "hello" in message.lower() or "hi" in message.lower():
                return "Hello! I'm EdAgent, your AI career coaching assistant. How can I help you today?"
            elif "learn" in message.lower() and "python" in message.lower():
                return "Python is an excellent choice for beginners! I can help you create a learning path."
            elif "assessment" in message.lower() or "skills" in message.lower():
                return "I'd be happy to assess your current skills. Let's start with a few questions."
            elif "career" in message.lower():
                return "Career development is my specialty! What field are you interested in?"
            else:
                return f"Thank you for your question about '{message[:50]}...'. I'm here to help with your learning journey!"
        
        async def mock_assess_skills(responses: List[str]):
            await asyncio.sleep(response_delay * 2)  # Assessment takes longer
            
            # Analyze responses to determine skill level
            total_experience = sum(1 for response in responses if any(
                word in response.lower() for word in ["yes", "know", "experience", "familiar"]
            ))
            
            if total_experience == 0:
                level = DifficultyLevel.BEGINNER
                confidence = 0.2
            elif total_experience <= len(responses) // 2:
                level = DifficultyLevel.BEGINNER
                confidence = 0.5
            else:
                level = DifficultyLevel.INTERMEDIATE
                confidence = 0.7
            
            return TestDataFactory.create_skill_assessment(
                user_id=f"test_user_{uuid.uuid4().hex[:8]}",
                overall_level=level,
                confidence_score=confidence
            )
        
        async def mock_create_learning_path(goal: str, current_skills: Dict):
            await asyncio.sleep(response_delay * 3)  # Path creation takes longest
            
            # Determine difficulty based on existing skills
            if not current_skills:
                difficulty = DifficultyLevel.BEGINNER
            elif len(current_skills) < 3:
                difficulty = DifficultyLevel.BEGINNER
            else:
                difficulty = DifficultyLevel.INTERMEDIATE
            
            return TestDataFactory.create_learning_path(
                goal=goal,
                difficulty=difficulty,
                num_milestones=4
            )
        
        mock.generate_response = mock_generate_response
        mock.assess_skills = mock_assess_skills
        mock.create_learning_path = mock_create_learning_path
        
        self.ai_service_mock = mock
        return mock
    
    def setup_content_recommender_mock(self, response_delay: float = 0.05):
        """Set up content recommender mock"""
        mock = MagicMock()
        
        async def mock_get_recommendations(skill: str, level: str, limit: int = 5):
            await asyncio.sleep(response_delay)
            return TestDataFactory.create_content_recommendations(
                skill=skill,
                level=level,
                num_recommendations=limit,
                include_paid=True
            )
        
        async def mock_search_youtube_content(query: str, filters: Dict = None):
            await asyncio.sleep(response_delay)
            return TestDataFactory.create_content_recommendations(
                skill=query.split()[0] if query else "programming",
                level="beginner",
                num_recommendations=3
            )
        
        mock.get_recommendations = mock_get_recommendations
        mock.search_youtube_content = mock_search_youtube_content
        
        self.content_recommender_mock = mock
        return mock
    
    def setup_user_context_manager_mock(self):
        """Set up user context manager mock"""
        mock = MagicMock()
        
        # Store contexts in memory for the test session
        self._user_contexts = {}
        
        async def mock_get_user_context(user_id: str):
            if user_id not in self._user_contexts:
                self._user_contexts[user_id] = TestDataFactory.create_user_context(user_id=user_id)
            return self._user_contexts[user_id]
        
        async def mock_update_user_context(user_id: str, context: UserContext):
            self._user_contexts[user_id] = context
        
        async def mock_save_learning_path(user_id: str, learning_path: LearningPath):
            return f"path_{uuid.uuid4().hex[:8]}"
        
        mock.get_user_context = mock_get_user_context
        mock.update_user_context = mock_update_user_context
        mock.save_learning_path = mock_save_learning_path
        
        self.user_context_manager_mock = mock
        return mock
    
    def get_all_mocks(self) -> Dict[str, Any]:
        """Get all configured mocks"""
        return {
            "ai_service": self.ai_service_mock,
            "content_recommender": self.content_recommender_mock,
            "user_context_manager": self.user_context_manager_mock,
            "conversation_manager": self.conversation_manager_mock
        }


# Pytest fixtures for easy use in tests
@pytest.fixture
def test_data_factory():
    """Provide test data factory"""
    return TestDataFactory()

@pytest.fixture
def test_db_manager():
    """Provide test database manager with cleanup"""
    manager = TestDatabaseManager()
    yield manager
    # Cleanup after test
    asyncio.run(manager.cleanup_all())

@pytest.fixture
def mock_service_manager():
    """Provide mock service manager"""
    return MockServiceManager()

@pytest.fixture
def sample_user_context(test_data_factory):
    """Provide a sample user context"""
    return test_data_factory.create_user_context()

@pytest.fixture
def sample_learning_path(test_data_factory):
    """Provide a sample learning path"""
    return test_data_factory.create_learning_path()

@pytest.fixture
def sample_skill_assessment(test_data_factory):
    """Provide a sample skill assessment"""
    return test_data_factory.create_skill_assessment(user_id="sample_user_123")

@pytest.fixture
def sample_conversation_history(test_data_factory, sample_user_context):
    """Provide sample conversation history"""
    return test_data_factory.create_conversation_history(
        user_id=sample_user_context.user_id,
        num_messages=3,
        conversation_type="general"
    )

@pytest.fixture
def sample_content_recommendations(test_data_factory):
    """Provide sample content recommendations"""
    return test_data_factory.create_content_recommendations(
        skill="python",
        level="beginner",
        num_recommendations=3
    )


# Test the test data management system itself
class TestTestDataManagement:
    """Test the test data management utilities"""
    
    def test_user_context_factory(self, test_data_factory):
        """Test user context creation"""
        context = test_data_factory.create_user_context(
            skill_level=SkillLevelEnum.INTERMEDIATE,
            career_goals=["become a data scientist"],
            learning_style=LearningStyleEnum.KINESTHETIC
        )
        
        assert context.user_id.startswith("test_user_")
        assert "become a data scientist" in context.career_goals
        assert context.learning_preferences.learning_style == LearningStyleEnum.KINESTHETIC
        assert len(context.current_skills) > 0  # Should have some default skills
    
    def test_learning_path_factory(self, test_data_factory):
        """Test learning path creation"""
        path = test_data_factory.create_learning_path(
            goal="become a web developer",
            difficulty=DifficultyLevel.BEGINNER,
            num_milestones=4
        )
        
        assert path.goal == "become a web developer"
        assert path.difficulty_level == DifficultyLevel.BEGINNER
        assert len(path.milestones) == 4
        assert all(milestone.order_index == i for i, milestone in enumerate(path.milestones))
        
        # Check that milestones have resources
        for milestone in path.milestones:
            assert len(milestone.resources) > 0
    
    def test_skill_assessment_factory(self, test_data_factory):
        """Test skill assessment creation"""
        assessment = test_data_factory.create_skill_assessment(
            user_id="test_user_456",
            skill_area="Data Science",
            overall_level=DifficultyLevel.INTERMEDIATE,
            confidence_score=0.8
        )
        
        assert assessment.user_id == "test_user_456"
        assert assessment.skill_area == "Data Science"
        assert assessment.overall_level == DifficultyLevel.INTERMEDIATE
        assert assessment.confidence_score == 0.8
        assert len(assessment.strengths) > 0
        assert len(assessment.weaknesses) > 0
        assert len(assessment.recommendations) > 0
        assert len(assessment.detailed_scores) > 0
    
    def test_conversation_history_factory(self, test_data_factory):
        """Test conversation history creation"""
        user_id = "test_user_123"
        history = test_data_factory.create_conversation_history(
            user_id=user_id,
            num_messages=3,
            conversation_type="skill_assessment"
        )
        
        # Should have user and assistant messages
        assert len(history) == 6  # 3 pairs of messages
        assert all(msg.content for msg in history)  # All messages should have content
        
        # Should alternate between user and assistant
        message_types = [msg.message_type for msg in history]
        expected_types = [MessageType.USER, MessageType.ASSISTANT] * 3
        assert message_types == expected_types
    
    def test_content_recommendations_factory(self, test_data_factory):
        """Test content recommendations creation"""
        recommendations = test_data_factory.create_content_recommendations(
            skill="javascript",
            level="intermediate",
            num_recommendations=3,
            include_paid=True
        )
        
        assert len(recommendations) == 3
        assert all("javascript" in rec.title.lower() for rec in recommendations)
        assert all(rec.difficulty_level == "intermediate" for rec in recommendations)
        
        # Should have mix of free and paid content when include_paid=True
        free_count = sum(1 for rec in recommendations if rec.is_free)
        paid_count = sum(1 for rec in recommendations if not rec.is_free)
        assert free_count > 0  # Should have some free content
    
    def test_database_manager_tracking(self, test_db_manager):
        """Test database manager tracking functionality"""
        # Track various items
        test_db_manager.track_user("user_1")
        test_db_manager.track_user("user_2")
        test_db_manager.track_session("session_1")
        test_db_manager.track_conversation("conv_1")
        test_db_manager.track_learning_path("path_1")
        
        summary = test_db_manager.get_cleanup_summary()
        
        assert summary["users"] == 2
        assert summary["sessions"] == 1
        assert summary["conversations"] == 1
        assert summary["learning_paths"] == 1
    
    def test_mock_service_manager(self, mock_service_manager):
        """Test mock service manager setup"""
        # Set up mocks
        ai_mock = mock_service_manager.setup_ai_service_mock()
        content_mock = mock_service_manager.setup_content_recommender_mock()
        context_mock = mock_service_manager.setup_user_context_manager_mock()
        
        # Verify mocks are configured
        assert ai_mock is not None
        assert content_mock is not None
        assert context_mock is not None
        
        all_mocks = mock_service_manager.get_all_mocks()
        assert "ai_service" in all_mocks
        assert "content_recommender" in all_mocks
        assert "user_context_manager" in all_mocks


if __name__ == "__main__":
    pytest.main([__file__, "-v"])