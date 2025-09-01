"""
Unit tests for the response processing system
"""

import pytest
import json
from datetime import datetime, timedelta

from edagent.services.response_processing import (
    ResponseValidator,
    ResponseParser,
    StructuredResponseHandler,
    ResponseEnhancer,
    ResponseParsingError,
    process_skill_assessment_response,
    process_learning_path_response,
    process_conversation_response
)
from edagent.models.user_context import UserContext, SkillLevel, SkillLevelEnum, UserPreferences, LearningStyleEnum
from edagent.models.learning import SkillAssessment, LearningPath, DifficultyLevel


class TestResponseValidator:
    """Test cases for ResponseValidator"""
    
    def test_validate_skill_assessment_data_valid(self):
        """Test validation of valid skill assessment data"""
        data = {
            "skill_area": "Python Programming",
            "overall_level": "beginner",
            "confidence_score": 0.6,
            "strengths": ["Basic syntax understanding"],
            "weaknesses": ["Needs more practice"],
            "recommendations": ["Practice coding exercises"],
            "detailed_scores": {"syntax": 0.7, "logic": 0.5}
        }
        
        assert ResponseValidator.validate_skill_assessment_data(data) is True
    
    def test_validate_skill_assessment_data_missing_fields(self):
        """Test validation with missing required fields"""
        data = {
            "skill_area": "Python Programming",
            "overall_level": "beginner"
            # Missing other required fields
        }
        
        assert ResponseValidator.validate_skill_assessment_data(data) is False
    
    def test_validate_skill_assessment_data_invalid_level(self):
        """Test validation with invalid overall level"""
        data = {
            "skill_area": "Python Programming",
            "overall_level": "expert",  # Invalid level
            "confidence_score": 0.6,
            "strengths": ["Basic syntax"],
            "weaknesses": ["Needs practice"],
            "recommendations": ["Practice more"]
        }
        
        assert ResponseValidator.validate_skill_assessment_data(data) is False
    
    def test_validate_skill_assessment_data_invalid_confidence_score(self):
        """Test validation with invalid confidence score"""
        data = {
            "skill_area": "Python Programming",
            "overall_level": "beginner",
            "confidence_score": 1.5,  # Invalid score > 1.0
            "strengths": ["Basic syntax"],
            "weaknesses": ["Needs practice"],
            "recommendations": ["Practice more"]
        }
        
        assert ResponseValidator.validate_skill_assessment_data(data) is False
    
    def test_validate_learning_path_data_valid(self):
        """Test validation of valid learning path data"""
        data = {
            "title": "Python Learning Path",
            "description": "Learn Python from scratch",
            "difficulty_level": "beginner",
            "milestones": [
                {
                    "title": "Python Basics",
                    "description": "Learn fundamental concepts",
                    "skills_to_learn": ["Variables", "Functions"],
                    "resources": [
                        {
                            "title": "Python Tutorial",
                            "type": "video",
                            "url": "https://example.com",
                            "is_free": True,
                            "duration_hours": 2
                        }
                    ]
                }
            ]
        }
        
        assert ResponseValidator.validate_learning_path_data(data) is True
    
    def test_validate_learning_path_data_empty_milestones(self):
        """Test validation with empty milestones"""
        data = {
            "title": "Python Learning Path",
            "description": "Learn Python from scratch",
            "milestones": []  # Empty milestones
        }
        
        assert ResponseValidator.validate_learning_path_data(data) is False
    
    def test_validate_milestone_data_valid(self):
        """Test validation of valid milestone data"""
        data = {
            "title": "Python Basics",
            "description": "Learn fundamental concepts",
            "skills_to_learn": ["Variables", "Functions"],
            "prerequisites": ["Basic computer skills"],
            "difficulty_level": "beginner",
            "assessment_criteria": ["Complete exercises"]
        }
        
        assert ResponseValidator.validate_milestone_data(data) is True
    
    def test_validate_milestone_data_missing_title(self):
        """Test validation with missing title"""
        data = {
            "description": "Learn fundamental concepts"
            # Missing title
        }
        
        assert ResponseValidator.validate_milestone_data(data) is False
    
    def test_validate_resource_data_valid(self):
        """Test validation of valid resource data"""
        data = {
            "title": "Python Tutorial",
            "type": "video",
            "url": "https://example.com",
            "is_free": True,
            "duration_hours": 2
        }
        
        assert ResponseValidator.validate_resource_data(data) is True
    
    def test_validate_resource_data_invalid_type(self):
        """Test validation with invalid resource type"""
        data = {
            "title": "Python Tutorial",
            "type": "invalid_type",  # Invalid type
            "url": "https://example.com"
        }
        
        assert ResponseValidator.validate_resource_data(data) is False


