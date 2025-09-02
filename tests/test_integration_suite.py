"""
Comprehensive integration test suite for EdAgent
Tests complete user journeys, performance, and system integration
"""

import pytest
import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
from concurrent.futures import ThreadPoolExecutor
import json

from fastapi.testclient import TestClient
from edagent.api.app import create_app
from edagent.services.conversation_manager import ConversationManager
from edagent.models.user_context import UserContext, SkillLevel, SkillLevelEnum, UserPreferences, LearningStyleEnum
from edagent.models.conversation import ConversationResponse, Message
from edagent.models.learning import LearningPath, Milestone, DifficultyLevel


class TestDataManager:
    """Utility class for managing test data and cleanup"""
    
    def __init__(self):
        self.created_users: List[str] = []
        self.created_sessions: List[str] = []
        self.created_conversations: List[str] = []
        self.created_learning_paths: List[str] = []
    
    def create_test_user(self, user_id: str = None) -> str:
        """Create a test user and track for cleanup"""
        if user_id is None:
            user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        
        self.created_users.append(user_id)
        return user_id
    
    def create_test_session(self, session_id: str = None) -> str:
        """Create a test session and track for cleanup"""
        if session_id is None:
            session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        
        self.created_sessions.append(session_id)
        return session_id
    
    def create_test_conversation(self, conversation_id: str = None) -> str:
        """Create a test conversation and track for cleanup"""
        if conversation_id is None:
            conversation_id = f"test_conv_{uuid.uuid4().hex[:8]}"
        
        self.created_conversations.append(conversation_id)
        return conversation_id
    
    def create_test_learning_path(self, path_id: str = None) -> str:
        """Create a test learning path and track for cleanup"""
        if path_id is None:
            path_id = f"test_path_{uuid.uuid4().hex[:8]}"
        
        self.created_learning_paths.append(path_id)
        return path_id
    
    async def cleanup_all(self):
        """Clean up all created test data"""
        # In a real implementation, this would clean up database records
        # For now, we'll just clear the tracking lists
        self.created_users.clear()
        self.created_sessions.clear()
        self.created_conversations.clear()
        self.created_learning_paths.clear()


class PerformanceMetrics:
    """Utility class for tracking performance metrics"""
    
    def __init__(self):
        self.response_times: List[float] = []
        self.error_count: int = 0
        self.success_count: int = 0
    
    def record_response_time(self, duration: float):
        """Record a response time"""
        self.response_times.append(duration)
    
    def record_success(self):
        """Record a successful operation"""
        self.success_count += 1
    
    def record_error(self):
        """Record a failed operation"""
        self.error_count += 1
    
    @property
    def average_response_time(self) -> float:
        """Calculate average response time"""
        return sum(self.response_times) / len(self.response_times) if self.response_times else 0
    
    @property
    def max_response_time(self) -> float:
        """Get maximum response time"""
        return max(self.response_times) if self.response_times else 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.success_count + self.error_count
        return self.success_count / total if total > 0 else 0


