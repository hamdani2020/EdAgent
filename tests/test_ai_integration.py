"""
Integration tests for AI service with response processing
"""

import pytest
import json
from unittest.mock import Mock, patch

from edagent.services.ai_service import GeminiAIService
from edagent.models.user_context import UserContext, SkillLevel, SkillLevelEnum, UserPreferences, LearningStyleEnum
from edagent.models.learning import SkillAssessment, LearningPath, DifficultyLevel


class TestAIServiceIntegration:
    """Integration tests for AI service with prompt engineering and response processing"""
    
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
            user_id="integration-test-user",
            career_goals=["become a web developer"],
            learning_preferences=preferences,
            conversation_history=["Hello", "I want to learn web development"]
        )
        
        context.add_skill("html", SkillLevelEnum.BEGINNER, 0.7)
        return context
    
    @pytest.mark.asyncio
    async def test_generate_response_with_processing(self, ai_service, sample_user_context):
        """Test response generation with full processing pipeline"""
        mock_response = "**Great question!** I'd be happy to help you learn web development. Since you already have some HTML knowledge, I recommend focusing on CSS next to improve your styling skills."
        
        with patch.object(ai_service, '_make_api_call', return_value=mock_response):
            response = await ai_service.generate_response(
                "What should I learn next in web development?",
                sample_user_context
            )
            
            # Response should be processed (markdown removed, etc.)
            assert isinstance(response, str)
            assert "Great question!" in response
            assert "**" not in response  # Markdown should be cleaned
            assert "CSS" in response
            assert len(response) > 10
    
    @pytest.mark.asyncio
    async def test_assess_skills_with_processing(self, ai_service):
        """Test skill assessment with full processing pipeline"""
        assessment_data = {
            "skill_area": "Web Development",
            "overall_level": "beginner",
            "confidence_score": 0.6,
            "strengths": ["Basic HTML understanding", "Eager to learn"],
            "weaknesses": ["Limited CSS knowledge", "No JavaScript experience"],
            "recommendations": ["Practice CSS layouts", "Learn JavaScript basics"],
            "detailed_scores": {"html": 0.7, "css": 0.3, "javascript": 0.1}
        }
        mock_response = json.dumps(assessment_data)
        
        with patch.object(ai_service, '_make_api_call', return_value=mock_response):
            responses = [
                "I know basic HTML tags and can create simple web pages",
                "I struggle with CSS layouts and positioning",
                "I haven't learned JavaScript yet but I'm interested"
            ]
            
            assessment = await ai_service.assess_skills(responses)
            
            assert isinstance(assessment, SkillAssessment)
            assert assessment.skill_area == "Web Development"
            assert assessment.overall_level == DifficultyLevel.BEGINNER
            assert assessment.confidence_score == 0.6
            assert "Basic HTML understanding" in assessment.strengths
            assert "Limited CSS knowledge" in assessment.weaknesses
            assert "Practice CSS layouts" in assessment.recommendations
            assert assessment.detailed_scores["html"] == 0.7
    
    @pytest.mark.asyncio
    async def test_assess_skills_with_invalid_response(self, ai_service):
        """Test skill assessment with invalid AI response (fallback handling)"""
        mock_response = "This is not valid JSON at all"
        
        with patch.object(ai_service, '_make_api_call', return_value=mock_response):
            responses = ["I know some programming"]
            
            assessment = await ai_service.assess_skills(responses)
            
            # Should return fallback assessment
            assert isinstance(assessment, SkillAssessment)
            assert assessment.skill_area == "General"
            assert assessment.overall_level == DifficultyLevel.BEGINNER
            assert "Willingness to learn" in assessment.strengths
    
    @pytest.mark.asyncio
    async def test_create_learning_path_with_processing(self, ai_service):
        """Test learning path creation with full processing pipeline"""
        path_data = {
            "title": "Web Development Mastery Path",
            "description": "Complete path to become a web developer",
            "difficulty_level": "beginner",
            "prerequisites": ["Basic computer skills"],
            "target_skills": ["HTML", "CSS", "JavaScript", "React"],
            "milestones": [
                {
                    "title": "HTML Fundamentals",
                    "description": "Master HTML structure and semantics",
                    "skills_to_learn": ["HTML tags", "Document structure", "Semantic HTML"],
                    "prerequisites": [],
                    "estimated_duration_days": 14,
                    "difficulty_level": "beginner",
                    "assessment_criteria": ["Build a complete webpage", "Use semantic HTML properly"],
                    "resources": [
                        {
                            "title": "HTML Crash Course",
                            "url": "https://youtube.com/watch?v=html-course",
                            "type": "video",
                            "is_free": True,
                            "duration_hours": 3
                        },
                        {
                            "title": "MDN HTML Guide",
                            "url": "https://developer.mozilla.org/en-US/docs/Web/HTML",
                            "type": "documentation",
                            "is_free": True,
                            "duration_hours": 5
                        }
                    ]
                },
                {
                    "title": "CSS Styling",
                    "description": "Learn to style web pages with CSS",
                    "skills_to_learn": ["CSS selectors", "Flexbox", "Grid"],
                    "prerequisites": ["HTML Fundamentals"],
                    "estimated_duration_days": 21,
                    "difficulty_level": "beginner",
                    "assessment_criteria": ["Create responsive layouts", "Style a complete website"],
                    "resources": [
                        {
                            "title": "CSS Complete Guide",
                            "url": "https://youtube.com/watch?v=css-guide",
                            "type": "video",
                            "is_free": True,
                            "duration_hours": 8
                        }
                    ]
                }
            ]
        }
        mock_response = json.dumps(path_data)
        
        with patch.object(ai_service, '_make_api_call', return_value=mock_response):
            current_skills = {
                "html": SkillLevel("html", SkillLevelEnum.BEGINNER, 0.6)
            }
            
            path = await ai_service.create_learning_path("Become a web developer", current_skills)
            
            assert isinstance(path, LearningPath)
            assert path.title == "Web Development Mastery Path"
            assert path.goal == "Become a web developer"
            assert path.difficulty_level == DifficultyLevel.BEGINNER
            assert len(path.milestones) == 2
            
            # Check first milestone
            html_milestone = path.milestones[0]
            assert html_milestone.title == "HTML Fundamentals"
            assert html_milestone.estimated_duration.days == 14
            assert len(html_milestone.resources) == 2
            assert html_milestone.resources[0]["title"] == "HTML Crash Course"
            
            # Check second milestone
            css_milestone = path.milestones[1]
            assert css_milestone.title == "CSS Styling"
            assert css_milestone.estimated_duration.days == 21
            assert "HTML Fundamentals" in css_milestone.prerequisites
    
    @pytest.mark.asyncio
    async def test_create_learning_path_with_invalid_response(self, ai_service):
        """Test learning path creation with invalid AI response (fallback handling)"""
        mock_response = "Invalid JSON response"
        
        with patch.object(ai_service, '_make_api_call', return_value=mock_response):
            current_skills = {}
            
            path = await ai_service.create_learning_path("Learn Python", current_skills)
            
            # Should return fallback path
            assert isinstance(path, LearningPath)
            assert "Basic Path: Learn Python" in path.title
            assert path.goal == "Learn Python"
            assert len(path.milestones) == 1
            assert path.milestones[0].title == "Get Started"
    
    @pytest.mark.asyncio
    async def test_prompt_engineering_integration(self, ai_service, sample_user_context):
        """Test that prompt engineering is properly integrated"""
        with patch.object(ai_service, '_make_api_call') as mock_call:
            mock_call.return_value = "I'd be happy to help you with web development!"
            
            await ai_service.generate_response("How do I learn CSS?", sample_user_context)
            
            # Verify that the prompt includes user context
            call_args = mock_call.call_args[0]
            prompt = call_args[1]  # Second argument is the prompt
            
            assert "EdAgent" in prompt
            assert "integration-test-user" in prompt
            assert "become a web developer" in prompt
            assert "html (beginner)" in prompt
            assert "visual" in prompt
            assert "How do I learn CSS?" in prompt
    
    @pytest.mark.asyncio
    async def test_skill_area_inference(self, ai_service):
        """Test that skill area inference works correctly"""
        # Test programming responses
        programming_responses = [
            "I know Python and have built some scripts",
            "I struggle with object-oriented programming concepts",
            "I want to learn more about algorithms and data structures"
        ]
        
        inferred_area = ai_service._infer_skill_area(programming_responses)
        assert inferred_area == "Programming"
        
        # Test web development responses
        web_responses = [
            "I know HTML and CSS basics",
            "I've built a few websites using React",
            "I want to learn more about frontend development"
        ]
        
        inferred_area = ai_service._infer_skill_area(web_responses)
        assert inferred_area == "Web Development"
        
        # Test data science responses
        data_responses = [
            "I work with data analysis using pandas",
            "I know some statistics and machine learning",
            "I want to improve my SQL skills"
        ]
        
        inferred_area = ai_service._infer_skill_area(data_responses)
        assert inferred_area == "Data Science"
        
        # Test unknown area
        unknown_responses = [
            "I like learning new things",
            "I'm interested in technology",
            "I want to advance my career"
        ]
        
        inferred_area = ai_service._infer_skill_area(unknown_responses)
        assert inferred_area == "General"
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, ai_service, sample_user_context):
        """Test error handling throughout the integration"""
        # Test API error handling
        with patch.object(ai_service, '_make_api_call', side_effect=Exception("API Error")):
            response = await ai_service.generate_response("Test question", sample_user_context)
            
            # Should return fallback response
            assert isinstance(response, str)
            assert "having trouble connecting" in response
        
        # Test skill assessment error handling
        with patch.object(ai_service, '_make_api_call', side_effect=Exception("API Error")):
            assessment = await ai_service.assess_skills(["I know programming"])
            
            # Should return fallback assessment
            assert isinstance(assessment, SkillAssessment)
            assert assessment.skill_area == "General"
        
        # Test learning path error handling
        with patch.object(ai_service, '_make_api_call', side_effect=Exception("API Error")):
            path = await ai_service.create_learning_path("Learn something", {})
            
            # Should return fallback path
            assert isinstance(path, LearningPath)
            assert "Basic Path" in path.title