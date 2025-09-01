"""
Integration tests for interview preparation functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from edagent.services.conversation_manager import ConversationManager
from edagent.models.user_context import UserContext, SkillLevel, SkillLevelEnum
from edagent.models.interview import InterviewType, DifficultyLevel
from edagent.models.conversation import ConversationResponse


class TestInterviewConversationIntegration:
    """Test interview preparation integration with conversation manager"""
    
    @pytest.fixture
    def conversation_manager(self):
        """Create conversation manager with mocked dependencies"""
        manager = ConversationManager()
        
        # Mock the AI service
        manager.ai_service.generate_response = AsyncMock()
        manager.ai_service._make_api_call = AsyncMock()
        manager.ai_service._get_model = Mock()
        manager.ai_service._get_generation_config = Mock()
        
        # Mock user context manager
        manager.user_context_manager.get_user_context = AsyncMock()
        manager.user_context_manager.create_user_context = AsyncMock()
        manager.user_context_manager.add_conversation = AsyncMock()
        
        return manager
    
    @pytest.fixture
    def sample_user_context(self):
        """Create sample user context"""
        return UserContext(
            user_id="test-user-123",
            current_skills={
                "python": SkillLevel("python", SkillLevelEnum.INTERMEDIATE, 0.7),
                "communication": SkillLevel("communication", SkillLevelEnum.BEGINNER, 0.5)
            },
            career_goals=["become a software engineer", "work at a tech company"]
        )
    
    @pytest.mark.asyncio
    async def test_interview_intent_detection(self, conversation_manager):
        """Test that interview-related messages are properly detected"""
        test_cases = [
            ("I need help with interview preparation", "interview_preparation"),
            ("Can we practice interview questions?", "interview_preparation"),
            ("I have a job interview next week", "interview_preparation"),
            ("Help me prepare for interviews", "interview_preparation"),
            ("Interview tips please", "interview_preparation"),
            ("Mock interview practice", "interview_preparation"),
            ("What should I expect in a tech interview?", "interview_preparation"),
            ("I'm nervous about my upcoming interview", "interview_preparation"),
            ("Tell me about yourself", "general"),  # Should not trigger interview intent
            ("I want to learn Python", "general")   # Should not trigger interview intent
        ]
        
        for message, expected_intent in test_cases:
            detected_intent = conversation_manager._detect_intent(message)
            assert detected_intent == expected_intent, f"Message '{message}' should detect '{expected_intent}' but got '{detected_intent}'"
    
    @pytest.mark.asyncio
    async def test_general_interview_advice_request(self, conversation_manager, sample_user_context):
        """Test handling general interview advice requests"""
        # Setup mocks
        conversation_manager.user_context_manager.get_user_context.return_value = sample_user_context
        conversation_manager.ai_service.generate_response.return_value = """
        Here are some key interview tips:
        
        1. Research the company thoroughly
        2. Prepare specific examples using the STAR method
        3. Practice common behavioral questions
        4. Prepare thoughtful questions to ask the interviewer
        
        Would you like to practice some questions together?
        """
        
        # Test general interview advice
        response = await conversation_manager.handle_message(
            user_id="test-user-123",
            message="Can you give me some interview tips?"
        )
        
        assert isinstance(response, ConversationResponse)
        assert response.response_type == "career_coaching"
        assert "interview tips" in response.message.lower() or "research" in response.message.lower()
        assert len(response.suggested_actions) > 0
        assert any("practice" in action.lower() for action in response.suggested_actions)
    
    @pytest.mark.asyncio
    async def test_interview_practice_session_initiation(self, conversation_manager, sample_user_context):
        """Test initiating an interview practice session"""
        # Setup mocks
        conversation_manager.user_context_manager.get_user_context.return_value = sample_user_context
        
        # Mock AI service for question generation
        conversation_manager.ai_service._make_api_call.return_value = '''
        {
            "questions": [
                {
                    "question": "Tell me about yourself and your background in software development",
                    "key_points": ["Technical background", "Experience", "Career goals"],
                    "sample_answer": "I'm a software developer with experience in...",
                    "follow_up_questions": ["What programming languages do you prefer?"],
                    "tags": ["introduction", "technical"]
                },
                {
                    "question": "Describe a challenging technical problem you solved",
                    "key_points": ["Problem description", "Solution approach", "Results"],
                    "sample_answer": "I encountered a performance issue where...",
                    "follow_up_questions": ["How did you measure the improvement?"],
                    "tags": ["problem-solving", "technical"]
                }
            ]
        }
        '''
        
        # Test practice session initiation
        response = await conversation_manager.handle_message(
            user_id="test-user-123",
            message="I want to practice interview questions for a software engineer position"
        )
        
        assert isinstance(response, ConversationResponse)
        assert response.response_type == "career_coaching"
        assert "question 1 of" in response.message.lower()
        assert "tell me about yourself" in response.message.lower()
        assert response.metadata["intent"] == "interview_practice"
        assert "session_id" in response.metadata
        assert response.metadata["current_question"] == 0
        assert response.metadata["total_questions"] > 0
    
    @pytest.mark.asyncio
    async def test_industry_specific_guidance_request(self, conversation_manager, sample_user_context):
        """Test requesting industry-specific interview guidance"""
        # Setup mocks
        conversation_manager.user_context_manager.get_user_context.return_value = sample_user_context
        
        # Mock AI service for industry guidance
        conversation_manager.ai_service._make_api_call.return_value = '''
        {
            "common_questions": [
                "Describe your technical background",
                "How do you approach debugging complex issues?",
                "Tell me about a time you had to learn a new technology quickly"
            ],
            "key_skills": ["Programming", "Problem-solving", "Communication", "Teamwork"],
            "interview_format": "Phone screening, technical assessment, system design, behavioral interview",
            "preparation_tips": [
                "Practice coding problems on platforms like LeetCode",
                "Review system design fundamentals",
                "Prepare behavioral examples using STAR method"
            ],
            "red_flags": ["Lack of technical depth", "Poor communication skills"],
            "success_factors": ["Strong technical foundation", "Clear communication", "Cultural fit"]
        }
        '''
        
        # Test industry guidance request
        response = await conversation_manager.handle_message(
            user_id="test-user-123",
            message="What should I expect in a tech company interview?"
        )
        
        assert isinstance(response, ConversationResponse)
        assert response.response_type == "career_coaching"
        assert "technology" in response.message.lower() or "tech" in response.message.lower()
        assert "common questions" in response.message.lower()
        assert "key skills" in response.message.lower()
        assert response.metadata["intent"] == "industry_guidance"
        assert response.metadata["industry"] in ["Technology", "Tech"]
    
    @pytest.mark.asyncio
    async def test_interview_nervousness_handling(self, conversation_manager, sample_user_context):
        """Test handling interview anxiety and nervousness"""
        # Setup mocks
        conversation_manager.user_context_manager.get_user_context.return_value = sample_user_context
        conversation_manager.ai_service.generate_response.return_value = """
        I understand that interview nerves are completely normal! Here are some strategies to help:
        
        **Managing Interview Anxiety:**
        • Preparation is your best friend - the more prepared you are, the more confident you'll feel
        • Practice deep breathing exercises before and during the interview
        • Arrive early to give yourself time to settle in
        • Remember that the interviewer wants you to succeed
        • Practice your answers out loud beforehand
        
        Would you like to do some practice questions to build your confidence?
        """
        
        # Test nervousness handling
        response = await conversation_manager.handle_message(
            user_id="test-user-123",
            message="I'm really nervous about my upcoming interview. Any tips?"
        )
        
        assert isinstance(response, ConversationResponse)
        assert response.response_type == "career_coaching"
        assert any(word in response.message.lower() for word in ["nervous", "anxiety", "confidence", "preparation"])
        assert "practice" in response.message.lower()
    
    @pytest.mark.asyncio
    async def test_role_extraction_from_message(self, conversation_manager):
        """Test extracting target role from user messages"""
        test_cases = [
            ("I'm preparing for a software developer interview", "Software Developer"),
            ("Help me with data scientist interview prep", "Data Scientist"),
            ("I have a product manager interview next week", "Product Manager"),
            ("Preparing for a marketing manager position", "Marketing Manager"),
            ("I'm interviewing for a sales rep role", "Sales Representative"),
            ("Generic interview preparation", "Software Developer"),  # Default
        ]
        
        sample_context = UserContext(user_id="test")
        
        for message, expected_role in test_cases:
            extracted_role = conversation_manager._extract_target_role(message, sample_context)
            assert extracted_role == expected_role, f"Message '{message}' should extract '{expected_role}' but got '{extracted_role}'"
    
    @pytest.mark.asyncio
    async def test_industry_extraction_from_message(self, conversation_manager):
        """Test extracting target industry from user messages"""
        test_cases = [
            ("I'm preparing for a tech company interview", "Technology"),
            ("Help with healthcare interview preparation", "Healthcare"),
            ("I have a finance interview coming up", "Finance"),
            ("Preparing for an education sector interview", "Education"),
            ("Marketing industry interview tips", "Marketing"),
            ("Generic interview help", None),  # Should return None for generic
        ]
        
        for message, expected_industry in test_cases:
            extracted_industry = conversation_manager._extract_industry_from_message(message)
            assert extracted_industry == expected_industry, f"Message '{message}' should extract '{expected_industry}' but got '{extracted_industry}'"
    
    @pytest.mark.asyncio
    async def test_interview_question_categorization(self, conversation_manager):
        """Test categorizing different types of interview questions"""
        # Test behavioral question detection
        assert conversation_manager._is_general_interview_question("What are some good interview tips?")
        assert conversation_manager._is_general_interview_question("How should I prepare for interviews?")
        
        # Test practice session detection
        assert conversation_manager._wants_practice_session("Can we do a mock interview?")
        assert conversation_manager._wants_practice_session("I want to practice interview questions")
        
        # Test industry guidance detection
        assert conversation_manager._wants_industry_guidance("What should I expect in a tech interview?")
        assert conversation_manager._wants_industry_guidance("Tell me about finance industry interviews")
    
    @pytest.mark.asyncio
    async def test_interview_preparation_guidance_formatting(self, conversation_manager):
        """Test formatting of interview preparation guidance"""
        sample_context = UserContext(user_id="test")
        
        guidance = conversation_manager._create_interview_preparation_guidance(sample_context)
        
        assert "Interview Preparation Options" in guidance
        assert "Practice Interview Session" in guidance
        assert "General Interview Tips" in guidance
        assert "Industry-Specific Guidance" in guidance
        assert "Question Practice" in guidance
        assert "Start a practice session" in guidance
        assert "Interview tips" in guidance
    
    @pytest.mark.asyncio
    async def test_structured_interview_advice(self, conversation_manager):
        """Test structured interview advice for different categories"""
        # Test nervousness advice
        nervousness_advice = conversation_manager._get_structured_interview_advice("I'm nervous about interviews")
        assert "Managing Interview Nerves" in nervousness_advice
        assert "preparation" in nervousness_advice.lower()
        assert "breathing" in nervousness_advice.lower()
        
        # Test questions to ask advice
        questions_advice = conversation_manager._get_structured_interview_advice("What questions should I ask the interviewer?")
        assert "Questions to Ask Interviewers" in questions_advice
        assert "typical day" in questions_advice.lower()
        assert "opportunities" in questions_advice.lower()
        
        # Test dress code advice
        dress_advice = conversation_manager._get_structured_interview_advice("What should I wear to the interview?")
        assert "Interview Attire Guidelines" in dress_advice
        assert "business" in dress_advice.lower()
        assert "professional" in dress_advice.lower()
        
        # Test general advice
        general_advice = conversation_manager._get_structured_interview_advice("General interview help")
        assert "Essential Interview Tips" in general_advice
        assert "research" in general_advice.lower()
        assert "STAR method" in general_advice
    
    @pytest.mark.asyncio
    async def test_interview_conversation_flow(self, conversation_manager, sample_user_context):
        """Test complete interview preparation conversation flow"""
        # Setup mocks
        conversation_manager.user_context_manager.get_user_context.return_value = sample_user_context
        conversation_manager.user_context_manager.create_user_context.return_value = sample_user_context
        
        # Mock AI responses
        conversation_manager.ai_service.generate_response.return_value = "Here are some helpful interview tips..."
        conversation_manager.ai_service._make_api_call.return_value = '''
        {
            "questions": [
                {
                    "question": "Why do you want to work here?",
                    "key_points": ["Company research", "Role alignment", "Career goals"],
                    "sample_answer": "I'm interested in this role because...",
                    "follow_up_questions": ["What do you know about our products?"],
                    "tags": ["motivation"]
                }
            ]
        }
        '''
        
        # 1. Initial interview preparation request
        response1 = await conversation_manager.handle_message(
            user_id="test-user-123",
            message="I need help preparing for interviews"
        )
        
        assert response1.response_type == "career_coaching"
        assert "interview" in response1.message.lower()
        
        # 2. Request for practice session
        response2 = await conversation_manager.handle_message(
            user_id="test-user-123",
            message="Let's start a practice interview session"
        )
        
        assert response2.response_type == "career_coaching"
        assert "question 1 of" in response2.message.lower()
        assert response2.metadata["intent"] == "interview_practice"
        
        # 3. Request for industry guidance
        response3 = await conversation_manager.handle_message(
            user_id="test-user-123",
            message="What should I expect in a technology company interview?"
        )
        
        assert response3.response_type == "career_coaching"
        assert response3.metadata["intent"] == "industry_guidance"
        
        # Verify all responses are properly formatted
        for response in [response1, response2, response3]:
            assert isinstance(response, ConversationResponse)
            assert response.message
            assert response.response_type == "career_coaching"


class TestInterviewPreparationEffectiveness:
    """Test the effectiveness of interview preparation features"""
    
    @pytest.mark.asyncio
    async def test_interview_question_quality(self):
        """Test that generated interview questions meet quality standards"""
        from edagent.services.interview_preparation import InterviewPreparationService
        
        # Mock AI service
        mock_ai_service = Mock()
        mock_ai_service._make_api_call = AsyncMock()
        mock_ai_service._get_model = Mock()
        mock_ai_service._get_generation_config = Mock()
        
        service = InterviewPreparationService(ai_service=mock_ai_service)
        
        # Mock high-quality question response
        mock_ai_service._make_api_call.return_value = '''
        {
            "questions": [
                {
                    "question": "Describe a time when you had to work with a difficult team member and how you handled the situation",
                    "key_points": [
                        "Specific situation description",
                        "Actions taken to address the difficulty",
                        "Communication strategies used",
                        "Outcome and lessons learned"
                    ],
                    "sample_answer": "In my previous role, I worked with a colleague who was resistant to feedback. I approached this by first trying to understand their perspective through one-on-one conversations, then finding common ground on project goals, and finally establishing clear communication protocols that worked for both of us. This resulted in improved collaboration and successful project completion.",
                    "follow_up_questions": [
                        "How do you typically handle conflict in the workplace?",
                        "What would you do if the situation hadn't improved?"
                    ],
                    "tags": ["behavioral", "teamwork", "conflict-resolution"]
                }
            ]
        }
        '''
        
        session = await service.create_interview_session(
            user_id="test-user",
            target_role="Project Manager",
            target_industry="Technology",
            num_questions=1
        )
        
        question = session.questions[0]
        
        # Verify question quality
        assert len(question.question) > 20  # Substantial question
        assert len(question.key_points) >= 3  # Multiple evaluation criteria
        assert len(question.sample_answer) > 50  # Detailed sample answer
        assert len(question.follow_up_questions) > 0  # Has follow-up questions
        assert len(question.tags) > 0  # Properly tagged
        
        # Verify question is behavioral and specific
        assert any(word in question.question.lower() for word in ["describe", "tell me about", "give me an example"])
        assert "time when" in question.question.lower() or "situation" in question.question.lower()
    
    @pytest.mark.asyncio
    async def test_feedback_quality_and_actionability(self):
        """Test that feedback is constructive and actionable"""
        from edagent.services.interview_preparation import InterviewPreparationService
        from edagent.models.interview import InterviewQuestion, InterviewType, DifficultyLevel
        
        # Mock AI service
        mock_ai_service = Mock()
        mock_ai_service._make_api_call = AsyncMock()
        mock_ai_service._get_model = Mock()
        mock_ai_service._get_generation_config = Mock()
        
        service = InterviewPreparationService(ai_service=mock_ai_service)
        
        # Mock detailed feedback response
        mock_ai_service._make_api_call.return_value = '''
        {
            "score": 7.5,
            "feedback_text": "Your response demonstrates good self-awareness and shows you can handle challenging situations. You provided a clear example and explained your thought process well. To strengthen your answer, consider adding more specific details about the outcome and quantifiable results.",
            "strengths": [
                "Clear example with specific context",
                "Demonstrated problem-solving approach",
                "Showed emotional intelligence and empathy",
                "Good structure following situation-action-result format"
            ],
            "improvements": [
                "Add more quantifiable results or metrics",
                "Elaborate on the specific communication techniques used",
                "Mention what you learned from the experience",
                "Could provide more detail about the timeline"
            ],
            "suggestions": [
                "Practice using the STAR method more explicitly (Situation, Task, Action, Result)",
                "Prepare 2-3 similar examples to show consistency",
                "Consider mentioning how this experience changed your approach to teamwork",
                "Practice delivering this answer in 2-3 minutes"
            ],
            "feedback_type": "improvement"
        }
        '''
        
        question = InterviewQuestion(
            question="Tell me about a time you had to work with a difficult team member",
            question_type=InterviewType.BEHAVIORAL,
            difficulty=DifficultyLevel.INTERMEDIATE
        )
        
        user_response = "I once worked with someone who was always negative and criticized everyone's ideas. I tried to stay positive and focus on the work, and eventually things got better."
        
        feedback = await service.provide_feedback(question, user_response)
        
        # Verify feedback quality
        assert 0 <= feedback.score <= 10
        assert len(feedback.feedback_text) > 50  # Substantial feedback
        assert len(feedback.strengths) >= 2  # Multiple strengths identified
        assert len(feedback.improvements) >= 2  # Multiple improvement areas
        assert len(feedback.suggestions) >= 2  # Multiple actionable suggestions
        
        # Verify feedback is constructive
        assert any(word in feedback.feedback_text.lower() for word in ["good", "demonstrates", "shows"])
        assert any(word in " ".join(feedback.improvements).lower() for word in ["add", "elaborate", "consider", "include"])
        assert any(word in " ".join(feedback.suggestions).lower() for word in ["practice", "prepare", "try", "consider"])
    
    @pytest.mark.asyncio
    async def test_industry_guidance_comprehensiveness(self):
        """Test that industry guidance is comprehensive and useful"""
        from edagent.services.interview_preparation import InterviewPreparationService
        
        # Mock AI service
        mock_ai_service = Mock()
        mock_ai_service._make_api_call = AsyncMock()
        mock_ai_service._get_model = Mock()
        mock_ai_service._get_generation_config = Mock()
        
        service = InterviewPreparationService(ai_service=mock_ai_service)
        
        # Mock comprehensive industry guidance
        mock_ai_service._make_api_call.return_value = '''
        {
            "common_questions": [
                "Describe your technical background and experience",
                "How do you approach debugging a complex technical issue?",
                "Tell me about a time you had to learn a new technology quickly",
                "How do you stay updated with the latest technology trends?",
                "Describe a challenging project you worked on and your role in it"
            ],
            "key_skills": [
                "Programming and technical proficiency",
                "Problem-solving and analytical thinking",
                "Communication and collaboration",
                "Continuous learning and adaptability",
                "Project management and organization",
                "Attention to detail and quality focus"
            ],
            "interview_format": "Technology interviews typically include: (1) Phone/video screening with HR or hiring manager, (2) Technical phone/video interview with coding questions, (3) On-site or virtual interviews including technical deep-dive, system design (for senior roles), behavioral questions, and team fit assessment, (4) Final interview with senior leadership or team leads",
            "preparation_tips": [
                "Practice coding problems on platforms like LeetCode, HackerRank, or CodeSignal",
                "Review fundamental computer science concepts (data structures, algorithms, complexity)",
                "Prepare to explain your past projects in detail, including technical decisions and trade-offs",
                "Study system design basics if applying for senior positions",
                "Research the company's technology stack and recent technical blog posts",
                "Prepare behavioral examples that demonstrate leadership, problem-solving, and collaboration"
            ],
            "red_flags": [
                "Inability to explain technical concepts clearly",
                "Lack of curiosity about the company's technical challenges",
                "Poor problem-solving approach or giving up too quickly on technical questions"
            ],
            "success_factors": [
                "Strong technical foundation with ability to explain concepts clearly",
                "Demonstrated passion for technology and continuous learning",
                "Good communication skills and ability to work in teams",
                "Problem-solving mindset with structured approach to challenges",
                "Cultural fit with company values and team dynamics"
            ]
        }
        '''
        
        guidance = await service.get_industry_guidance("Technology")
        
        # Verify comprehensiveness
        assert len(guidance.common_questions) >= 3
        assert len(guidance.key_skills) >= 4
        assert len(guidance.preparation_tips) >= 4
        assert len(guidance.red_flags) >= 2
        assert len(guidance.success_factors) >= 3
        
        # Verify content quality
        assert len(guidance.interview_format) > 100  # Detailed format description
        
        # Verify industry-specific content
        tech_keywords = ["technical", "coding", "programming", "technology", "system", "software"]
        guidance_text = (
            " ".join(guidance.common_questions) + " " +
            " ".join(guidance.key_skills) + " " +
            guidance.interview_format + " " +
            " ".join(guidance.preparation_tips)
        ).lower()
        
        assert any(keyword in guidance_text for keyword in tech_keywords)


if __name__ == "__main__":
    pytest.main([__file__])