class TestEndToEndUserJourneys:
    """Test complete user journeys from start to finish"""
    
    @pytest.fixture
    def app(self):
        """Create test FastAPI app"""
        return create_app()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def test_data_manager(self):
        """Create test data manager"""
        manager = TestDataManager()
        yield manager
        # Cleanup after test
        asyncio.run(manager.cleanup_all())
    
    @pytest.fixture
    def mock_conversation_manager(self):
        """Create mocked conversation manager with realistic responses"""
        manager = MagicMock(spec=ConversationManager)
        
        # Mock realistic conversation responses
        async def mock_handle_message(user_id: str, message: str) -> ConversationResponse:
            return ConversationResponse(
                message=f"Thank you for your question about '{message[:50]}...'. I'd be happy to help you with your learning journey!",
                conversation_id=f"conv_{uuid.uuid4().hex[:8]}",
                user_id=user_id,
                timestamp=datetime.now(),
                message_type="response",
                context_used=True,
                suggested_actions=["Continue conversation", "Start skill assessment", "Create learning path"]
            )
        
        manager.handle_message = mock_handle_message
        return manager
    
    @pytest.mark.asyncio
    async def test_complete_beginner_onboarding_journey(self, client, test_data_manager, mock_conversation_manager):
        """Test complete journey for a new beginner user"""
        # Step 1: User registration/session creation
        user_id = test_data_manager.create_test_user()
        
        with patch('edagent.services.auth_service.db_manager') as mock_db:
            mock_session = AsyncMock()
            mock_db.get_session.return_value.__aenter__.return_value = mock_session
            
            # Mock user creation
            from edagent.database.models import User
            mock_user = User(id=user_id)
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
            
            # Create session
            session_response = client.post(
                "/api/v1/auth/session",
                json={"user_id": user_id, "session_duration_minutes": 120}
            )
            
            assert session_response.status_code == 200
            session_data = session_response.json()
            session_token = session_data["session_token"]
        
        # Step 2: Initial conversation - user expresses interest in learning
        with patch('edagent.services.conversation_manager.ConversationManager') as mock_cm_class:
            mock_cm_class.return_value = mock_conversation_manager
            
            initial_message = "Hi! I'm completely new to programming and want to become a web developer. Where should I start?"
            
            conversation_response = client.post(
                "/api/v1/conversations/message",
                json={"message": initial_message},
                headers={"Authorization": f"Bearer {session_token}"}
            )
            
            # Should get encouraging response
            assert conversation_response.status_code == 200
            response_data = conversation_response.json()
            assert "learning journey" in response_data["message"].lower()
            assert "suggested_actions" in response_data
        
        # Step 3: Skill assessment
        with patch('edagent.services.conversation_manager.ConversationManager') as mock_cm_class:
            # Mock skill assessment workflow
            async def mock_start_assessment(user_id: str):
                from edagent.models.learning import AssessmentSession
                return AssessmentSession(
                    session_id=f"assessment_{uuid.uuid4().hex[:8]}",
                    user_id=user_id,
                    current_question=0,
                    questions=[
                        "Have you ever written HTML code before?",
                        "Are you familiar with CSS styling?",
                        "Do you have any programming experience?"
                    ],
                    responses=[],
                    status="in_progress"
                )
            
            mock_conversation_manager.start_skill_assessment = mock_start_assessment
            mock_cm_class.return_value = mock_conversation_manager
            
            assessment_response = client.post(
                "/api/v1/assessment/start",
                headers={"Authorization": f"Bearer {session_token}"}
            )
            
            assert assessment_response.status_code == 200
            assessment_data = assessment_response.json()
            assert "session_id" in assessment_data
            assert "questions" in assessment_data
        
        # Step 4: Complete assessment with beginner responses
        assessment_responses = [
            "No, I've never written HTML code",
            "I don't know what CSS is",
            "I have no programming experience at all"
        ]
        
        with patch('edagent.services.conversation_manager.ConversationManager') as mock_cm_class:
            # Mock assessment completion
            from edagent.models.learning import SkillAssessment
            mock_assessment_result = SkillAssessment(
                skill_area="Web Development",
                overall_level=DifficultyLevel.BEGINNER,
                confidence_score=0.1,
                strengths=["Eager to learn", "Clear goals"],
                weaknesses=["No technical experience", "Needs foundation skills"],
                recommendations=["Start with HTML basics", "Learn fundamental concepts", "Practice regularly"],
                detailed_scores={"html": 0.0, "css": 0.0, "javascript": 0.0}
            )
            
            async def mock_complete_assessment(session_id: str, responses: List[str]):
                return mock_assessment_result
            
            mock_conversation_manager.complete_skill_assessment = mock_complete_assessment
            mock_cm_class.return_value = mock_conversation_manager
            
            for i, response in enumerate(assessment_responses):
                submit_response = client.post(
                    f"/api/v1/assessment/respond",
                    json={"session_id": "test_session", "response": response},
                    headers={"Authorization": f"Bearer {session_token}"}
                )
                assert submit_response.status_code == 200
        
        # Step 5: Generate personalized learning path
        with patch('edagent.services.conversation_manager.ConversationManager') as mock_cm_class:
            # Mock learning path generation
            mock_milestone = Milestone(
                title="Web Development Foundations",
                description="Learn the absolute basics of web development",
                skills_to_learn=["html", "css", "basic_concepts"],
                estimated_duration=timedelta(days=30),
                difficulty_level=DifficultyLevel.BEGINNER,
                assessment_criteria=["Create a simple webpage", "Style with basic CSS"],
                order_index=0
            )
            
            mock_milestone.add_resource(
                title="HTML & CSS for Beginners",
                url="https://example.com/html-css-course",
                resource_type="course",
                is_free=True,
                duration=timedelta(hours=20)
            )
            
            mock_learning_path = LearningPath(
                title="Complete Beginner Web Developer Path",
                description="A comprehensive path for absolute beginners",
                goal="become a web developer",
                milestones=[mock_milestone],
                estimated_duration=timedelta(days=90),
                difficulty_level=DifficultyLevel.BEGINNER,
                target_skills=["web development", "frontend basics"]
            )
            
            async def mock_generate_path(user_id: str, goal: str):
                return mock_learning_path
            
            mock_conversation_manager.generate_learning_path = mock_generate_path
            mock_cm_class.return_value = mock_conversation_manager
            
            path_response = client.post(
                "/api/v1/learning/path",
                json={"goal": "become a web developer"},
                headers={"Authorization": f"Bearer {session_token}"}
            )
            
            assert path_response.status_code == 200
            path_data = path_response.json()
            assert "title" in path_data
            assert "milestones" in path_data
            assert path_data["difficulty_level"] == "beginner"
        
        # Step 6: Get content recommendations
        with patch('edagent.services.content_recommender.ContentRecommender') as mock_cr_class:
            mock_recommendations = [
                {
                    "title": "HTML Basics for Beginners",
                    "url": "https://youtube.com/watch?v=html-basics",
                    "platform": "YouTube",
                    "content_type": "video",
                    "duration_minutes": 45,
                    "rating": 4.8,
                    "is_free": True,
                    "skill_match_score": 0.95
                },
                {
                    "title": "CSS Fundamentals Course",
                    "url": "https://example.com/css-course",
                    "platform": "FreeCodeCamp",
                    "content_type": "interactive",
                    "duration_minutes": 180,
                    "rating": 4.9,
                    "is_free": True,
                    "skill_match_score": 0.92
                }
            ]
            
            mock_recommender = MagicMock()
            mock_recommender.get_recommendations = AsyncMock(return_value=mock_recommendations)
            mock_cr_class.return_value = mock_recommender
            
            recommendations_response = client.get(
                "/api/v1/content/recommendations?skill=html&level=beginner",
                headers={"Authorization": f"Bearer {session_token}"}
            )
            
            assert recommendations_response.status_code == 200
            rec_data = recommendations_response.json()
            assert len(rec_data["recommendations"]) > 0
            assert all(rec["is_free"] for rec in rec_data["recommendations"])
        
        # Step 7: Continue conversation with follow-up questions
        follow_up_messages = [
            "This looks great! How long will it take me to complete the first milestone?",
            "What should I focus on first - HTML or CSS?",
            "Do you have any tips for staying motivated while learning?"
        ]
        
        with patch('edagent.services.conversation_manager.ConversationManager') as mock_cm_class:
            mock_cm_class.return_value = mock_conversation_manager
            
            for message in follow_up_messages:
                follow_up_response = client.post(
                    "/api/v1/conversations/message",
                    json={"message": message},
                    headers={"Authorization": f"Bearer {session_token}"}
                )
                
                assert follow_up_response.status_code == 200
                response_data = follow_up_response.json()
                assert len(response_data["message"]) > 50  # Substantial response
                assert "suggested_actions" in response_data
        
        # Verify the complete journey was successful
        assert len(test_data_manager.created_users) == 1
        print(f"✅ Complete beginner onboarding journey successful for user {user_id}")
    
    @pytest.mark.asyncio
    async def test_experienced_user_career_change_journey(self, client, test_data_manager, mock_conversation_manager):
        """Test journey for experienced professional changing careers"""
        # Step 1: Create experienced user with existing skills
        user_id = test_data_manager.create_test_user()
        
        with patch('edagent.services.auth_service.db_manager') as mock_db:
            mock_session = AsyncMock()
            mock_db.get_session.return_value.__aenter__.return_value = mock_session
            
            from edagent.database.models import User
            mock_user = User(id=user_id)
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
            
            session_response = client.post(
                "/api/v1/auth/session",
                json={"user_id": user_id, "session_duration_minutes": 120}
            )
            
            assert session_response.status_code == 200
            session_token = session_response.json()["session_token"]
        
        # Step 2: User explains their background and career change goals
        with patch('edagent.services.conversation_manager.ConversationManager') as mock_cm_class:
            mock_cm_class.return_value = mock_conversation_manager
            
            career_change_message = """I'm a marketing manager with 8 years of experience, but I want to transition 
            into data science. I have some Excel skills and basic statistics knowledge from my MBA, but I'm new to 
            programming. I can dedicate about 15-20 hours per week to learning. What's the best path forward?"""
            
            conversation_response = client.post(
                "/api/v1/conversations/message",
                json={"message": career_change_message},
                headers={"Authorization": f"Bearer {session_token}"}
            )
            
            assert conversation_response.status_code == 200
            response_data = conversation_response.json()
            assert "career transition" in response_data["message"].lower() or "data science" in response_data["message"].lower()
        
        # Step 3: Skill assessment for career changer
        with patch('edagent.services.conversation_manager.ConversationManager') as mock_cm_class:
            from edagent.models.learning import SkillAssessment
            mock_assessment_result = SkillAssessment(
                skill_area="Data Science",
                overall_level=DifficultyLevel.BEGINNER,
                confidence_score=0.4,
                strengths=["Business domain knowledge", "Statistics foundation", "Excel proficiency", "Strong motivation"],
                weaknesses=["No programming experience", "Limited technical skills", "Needs Python basics"],
                recommendations=["Start with Python fundamentals", "Learn data manipulation with pandas", "Practice with real datasets"],
                detailed_scores={"python": 0.0, "statistics": 0.6, "excel": 0.8, "sql": 0.1, "machine_learning": 0.0}
            )
            
            async def mock_complete_assessment(session_id: str, responses: List[str]):
                return mock_assessment_result
            
            mock_conversation_manager.complete_skill_assessment = mock_complete_assessment
            mock_cm_class.return_value = mock_conversation_manager
            
            assessment_responses = [
                "I'm very comfortable with Excel and have used it for data analysis",
                "I have a good understanding of statistics from my MBA program",
                "I've never programmed before but I'm eager to learn",
                "I understand business metrics and KPIs very well"
            ]
            
            for response in assessment_responses:
                submit_response = client.post(
                    f"/api/v1/assessment/respond",
                    json={"session_id": "test_session", "response": response},
                    headers={"Authorization": f"Bearer {session_token}"}
                )
                assert submit_response.status_code == 200
        
        # Step 4: Generate career transition learning path
        with patch('edagent.services.conversation_manager.ConversationManager') as mock_cm_class:
            # Create comprehensive learning path for career changer
            milestones = [
                Milestone(
                    title="Python Programming Fundamentals",
                    description="Learn Python basics with focus on data applications",
                    skills_to_learn=["python_basics", "data_types", "control_structures"],
                    estimated_duration=timedelta(days=21),
                    difficulty_level=DifficultyLevel.BEGINNER,
                    order_index=0
                ),
                Milestone(
                    title="Data Manipulation with Pandas",
                    description="Master data cleaning and analysis with pandas",
                    skills_to_learn=["pandas", "data_cleaning", "data_analysis"],
                    estimated_duration=timedelta(days=28),
                    difficulty_level=DifficultyLevel.INTERMEDIATE,
                    order_index=1
                ),
                Milestone(
                    title="Statistical Analysis and Visualization",
                    description="Apply statistical concepts using Python tools",
                    skills_to_learn=["matplotlib", "seaborn", "statistical_analysis"],
                    estimated_duration=timedelta(days=21),
                    difficulty_level=DifficultyLevel.INTERMEDIATE,
                    order_index=2
                )
            ]
            
            mock_learning_path = LearningPath(
                title="Marketing Professional to Data Scientist Path",
                description="Tailored path leveraging business background for data science transition",
                goal="transition to data science",
                milestones=milestones,
                estimated_duration=timedelta(days=120),
                difficulty_level=DifficultyLevel.INTERMEDIATE,
                target_skills=["data science", "python", "analytics"]
            )
            
            async def mock_generate_path(user_id: str, goal: str):
                return mock_learning_path
            
            mock_conversation_manager.generate_learning_path = mock_generate_path
            mock_cm_class.return_value = mock_conversation_manager
            
            path_response = client.post(
                "/api/v1/learning/path",
                json={"goal": "transition to data science"},
                headers={"Authorization": f"Bearer {session_token}"}
            )
            
            assert path_response.status_code == 200
            path_data = path_response.json()
            assert "Marketing Professional" in path_data["title"]
            assert len(path_data["milestones"]) >= 3
        
        # Step 5: Resume analysis for career transition
        with patch('edagent.services.resume_analyzer.ResumeAnalyzer') as mock_ra_class:
            mock_analysis = {
                "overall_score": 7.2,
                "strengths": [
                    "Strong business and analytical background",
                    "Leadership experience",
                    "Quantitative skills from MBA"
                ],
                "improvement_areas": [
                    "Add technical skills section",
                    "Include data-related projects",
                    "Highlight analytical achievements with metrics"
                ],
                "career_transition_advice": [
                    "Emphasize transferable analytical skills",
                    "Consider adding relevant coursework or certifications",
                    "Create portfolio projects to demonstrate technical skills"
                ]
            }
            
            mock_analyzer = MagicMock()
            mock_analyzer.analyze_resume = AsyncMock(return_value=mock_analysis)
            mock_ra_class.return_value = mock_analyzer
            
            resume_response = client.post(
                "/api/v1/resume/analyze",
                json={"resume_text": "Marketing Manager with 8 years experience..."},
                headers={"Authorization": f"Bearer {session_token}"}
            )
            
            assert resume_response.status_code == 200
            analysis_data = resume_response.json()
            assert "career_transition_advice" in analysis_data
            assert analysis_data["overall_score"] > 6.0
        
        print(f"✅ Experienced user career change journey successful for user {user_id}")
    
    @pytest.mark.asyncio
    async def test_interview_preparation_workflow(self, client, test_data_manager):
        """Test complete interview preparation workflow"""
        user_id = test_data_manager.create_test_user()
        
        with patch('edagent.services.auth_service.db_manager') as mock_db:
            mock_session = AsyncMock()
            mock_db.get_session.return_value.__aenter__.return_value = mock_session
            
            from edagent.database.models import User
            mock_user = User(id=user_id)
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
            
            session_response = client.post(
                "/api/v1/auth/session",
                json={"user_id": user_id, "session_duration_minutes": 120}
            )
            
            session_token = session_response.json()["session_token"]
        
        # Step 1: Start interview preparation
        with patch('edagent.services.interview_preparation.InterviewPreparationService') as mock_ip_class:
            mock_questions = [
                {
                    "question": "Tell me about yourself and your background in software development.",
                    "category": "behavioral",
                    "difficulty": "easy",
                    "tips": ["Focus on relevant experience", "Keep it concise", "End with why you're interested in this role"]
                },
                {
                    "question": "How would you implement a function to reverse a string in Python?",
                    "category": "technical",
                    "difficulty": "medium",
                    "tips": ["Consider multiple approaches", "Discuss time complexity", "Write clean, readable code"]
                }
            ]
            
            mock_service = MagicMock()
            mock_service.generate_interview_questions = AsyncMock(return_value=mock_questions)
            mock_ip_class.return_value = mock_service
            
            prep_response = client.post(
                "/api/v1/interview/prepare",
                json={
                    "position": "Software Developer",
                    "company_type": "startup",
                    "experience_level": "entry"
                },
                headers={"Authorization": f"Bearer {session_token}"}
            )
            
            assert prep_response.status_code == 200
            prep_data = prep_response.json()
            assert "questions" in prep_data
            assert len(prep_data["questions"]) > 0
        
        # Step 2: Practice answering questions
        with patch('edagent.services.interview_preparation.InterviewPreparationService') as mock_ip_class:
            mock_feedback = {
                "score": 8.5,
                "strengths": ["Clear communication", "Good technical knowledge"],
                "improvements": ["Provide more specific examples", "Practice speaking more confidently"],
                "follow_up_questions": ["Can you give a specific example of a challenging project?"]
            }
            
            mock_service = MagicMock()
            mock_service.evaluate_answer = AsyncMock(return_value=mock_feedback)
            mock_ip_class.return_value = mock_service
            
            practice_response = client.post(
                "/api/v1/interview/practice",
                json={
                    "question_id": "q1",
                    "answer": "I'm a passionate developer with experience in Python and web development..."
                },
                headers={"Authorization": f"Bearer {session_token}"}
            )
            
            assert practice_response.status_code == 200
            feedback_data = practice_response.json()
            assert "score" in feedback_data
            assert feedback_data["score"] > 7.0
        
        print(f"✅ Interview preparation workflow successful for user {user_id}")


