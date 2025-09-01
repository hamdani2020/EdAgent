"""
Unit tests for the Gemini AI service
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from edagent.services.ai_service import (
    GeminiAIService, 
    GeminiAPIError, 
    RateLimitError, 
    QuotaExceededError
)
from edagent.models.user_context import UserContext, SkillLevel, SkillLevelEnum, UserPreferences, LearningStyleEnum
from edagent.models.learning import SkillAssessment, LearningPath, DifficultyLevel


class TestGeminiAIService:
    """Test cases for GeminiAIService"""
    
    @pytest.fixture
    def ai_service(self):
        """Create AI service instance for testing"""
        with patch('edagent.services.ai_service.genai.configure'):
            service = GeminiAIService()
            return service
    
    @pytest.fixture
    def sample_user_context(self):
        """Create sample user context for testing"""
        preferences = UserPreferences(
            learning_style=LearningStyleEnum.VISUAL,
            time_commitment="2-3 hours/week",
            budget_preference="free"
        )
        
        context = UserContext(
            user_id="test-user-123",
            career_goals=["become a software developer"],
            learning_preferences=preferences
        )
        
        context.add_skill("python", SkillLevelEnum.BEGINNER, 0.6)
        return context
    
    @pytest.fixture
    def mock_gemini_model(self):
        """Create mock Gemini model"""
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = "Test response from Gemini"
        mock_model.generate_content.return_value = mock_response
        return mock_model
    
    def test_init_configures_gemini(self):
        """Test that initialization configures Gemini API"""
        with patch('edagent.services.ai_service.genai.configure') as mock_configure:
            service = GeminiAIService()
            mock_configure.assert_called_once()
    
    def test_init_handles_configuration_error(self):
        """Test that initialization handles configuration errors"""
        with patch('edagent.services.ai_service.genai.configure', side_effect=Exception("API key error")):
            with pytest.raises(GeminiAPIError, match="Failed to configure Gemini API"):
                GeminiAIService()
    
    def test_get_model_chat(self, ai_service):
        """Test getting chat model"""
        with patch('edagent.services.ai_service.genai.GenerativeModel') as mock_model_class:
            model = ai_service._get_model("chat")
            mock_model_class.assert_called_once()
            # Verify it was called with the correct model name
            call_args = mock_model_class.call_args
            assert call_args.kwargs['model_name'] == ai_service.settings.gemini_model_chat
    
    def test_get_model_reasoning(self, ai_service):
        """Test getting reasoning model"""
        with patch('edagent.services.ai_service.genai.GenerativeModel') as mock_model_class:
            model = ai_service._get_model("reasoning")
            mock_model_class.assert_called_once()
            # Verify it was called with the correct model name
            call_args = mock_model_class.call_args
            assert call_args.kwargs['model_name'] == ai_service.settings.gemini_model_reasoning
    
    def test_get_generation_config_chat(self, ai_service):
        """Test generation config for chat"""
        config = ai_service._get_generation_config("chat")
        assert config["temperature"] == ai_service.settings.gemini_temperature_chat
        assert config["max_output_tokens"] == ai_service.settings.gemini_max_tokens_response
    
    def test_get_generation_config_reasoning(self, ai_service):
        """Test generation config for reasoning"""
        config = ai_service._get_generation_config("reasoning")
        assert config["temperature"] == ai_service.settings.gemini_temperature_reasoning
        assert config["max_output_tokens"] == ai_service.settings.gemini_max_tokens_learning_path
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_within_limit(self, ai_service):
        """Test rate limiting when within limits"""
        ai_service._request_count = 5
        ai_service._last_request_time = datetime.now()
        
        # Should not raise or delay
        await ai_service._check_rate_limit()
        assert ai_service._request_count == 6
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self, ai_service):
        """Test rate limiting when limit is exceeded"""
        ai_service._request_count = ai_service.settings.rate_limit_requests_per_minute
        ai_service._last_request_time = datetime.now()
        
        # Mock sleep to avoid actual delay in tests
        with patch('asyncio.sleep') as mock_sleep:
            await ai_service._check_rate_limit()
            mock_sleep.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_make_api_call_success(self, ai_service, mock_gemini_model):
        """Test successful API call"""
        with patch.object(ai_service, '_get_model', return_value=mock_gemini_model):
            with patch.object(ai_service, '_check_rate_limit'):
                result = await ai_service._make_api_call(
                    mock_gemini_model, 
                    "test prompt", 
                    {"temperature": 0.7}
                )
                assert result == "Test response from Gemini"
    
    @pytest.mark.asyncio
    async def test_make_api_call_empty_response(self, ai_service, mock_gemini_model):
        """Test API call with empty response"""
        mock_response = Mock()
        mock_response.text = ""
        mock_gemini_model.generate_content.return_value = mock_response
        
        with patch.object(ai_service, '_check_rate_limit'):
            with pytest.raises(GeminiAPIError, match="Empty response"):
                await ai_service._make_api_call(
                    mock_gemini_model, 
                    "test prompt", 
                    {"temperature": 0.7}
                )
    
    @pytest.mark.asyncio
    async def test_make_api_call_rate_limit_error(self, ai_service, mock_gemini_model):
        """Test API call with rate limit error"""
        mock_gemini_model.generate_content.side_effect = Exception("rate limit exceeded")
        
        with patch.object(ai_service, '_check_rate_limit'):
            # Test that RateLimitError is eventually raised after retries
            from tenacity import RetryError
            with pytest.raises((RateLimitError, RetryError)):
                await ai_service._make_api_call(
                    mock_gemini_model, 
                    "test prompt", 
                    {"temperature": 0.7}
                )
    
    @pytest.mark.asyncio
    async def test_make_api_call_quota_error(self, ai_service, mock_gemini_model):
        """Test API call with quota exceeded error"""
        mock_gemini_model.generate_content.side_effect = Exception("quota exceeded")
        
        with patch.object(ai_service, '_check_rate_limit'):
            with pytest.raises(QuotaExceededError):
                await ai_service._make_api_call(
                    mock_gemini_model, 
                    "test prompt", 
                    {"temperature": 0.7}
                )
    
    def test_build_system_prompt_basic(self, ai_service):
        """Test building basic system prompt"""
        prompt = ai_service.build_system_prompt(None)
        assert "EdAgent" in prompt
        assert "career coach" in prompt
        assert "encouraging" in prompt
    
    def test_build_system_prompt_with_context(self, ai_service, sample_user_context):
        """Test building system prompt with user context"""
        prompt = ai_service.build_system_prompt(sample_user_context)
        assert "test-user-123" in prompt
        assert "become a software developer" in prompt
        assert "python (beginner)" in prompt
        assert "visual" in prompt
        assert "2-3 hours/week" in prompt
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, ai_service, sample_user_context, mock_gemini_model):
        """Test successful response generation"""
        with patch.object(ai_service, '_get_model', return_value=mock_gemini_model):
            with patch.object(ai_service, '_make_api_call', return_value="Great question! Here's my advice..."):
                response = await ai_service.generate_response(
                    "How do I learn Python?", 
                    sample_user_context
                )
                assert response == "Great question! Here's my advice..."
    
    @pytest.mark.asyncio
    async def test_generate_response_error_fallback(self, ai_service, sample_user_context):
        """Test response generation with error fallback"""
        with patch.object(ai_service, '_make_api_call', side_effect=Exception("API error")):
            response = await ai_service.generate_response(
                "How do I learn Python?", 
                sample_user_context
            )
            assert "having trouble connecting" in response
    
    @pytest.mark.asyncio
    async def test_assess_skills_success(self, ai_service):
        """Test successful skill assessment"""
        assessment_json = {
            "skill_area": "Python Programming",
            "overall_level": "beginner",
            "confidence_score": 0.6,
            "strengths": ["Basic syntax understanding"],
            "weaknesses": ["Needs more practice with functions"],
            "recommendations": ["Practice with coding exercises"],
            "detailed_scores": {"syntax": 0.7, "logic": 0.5}
        }
        
        mock_response = json.dumps(assessment_json)
        
        with patch.object(ai_service, '_make_api_call', return_value=mock_response):
            responses = ["I know basic Python syntax", "I struggle with functions"]
            assessment = await ai_service.assess_skills(responses)
            
            assert assessment.skill_area == "Python Programming"
            assert assessment.overall_level == DifficultyLevel.BEGINNER
            assert assessment.confidence_score == 0.6
            assert "Basic syntax understanding" in assessment.strengths
            assert "Needs more practice with functions" in assessment.weaknesses
    
    @pytest.mark.asyncio
    async def test_assess_skills_json_parsing_error(self, ai_service):
        """Test skill assessment with JSON parsing error"""
        with patch.object(ai_service, '_make_api_call', return_value="Invalid JSON response"):
            responses = ["I know some Python"]
            assessment = await ai_service.assess_skills(responses)
            
            # Should return default assessment
            assert assessment.skill_area == "General"
            assert assessment.overall_level == DifficultyLevel.BEGINNER
            assert "Willingness to learn" in assessment.strengths
    
    @pytest.mark.asyncio
    async def test_assess_skills_api_error(self, ai_service):
        """Test skill assessment with API error"""
        with patch.object(ai_service, '_make_api_call', side_effect=Exception("API error")):
            responses = ["I know some Python"]
            assessment = await ai_service.assess_skills(responses)
            
            # Should return default assessment
            assert assessment.skill_area == "General"
            assert assessment.overall_level == DifficultyLevel.BEGINNER
            assert any("motivation" in strength.lower() for strength in assessment.strengths)
    
    @pytest.mark.asyncio
    async def test_create_learning_path_success(self, ai_service):
        """Test successful learning path creation"""
        learning_path_json = {
            "title": "Python Developer Path",
            "description": "Learn Python programming from scratch",
            "difficulty_level": "beginner",
            "prerequisites": ["Basic computer skills"],
            "target_skills": ["Python programming", "Web development"],
            "milestones": [
                {
                    "title": "Python Basics",
                    "description": "Learn fundamental Python concepts",
                    "skills_to_learn": ["Variables", "Functions"],
                    "prerequisites": [],
                    "estimated_duration_days": 14,
                    "difficulty_level": "beginner",
                    "assessment_criteria": ["Complete basic exercises"],
                    "resources": [
                        {
                            "title": "Python Tutorial",
                            "url": "https://python.org/tutorial",
                            "type": "article",
                            "is_free": True,
                            "duration_hours": 10
                        }
                    ]
                }
            ]
        }
        
        mock_response = json.dumps(learning_path_json)
        
        with patch.object(ai_service, '_make_api_call', return_value=mock_response):
            current_skills = {}
            path = await ai_service.create_learning_path("Learn Python", current_skills)
            
            assert path.title == "Python Developer Path"
            assert path.goal == "Learn Python"
            assert len(path.milestones) == 1
            assert path.milestones[0].title == "Python Basics"
            assert len(path.milestones[0].resources) == 1
    
    @pytest.mark.asyncio
    async def test_create_learning_path_json_error(self, ai_service):
        """Test learning path creation with JSON parsing error"""
        with patch.object(ai_service, '_make_api_call', return_value="Invalid JSON"):
            current_skills = {}
            path = await ai_service.create_learning_path("Learn Python", current_skills)
            
            # Should return fallback path
            assert "Basic Path: Learn Python" in path.title
            assert path.goal == "Learn Python"
            assert len(path.milestones) == 1
    
    @pytest.mark.asyncio
    async def test_create_learning_path_api_error(self, ai_service):
        """Test learning path creation with API error"""
        with patch.object(ai_service, '_make_api_call', side_effect=Exception("API error")):
            current_skills = {}
            path = await ai_service.create_learning_path("Learn Python", current_skills)
            
            # Should return fallback path
            assert "Basic Path: Learn Python" in path.title
            assert path.goal == "Learn Python"
            assert len(path.milestones) == 1
    
    def test_create_fallback_learning_path(self, ai_service):
        """Test fallback learning path creation"""
        path = ai_service.response_handler._create_fallback_learning_path("Learn JavaScript")
        
        assert "Basic Path: Learn JavaScript" in path.title
        assert path.goal == "Learn JavaScript"
        assert len(path.milestones) == 1
        assert path.milestones[0].title == "Get Started"
        assert len(path.milestones[0].resources) == 1


class TestGeminiAIServiceIntegration:
    """Integration tests for GeminiAIService (require actual API key)"""
    
    @pytest.fixture
    def ai_service_real(self):
        """Create AI service for integration testing"""
        # Skip if no API key available
        try:
            service = GeminiAIService()
            return service
        except GeminiAPIError:
            pytest.skip("Gemini API key not available for integration tests")
    
    @pytest.fixture
    def sample_user_context(self):
        """Create sample user context for integration testing"""
        preferences = UserPreferences(
            learning_style=LearningStyleEnum.VISUAL,
            time_commitment="2-3 hours/week",
            budget_preference="free"
        )
        
        context = UserContext(
            user_id="integration-test-user",
            career_goals=["learn web development"],
            learning_preferences=preferences
        )
        
        context.add_skill("html", SkillLevelEnum.BEGINNER, 0.7)
        return context
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_generate_response(self, ai_service_real, sample_user_context):
        """Test actual response generation with Gemini API"""
        if not ai_service_real:
            pytest.skip("Integration test requires API key")
        
        response = await ai_service_real.generate_response(
            "What should I learn next in web development?",
            sample_user_context
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        # Response should be relevant to web development
        assert any(keyword in response.lower() for keyword in ["css", "javascript", "web", "development"])
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_assess_skills(self, ai_service_real):
        """Test actual skill assessment with Gemini API"""
        if not ai_service_real:
            pytest.skip("Integration test requires API key")
        
        responses = [
            "I know HTML tags and can create basic web pages",
            "I understand CSS for styling but struggle with layouts",
            "I haven't learned JavaScript yet"
        ]
        
        assessment = await ai_service_real.assess_skills(responses)
        
        assert isinstance(assessment, SkillAssessment)
        assert assessment.skill_area
        assert assessment.overall_level in [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE]
        assert 0.0 <= assessment.confidence_score <= 1.0
        assert len(assessment.strengths) > 0
        assert len(assessment.recommendations) > 0
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_create_learning_path(self, ai_service_real):
        """Test actual learning path creation with Gemini API"""
        if not ai_service_real:
            pytest.skip("Integration test requires API key")
        
        current_skills = {
            "html": SkillLevel("html", SkillLevelEnum.BEGINNER, 0.6)
        }
        
        path = await ai_service_real.create_learning_path(
            "Become a front-end web developer",
            current_skills
        )
        
        assert isinstance(path, LearningPath)
        assert path.title
        assert path.goal == "Become a front-end web developer"
        assert len(path.milestones) > 0
        assert len(path.target_skills) > 0
        
        # Check that milestones have proper structure
        for milestone in path.milestones:
            assert milestone.title
            assert milestone.description
            assert len(milestone.skills_to_learn) > 0