class TestResponseParser:
    """Test cases for ResponseParser"""
    
    def test_extract_json_from_response_pure_json(self):
        """Test extracting JSON from pure JSON response"""
        json_data = {"test": "value", "number": 42}
        response = json.dumps(json_data)
        
        result = ResponseParser.extract_json_from_response(response)
        assert result == json_data
    
    def test_extract_json_from_response_with_text(self):
        """Test extracting JSON from response with surrounding text"""
        json_data = {"test": "value", "number": 42}
        response = f"Here is the result: {json.dumps(json_data)} Hope this helps!"
        
        result = ResponseParser.extract_json_from_response(response)
        assert result == json_data
    
    def test_extract_json_from_response_code_block(self):
        """Test extracting JSON from code block"""
        json_data = {"test": "value", "number": 42}
        response = f"```json\n{json.dumps(json_data)}\n```"
        
        result = ResponseParser.extract_json_from_response(response)
        assert result == json_data
    
    def test_extract_json_from_response_invalid(self):
        """Test extracting JSON from invalid response"""
        response = "This is not JSON at all"
        
        result = ResponseParser.extract_json_from_response(response)
        assert result is None
    
    def test_parse_skill_assessment_response_valid(self):
        """Test parsing valid skill assessment response"""
        data = {
            "skill_area": "Python Programming",
            "overall_level": "beginner",
            "confidence_score": 0.6,
            "strengths": ["Basic syntax"],
            "weaknesses": ["Needs practice"],
            "recommendations": ["Practice more"]
        }
        response = json.dumps(data)
        
        result = ResponseParser.parse_skill_assessment_response(response)
        assert result == data
    
    def test_parse_skill_assessment_response_invalid(self):
        """Test parsing invalid skill assessment response"""
        response = "Invalid response"
        
        result = ResponseParser.parse_skill_assessment_response(response)
        assert result is None
    
    def test_parse_learning_path_response_valid(self):
        """Test parsing valid learning path response"""
        data = {
            "title": "Python Learning Path",
            "description": "Learn Python",
            "milestones": [
                {
                    "title": "Basics",
                    "description": "Learn basics"
                }
            ]
        }
        response = json.dumps(data)
        
        result = ResponseParser.parse_learning_path_response(response)
        assert result == data
    
    def test_clean_and_normalize_text(self):
        """Test text cleaning and normalization"""
        text = "  **Bold text**  and  *italic*  and  `code`  "
        
        result = ResponseParser.clean_and_normalize_text(text)
        assert result == "Bold text and italic and code"
    
    def test_clean_and_normalize_text_empty(self):
        """Test cleaning empty text"""
        result = ResponseParser.clean_and_normalize_text("")
        assert result == ""
    
    def test_clean_and_normalize_text_none(self):
        """Test cleaning None text"""
        result = ResponseParser.clean_and_normalize_text(None)
        assert result == ""