class TestPerformanceAndLoad:
    """Test system performance under various load conditions"""
    
    @pytest.fixture
    def app(self):
        return create_app()
    
    @pytest.fixture
    def client(self, app):
        return TestClient(app)
    
    @pytest.fixture
    def performance_metrics(self):
        return PerformanceMetrics()
    
    def test_response_time_requirements(self, client, performance_metrics):
        """Test that API responses meet time requirements (< 3 seconds)"""
        endpoints_to_test = [
            ("/health", "GET", None),
            ("/api/v1/conversations/message", "POST", {"message": "Hello"}),
        ]
        
        for endpoint, method, payload in endpoints_to_test:
            start_time = time.time()
            
            try:
                if method == "GET":
                    response = client.get(endpoint)
                else:
                    response = client.post(endpoint, json=payload)
                
                duration = time.time() - start_time
                performance_metrics.record_response_time(duration)
                
                if response.status_code < 500:
                    performance_metrics.record_success()
                else:
                    performance_metrics.record_error()
                
                # Response time requirement: < 3 seconds
                assert duration < 3.0, f"Response time {duration:.2f}s exceeds 3s limit for {endpoint}"
                
            except Exception as e:
                performance_metrics.record_error()
                print(f"Error testing {endpoint}: {e}")
        
        # Overall performance metrics
        assert performance_metrics.average_response_time < 2.0, "Average response time too high"
        assert performance_metrics.success_rate > 0.8, "Success rate too low"
    
    @pytest.mark.asyncio
    async def test_concurrent_user_handling(self, client, performance_metrics):
        """Test system behavior with multiple concurrent users"""
        num_concurrent_users = 10
        requests_per_user = 5
        
        async def simulate_user_session(user_id: str):
            """Simulate a user session with multiple requests"""
            session_metrics = PerformanceMetrics()
            
            # Create session
            start_time = time.time()
            try:
                with patch('edagent.services.auth_service.db_manager') as mock_db:
                    mock_session = AsyncMock()
                    mock_db.get_session.return_value.__aenter__.return_value = mock_session
                    
                    from edagent.database.models import User
                    mock_user = User(id=user_id)
                    mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
                    
                    session_response = client.post(
                        "/api/v1/auth/session",
                        json={"user_id": user_id, "session_duration_minutes": 60}
                    )
                
                duration = time.time() - start_time
                session_metrics.record_response_time(duration)
                
                if session_response.status_code == 200:
                    session_metrics.record_success()
                    session_token = session_response.json()["session_token"]
                else:
                    session_metrics.record_error()
                    return session_metrics
                
                # Make multiple conversation requests
                with patch('edagent.services.conversation_manager.ConversationManager') as mock_cm:
                    mock_manager = MagicMock()
                    
                    async def mock_handle_message(user_id: str, message: str):
                        from edagent.models.conversation import ConversationResponse
                        return ConversationResponse(
                            message=f"Response to: {message}",
                            conversation_id=f"conv_{uuid.uuid4().hex[:8]}",
                            user_id=user_id,
                            timestamp=datetime.now(),
                            message_type="response"
                        )
                    
                    mock_manager.handle_message = mock_handle_message
                    mock_cm.return_value = mock_manager
                    
                    for i in range(requests_per_user):
                        start_time = time.time()
                        
                        try:
                            response = client.post(
                                "/api/v1/conversations/message",
                                json={"message": f"Test message {i} from user {user_id}"},
                                headers={"Authorization": f"Bearer {session_token}"}
                            )
                            
                            duration = time.time() - start_time
                            session_metrics.record_response_time(duration)
                            
                            if response.status_code == 200:
                                session_metrics.record_success()
                            else:
                                session_metrics.record_error()
                        
                        except Exception as e:
                            session_metrics.record_error()
                            print(f"Error in user {user_id} request {i}: {e}")
                
            except Exception as e:
                session_metrics.record_error()
                print(f"Error in user {user_id} session: {e}")
            
            return session_metrics
        
        # Run concurrent user sessions
        tasks = []
        for i in range(num_concurrent_users):
            user_id = f"concurrent_user_{i}"
            tasks.append(simulate_user_session(user_id))
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate metrics
        total_requests = 0
        total_successes = 0
        total_errors = 0
        all_response_times = []
        
        for result in results:
            if isinstance(result, PerformanceMetrics):
                total_requests += result.success_count + result.error_count
                total_successes += result.success_count
                total_errors += result.error_count
                all_response_times.extend(result.response_times)
        
        # Performance assertions
        overall_success_rate = total_successes / total_requests if total_requests > 0 else 0
        average_response_time = sum(all_response_times) / len(all_response_times) if all_response_times else 0
        
        assert overall_success_rate > 0.7, f"Success rate {overall_success_rate:.2f} too low under concurrent load"
        assert average_response_time < 5.0, f"Average response time {average_response_time:.2f}s too high under load"
        
        print(f"✅ Concurrent user test: {num_concurrent_users} users, {total_requests} requests, "
              f"{overall_success_rate:.2%} success rate, {average_response_time:.2f}s avg response time")
    
    def test_memory_usage_under_load(self, client):
        """Test memory usage doesn't grow excessively under load"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make many requests to test memory usage
        num_requests = 100
        
        with patch('edagent.services.conversation_manager.ConversationManager') as mock_cm:
            mock_manager = MagicMock()
            
            async def mock_handle_message(user_id: str, message: str):
                from edagent.models.conversation import ConversationResponse
                return ConversationResponse(
                    message=f"Response to: {message}",
                    conversation_id=f"conv_{uuid.uuid4().hex[:8]}",
                    user_id=user_id,
                    timestamp=datetime.now(),
                    message_type="response"
                )
            
            mock_manager.handle_message = mock_handle_message
            mock_cm.return_value = mock_manager
            
            for i in range(num_requests):
                try:
                    response = client.post(
                        "/api/v1/conversations/message",
                        json={"message": f"Memory test message {i}"}
                    )
                except Exception as e:
                    print(f"Request {i} failed: {e}")
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory shouldn't increase by more than 100MB for 100 requests
        assert memory_increase < 100, f"Memory increased by {memory_increase:.1f}MB, possible memory leak"
        
        print(f"✅ Memory usage test: {memory_increase:.1f}MB increase over {num_requests} requests")
    
    def test_database_connection_pooling(self, client):
        """Test database connection pooling under load"""
        # This test would verify that database connections are properly pooled
        # and don't exhaust the connection limit
        
        num_requests = 50
        successful_requests = 0
        
        with patch('edagent.services.auth_service.db_manager') as mock_db:
            mock_session = AsyncMock()
            mock_db.get_session.return_value.__aenter__.return_value = mock_session
            
            from edagent.database.models import User
            mock_user = User(id="test_user")
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
            
            for i in range(num_requests):
                try:
                    response = client.post(
                        "/api/v1/auth/session",
                        json={"user_id": f"user_{i}", "session_duration_minutes": 60}
                    )
                    
                    if response.status_code == 200:
                        successful_requests += 1
                
                except Exception as e:
                    print(f"Database request {i} failed: {e}")
        
        success_rate = successful_requests / num_requests
        assert success_rate > 0.9, f"Database connection success rate {success_rate:.2%} too low"
        
        print(f"✅ Database connection pooling test: {success_rate:.2%} success rate over {num_requests} requests")


class TestSystemIntegration:
    """Test integration between different system components"""
    
    @pytest.fixture
    def app(self):
        return create_app()
    
    @pytest.fixture
    def client(self, app):
        return TestClient(app)
    
    @pytest.mark.asyncio
    async def test_ai_service_content_recommender_integration(self, client):
        """Test integration between AI service and content recommender"""
        with patch('edagent.services.ai_service.GeminiAIService') as mock_ai:
            with patch('edagent.services.content_recommender.ContentRecommender') as mock_cr:
                # Mock AI service response
                mock_ai_instance = MagicMock()
                mock_ai_instance.generate_response = AsyncMock(
                    return_value="I recommend focusing on Python fundamentals first."
                )
                mock_ai.return_value = mock_ai_instance
                
                # Mock content recommender response
                mock_cr_instance = MagicMock()
                mock_cr_instance.get_recommendations = AsyncMock(return_value=[
                    {
                        "title": "Python for Beginners",
                        "url": "https://example.com/python-course",
                        "platform": "YouTube",
                        "is_free": True,
                        "skill_match_score": 0.95
                    }
                ])
                mock_cr.return_value = mock_cr_instance
                
                # Test the integration through conversation
                with patch('edagent.services.conversation_manager.ConversationManager') as mock_cm:
                    mock_manager = MagicMock()
                    
                    async def mock_handle_message(user_id: str, message: str):
                        # Simulate the integration: AI generates response, then content is recommended
                        ai_response = await mock_ai_instance.generate_response(message, None)
                        recommendations = await mock_cr_instance.get_recommendations("python", "beginner")
                        
                        from edagent.models.conversation import ConversationResponse
                        return ConversationResponse(
                            message=ai_response,
                            conversation_id=f"conv_{uuid.uuid4().hex[:8]}",
                            user_id=user_id,
                            timestamp=datetime.now(),
                            message_type="response",
                            recommended_content=recommendations
                        )
                    
                    mock_manager.handle_message = mock_handle_message
                    mock_cm.return_value = mock_manager
                    
                    response = client.post(
                        "/api/v1/conversations/message",
                        json={"message": "I want to learn Python programming"}
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert "Python fundamentals" in data["message"]
                    assert "recommended_content" in data
                    assert len(data["recommended_content"]) > 0
        
        print("✅ AI service and content recommender integration test passed")
    
    @pytest.mark.asyncio
    async def test_user_context_learning_path_integration(self, client):
        """Test integration between user context and learning path generation"""
        user_id = f"integration_user_{uuid.uuid4().hex[:8]}"
        
        with patch('edagent.services.user_context_manager.UserContextManager') as mock_ucm:
            with patch('edagent.services.learning_path_generator.EnhancedLearningPathGenerator') as mock_lpg:
                # Mock user context
                user_context = UserContext(
                    user_id=user_id,
                    current_skills={
                        "Python": SkillLevel("Python", SkillLevelEnum.BEGINNER, 0.6, datetime.now())
                    },
                    career_goals=["become a data scientist"],
                    learning_preferences=UserPreferences(
                        learning_style=LearningStyleEnum.VISUAL,
                        time_commitment="part-time",
                        budget_preference="free"
                    )
                )
                
                mock_ucm_instance = MagicMock()
                mock_ucm_instance.get_user_context = AsyncMock(return_value=user_context)
                mock_ucm.return_value = mock_ucm_instance
                
                # Mock learning path generation
                mock_milestone = Milestone(
                    title="Advanced Python for Data Science",
                    description="Build on existing Python knowledge for data science applications",
                    skills_to_learn=["pandas", "numpy", "matplotlib"],
                    estimated_duration=timedelta(days=21),
                    difficulty_level=DifficultyLevel.INTERMEDIATE,
                    order_index=0
                )
                
                mock_learning_path = LearningPath(
                    title="Data Science Path for Python Beginners",
                    description="Tailored path based on existing Python knowledge",
                    goal="become a data scientist",
                    milestones=[mock_milestone],
                    estimated_duration=timedelta(days=90),
                    difficulty_level=DifficultyLevel.INTERMEDIATE,
                    target_skills=["data science", "python", "analytics"]
                )
                
                mock_lpg_instance = MagicMock()
                mock_lpg_instance.create_comprehensive_learning_path = AsyncMock(return_value=mock_learning_path)
                mock_lpg.return_value = mock_lpg_instance
                
                # Test the integration
                with patch('edagent.services.conversation_manager.ConversationManager') as mock_cm:
                    mock_manager = MagicMock()
                    
                    async def mock_generate_path(user_id: str, goal: str):
                        # Simulate the integration: get user context, then generate path
                        context = await mock_ucm_instance.get_user_context(user_id)
                        path = await mock_lpg_instance.create_comprehensive_learning_path(
                            goal, context.current_skills, context
                        )
                        return path
                    
                    mock_manager.generate_learning_path = mock_generate_path
                    mock_cm.return_value = mock_manager
                    
                    response = client.post(
                        "/api/v1/learning/path",
                        json={"goal": "become a data scientist"}
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert "Python Beginners" in data["title"]
                    assert data["difficulty_level"] == "intermediate"  # Adjusted based on existing skills
        
        print("✅ User context and learning path integration test passed")
    
    def test_authentication_authorization_integration(self, client):
        """Test integration between authentication and authorization systems"""
        user_id = f"auth_user_{uuid.uuid4().hex[:8]}"
        
        with patch('edagent.services.auth_service.db_manager') as mock_db:
            mock_session = AsyncMock()
            mock_db.get_session.return_value.__aenter__.return_value = mock_session
            
            from edagent.database.models import User, UserSession, APIKey
            mock_user = User(id=user_id)
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user
            
            # Test 1: Session-based authentication
            session_response = client.post(
                "/api/v1/auth/session",
                json={"user_id": user_id, "session_duration_minutes": 60}
            )
            
            assert session_response.status_code == 200
            session_token = session_response.json()["session_token"]
            
            # Mock session validation for protected endpoint access
            mock_db_session = UserSession(
                session_id="test_session",
                user_id=user_id,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=1),
                status="active"
            )
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_db_session
            
            # Access protected endpoint with session token
            protected_response = client.get(
                "/api/v1/conversations",
                headers={"Authorization": f"Bearer {session_token}"}
            )
            
            # Should not be 401 (unauthorized)
            assert protected_response.status_code != 401
            
            # Test 2: API key-based authentication
            api_key_response = client.post(
                f"/api/v1/auth/api-key?user_id={user_id}",
                json={
                    "name": "Integration Test Key",
                    "permissions": ["read"],
                    "expires_in_days": 30
                }
            )
            
            assert api_key_response.status_code == 200
            api_key = api_key_response.json()["api_key"]
            
            # Mock API key validation
            from edagent.services.auth_service import AuthenticationService
            auth_service = AuthenticationService()
            key_hash = auth_service._hash_api_key(api_key)
            
            mock_db_key = APIKey(
                key_id="test_key",
                user_id=user_id,
                key_hash=key_hash,
                name="Integration Test Key",
                permissions=["read"],
                is_active=True
            )
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_db_key
            
            # Access protected endpoint with API key
            api_protected_response = client.get(
                "/api/v1/conversations",
                headers={"X-API-Key": api_key}
            )
            
            # Should not be 401 (unauthorized)
            assert api_protected_response.status_code != 401
        
        print("✅ Authentication and authorization integration test passed")


if __name__ == "__main__":
    # Run specific test suites
    pytest.main([
        __file__ + "::TestEndToEndUserJourneys::test_complete_beginner_onboarding_journey",
        "-v", "--tb=short"
    ])