class TestStructuredResponseHandler:
    """Test cases for StructuredResponseHandler"""
    
    @pytest.fixture
    def handler(self):
        """Create StructuredResponseHandler instance for testing"""
        return StructuredResponseHandler()
    
    def test_process_skill_assessment_response_valid(self, handler):
        """Test processing valid skill assessment response"""
        data = {
            "skill_area": "Python Programming",
            "overall_level": "beginner",
            "confidence_score": 0.6,
            "strengths": ["Basic syntax understanding"],
            "weaknesses": ["Needs more practice with functions"],
            "recommendations": ["Practice coding exercises"],
            "detailed_scores": {"syntax": 0.7, "logic": 0.5}
        }
        response = json.dumps(data)
        
        result = handler.process_skill_assessment_response(response, "test-user")
        
        assert isinstance(result, SkillAssessment)
        assert result.user_id == "test-user"
        assert result.skill_area == "Python Programming"
        assert result.overall_level == DifficultyLevel.BEGINNER
        assert result.confidence_score == 0.6
        assert "Basic syntax understanding" in result.strengths
    
    def test_process_skill_assessment_response_invalid(self, handler):
        """Test processing invalid skill assessment response"""
        response = "Invalid JSON response"
        
        result = handler.process_skill_assessment_response(response, "test-user")
        
        assert isinstance(result, SkillAssessment)
        assert result.user_id == "test-user"
        assert result.skill_area == "General"
        assert result.overall_level == DifficultyLevel.BEGINNER
        assert "Willingness to learn" in result.strengths
    
    def test_process_learning_path_response_valid(self, handler):
        """Test processing valid learning path response"""
        data = {
            "title": "Python Developer Path",
            "description": "Learn Python programming",
            "difficulty_level": "beginner",
            "prerequisites": ["Basic computer skills"],
            "target_skills": ["Python programming"],
            "milestones": [
                {
                    "title": "Python Basics",
                    "description": "Learn fundamental concepts",
                    "skills_to_learn": ["Variables", "Functions"],
                    "prerequisites": [],
                    "estimated_duration_days": 14,
                    "difficulty_level": "beginner",
                    "assessment_criteria": ["Complete exercises"],
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
        response = json.dumps(data)
        
        result = handler.process_learning_path_response(response, "Learn Python")
        
        assert isinstance(result, LearningPath)
        assert result.title == "Python Developer Path"
        assert result.goal == "Learn Python"
        assert len(result.milestones) == 1
        assert result.milestones[0].title == "Python Basics"
        assert len(result.milestones[0].resources) == 1
    
    def test_process_learning_path_response_invalid(self, handler):
        """Test processing invalid learning path response"""
        response = "Invalid JSON response"
        
        result = handler.process_learning_path_response(response, "Learn Python")
        
        assert isinstance(result, LearningPath)
        assert "Basic Path: Learn Python" in result.title
        assert result.goal == "Learn Python"
        assert len(result.milestones) == 1
    
    def test_process_conversation_response_valid(self, handler):
        """Test processing valid conversation response"""
        response = "This is a **great** question! I'm happy to help you learn Python."
        
        result = handler.process_conversation_response(response)
        
        assert isinstance(result, str)
        assert "great" in result
        assert "Python" in result
        assert "**" not in result  # Markdown should be cleaned
    
    def test_process_conversation_response_too_short(self, handler):
        """Test processing too short conversation response"""
        response = "Yes."
        
        result = handler.process_conversation_response(response)
        
        assert isinstance(result, str)
        assert "I'm here to help" in result  # Should use fallback
    
    def test_process_conversation_response_too_long(self, handler):
        """Test processing too long conversation response"""
        response = "A" * 2500  # Very long response
        
        result = handler.process_conversation_response(response)
        
        assert isinstance(result, str)
        assert len(result) <= 2000
        assert result.endswith("...")
    
    def test_create_fallback_skill_assessment(self, handler):
        """Test creating fallback skill assessment"""
        result = handler._create_fallback_skill_assessment("test-user")
        
        assert isinstance(result, SkillAssessment)
        assert result.user_id == "test-user"
        assert result.skill_area == "General"
        assert len(result.strengths) > 0
        assert len(result.recommendations) > 0
    
    def test_create_fallback_learning_path(self, handler):
        """Test creating fallback learning path"""
        result = handler._create_fallback_learning_path("Learn JavaScript")
        
        assert isinstance(result, LearningPath)
        assert "Learn JavaScript" in result.title
        assert result.goal == "Learn JavaScript"
        assert len(result.milestones) == 1
        assert len(result.milestones[0].resources) == 1


class TestResponseEnhancer:
    """Test cases for ResponseEnhancer"""
    
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
        
        return context
    
    def test_enhance_skill_assessment_with_context(self, sample_user_context):
        """Test enhancing skill assessment with user context"""
        assessment = SkillAssessment(
            user_id="test-user",
            skill_area="Python",
            overall_level=DifficultyLevel.BEGINNER,
            confidence_score=0.6,
            strengths=["Basic syntax"],
            weaknesses=["Functions"],
            recommendations=["Practice more"]
        )
        
        original_count = len(assessment.recommendations)
        enhanced = ResponseEnhancer.enhance_skill_assessment(assessment, sample_user_context)
        
        assert isinstance(enhanced, SkillAssessment)
        assert len(enhanced.recommendations) > original_count
        assert any("video" in rec.lower() for rec in enhanced.recommendations)
        assert any("free" in rec.lower() for rec in enhanced.recommendations)
    
    def test_enhance_skill_assessment_without_context(self):
        """Test enhancing skill assessment without user context"""
        assessment = SkillAssessment(
            user_id="test-user",
            skill_area="Python",
            overall_level=DifficultyLevel.BEGINNER,
            confidence_score=0.6,
            strengths=["Basic syntax"],
            weaknesses=["Functions"],
            recommendations=["Practice more"]
        )
        
        enhanced = ResponseEnhancer.enhance_skill_assessment(assessment, None)
        
        assert isinstance(enhanced, SkillAssessment)
        assert enhanced == assessment  # Should be unchanged
    
    def test_enhance_learning_path_with_context(self, sample_user_context):
        """Test enhancing learning path with user context"""
        from edagent.models.learning import Milestone
        
        milestone = Milestone(
            title="Test Milestone",
            description="Test description"
        )
        milestone.resources = [
            {"title": "Free Resource", "is_free": True, "type": "video"},
            {"title": "Paid Resource", "is_free": False, "type": "course"}
        ]
        
        path = LearningPath(
            title="Test Path",
            description="Test description",
            goal="Learn something",
            milestones=[milestone]
        )
        
        enhanced = ResponseEnhancer.enhance_learning_path(path, sample_user_context)
        
        assert isinstance(enhanced, LearningPath)
        # Should filter out paid resources for free budget preference
        assert all(r.get("is_free", True) for milestone in enhanced.milestones for r in milestone.resources)
    
    def test_add_motivational_elements(self, sample_user_context):
        """Test adding motivational elements to responses"""
        response = "Here's how to learn Python programming."
        
        enhanced = ResponseEnhancer.add_motivational_elements(response, sample_user_context)
        
        assert isinstance(enhanced, str)
        assert "Great question!" in enhanced
        assert response in enhanced


class TestConvenienceFunctions:
    """Test cases for convenience functions"""
    
    def test_process_skill_assessment_response_function(self):
        """Test convenience function for processing skill assessment"""
        data = {
            "skill_area": "Python Programming",
            "overall_level": "beginner",
            "confidence_score": 0.6,
            "strengths": ["Basic syntax"],
            "weaknesses": ["Needs practice"],
            "recommendations": ["Practice more"]
        }
        response = json.dumps(data)
        
        result = process_skill_assessment_response(response, "test-user")
        
        assert isinstance(result, SkillAssessment)
        assert result.user_id == "test-user"
        assert result.skill_area == "Python Programming"
    
    def test_process_learning_path_response_function(self):
        """Test convenience function for processing learning path"""
        data = {
            "title": "Python Path",
            "description": "Learn Python",
            "milestones": [
                {
                    "title": "Basics",
                    "description": "Learn basics"
                }
            ]
        }
        response = json.dumps(data)
        
        result = process_learning_path_response(response, "Learn Python")
        
        assert isinstance(result, LearningPath)
        assert result.title == "Python Path"
        assert result.goal == "Learn Python"
    
    def test_process_conversation_response_function(self):
        """Test convenience function for processing conversation response"""
        response = "This is a helpful response about learning."
        
        result = process_conversation_response(response)
        
        assert isinstance(result, str)
        assert "helpful" in result


class TestErrorHandling:
    """Test cases for error handling in response processing"""
    
    @pytest.fixture
    def handler(self):
        """Create StructuredResponseHandler instance for testing"""
        return StructuredResponseHandler()
    
    def test_malformed_json_handling(self, handler):
        """Test handling of malformed JSON responses"""
        response = '{"skill_area": "Python", "overall_level": "beginner"'  # Missing closing brace
        
        result = handler.process_skill_assessment_response(response, "test-user")
        
        assert isinstance(result, SkillAssessment)
        assert result.skill_area == "General"  # Should use fallback
    
    def test_missing_required_fields_handling(self, handler):
        """Test handling of responses with missing required fields"""
        data = {
            "skill_area": "Python",
            # Missing other required fields
        }
        response = json.dumps(data)
        
        result = handler.process_skill_assessment_response(response, "test-user")
        
        assert isinstance(result, SkillAssessment)
        assert result.skill_area == "General"  # Should use fallback
    
    def test_invalid_data_types_handling(self, handler):
        """Test handling of responses with invalid data types"""
        data = {
            "skill_area": "Python",
            "overall_level": "beginner",
            "confidence_score": "invalid",  # Should be float
            "strengths": "not a list",  # Should be list
            "weaknesses": ["valid list"],
            "recommendations": ["valid list"]
        }
        response = json.dumps(data)
        
        result = handler.process_skill_assessment_response(response, "test-user")
        
        assert isinstance(result, SkillAssessment)
        assert result.skill_area == "General"  # Should use fallback
    
    def test_exception_during_processing(self, handler):
        """Test handling of exceptions during processing"""
        # This should trigger an exception in the processing logic
        response = None
        
        result = handler.process_conversation_response(response)
        
        assert isinstance(result, str)
        assert "I'm here to help" in result  # Should use fallback