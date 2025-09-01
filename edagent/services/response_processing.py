"""
AI response processing and validation for EdAgent
"""

import json
import re
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta

from ..models.user_context import UserContext, SkillLevel, SkillLevelEnum
from ..models.learning import SkillAssessment, LearningPath, Milestone, DifficultyLevel


logger = logging.getLogger(__name__)


class ResponseParsingError(Exception):
    """Exception raised when response parsing fails"""
    pass


class ResponseValidator:
    """Validates AI responses for correctness and completeness"""
    
    @staticmethod
    def validate_skill_assessment_data(data: Dict[str, Any]) -> bool:
        """Validate skill assessment response data"""
        required_fields = ["skill_area", "overall_level", "confidence_score", "strengths", "weaknesses", "recommendations"]
        
        # Check required fields exist
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field in skill assessment: {field}")
                return False
        
        # Validate field types and values
        if not isinstance(data["skill_area"], str) or not data["skill_area"].strip():
            logger.warning("Invalid skill_area in assessment data")
            return False
        
        if data["overall_level"] not in ["beginner", "intermediate", "advanced"]:
            logger.warning(f"Invalid overall_level: {data['overall_level']}")
            return False
        
        if not isinstance(data["confidence_score"], (int, float)) or not 0.0 <= data["confidence_score"] <= 1.0:
            logger.warning(f"Invalid confidence_score: {data['confidence_score']}")
            return False
        
        if not isinstance(data["strengths"], list) or not isinstance(data["weaknesses"], list):
            logger.warning("Strengths and weaknesses must be lists")
            return False
        
        if not isinstance(data["recommendations"], list):
            logger.warning("Recommendations must be a list")
            return False
        
        # Validate detailed_scores if present
        if "detailed_scores" in data:
            if not isinstance(data["detailed_scores"], dict):
                logger.warning("detailed_scores must be a dictionary")
                return False
            
            for category, score in data["detailed_scores"].items():
                if not isinstance(score, (int, float)) or not 0.0 <= score <= 1.0:
                    logger.warning(f"Invalid detailed score for {category}: {score}")
                    return False
        
        return True
    
    @staticmethod
    def validate_learning_path_data(data: Dict[str, Any]) -> bool:
        """Validate learning path response data"""
        required_fields = ["title", "description", "milestones"]
        
        # Check required fields exist
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field in learning path: {field}")
                return False
        
        # Validate basic fields
        if not isinstance(data["title"], str) or not data["title"].strip():
            logger.warning("Invalid title in learning path data")
            return False
        
        if not isinstance(data["description"], str):
            logger.warning("Invalid description in learning path data")
            return False
        
        if not isinstance(data["milestones"], list) or len(data["milestones"]) == 0:
            logger.warning("Milestones must be a non-empty list")
            return False
        
        # Validate difficulty level if present
        if "difficulty_level" in data and data["difficulty_level"] not in ["beginner", "intermediate", "advanced"]:
            logger.warning(f"Invalid difficulty_level: {data['difficulty_level']}")
            return False
        
        # Validate each milestone
        for i, milestone in enumerate(data["milestones"]):
            if not ResponseValidator.validate_milestone_data(milestone, i):
                return False
        
        return True
    
    @staticmethod
    def validate_milestone_data(data: Dict[str, Any], index: int = 0) -> bool:
        """Validate milestone data"""
        required_fields = ["title", "description"]
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field in milestone {index}: {field}")
                return False
        
        # Validate basic fields
        if not isinstance(data["title"], str) or not data["title"].strip():
            logger.warning(f"Invalid title in milestone {index}")
            return False
        
        if not isinstance(data["description"], str):
            logger.warning(f"Invalid description in milestone {index}")
            return False
        
        # Validate optional fields
        if "skills_to_learn" in data and not isinstance(data["skills_to_learn"], list):
            logger.warning(f"skills_to_learn must be a list in milestone {index}")
            return False
        
        if "prerequisites" in data and not isinstance(data["prerequisites"], list):
            logger.warning(f"prerequisites must be a list in milestone {index}")
            return False
        
        if "assessment_criteria" in data and not isinstance(data["assessment_criteria"], list):
            logger.warning(f"assessment_criteria must be a list in milestone {index}")
            return False
        
        if "difficulty_level" in data and data["difficulty_level"] not in ["beginner", "intermediate", "advanced"]:
            logger.warning(f"Invalid difficulty_level in milestone {index}: {data['difficulty_level']}")
            return False
        
        # Validate resources if present
        if "resources" in data:
            if not isinstance(data["resources"], list):
                logger.warning(f"resources must be a list in milestone {index}")
                return False
            
            for j, resource in enumerate(data["resources"]):
                if not ResponseValidator.validate_resource_data(resource, index, j):
                    return False
        
        return True
    
    @staticmethod
    def validate_resource_data(data: Dict[str, Any], milestone_index: int = 0, resource_index: int = 0) -> bool:
        """Validate resource data"""
        required_fields = ["title", "type"]
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field in resource {milestone_index}.{resource_index}: {field}")
                return False
        
        # Validate basic fields
        if not isinstance(data["title"], str) or not data["title"].strip():
            logger.warning(f"Invalid title in resource {milestone_index}.{resource_index}")
            return False
        
        valid_types = ["video", "course", "article", "interactive", "book", "tutorial", "documentation"]
        if data["type"] not in valid_types:
            logger.warning(f"Invalid resource type in {milestone_index}.{resource_index}: {data['type']}")
            return False
        
        # Validate optional fields
        if "url" in data and data["url"] and not isinstance(data["url"], str):
            logger.warning(f"Invalid URL in resource {milestone_index}.{resource_index}")
            return False
        
        if "is_free" in data and not isinstance(data["is_free"], bool):
            logger.warning(f"is_free must be boolean in resource {milestone_index}.{resource_index}")
            return False
        
        if "duration_hours" in data:
            if not isinstance(data["duration_hours"], (int, float)) or data["duration_hours"] < 0:
                logger.warning(f"Invalid duration_hours in resource {milestone_index}.{resource_index}")
                return False
        
        return True


class ResponseParser:
    """Parses AI responses into structured data"""
    
    @staticmethod
    def extract_json_from_response(response: str) -> Optional[Dict[str, Any]]:
        """Extract JSON object from AI response text"""
        try:
            # First try to parse the entire response as JSON
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON within the response text
        json_patterns = [
            r'\{.*\}',  # Match anything between curly braces
            r'```json\s*(\{.*?\})\s*```',  # Match JSON in code blocks
            r'```\s*(\{.*?\})\s*```',  # Match JSON in generic code blocks
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        
        logger.warning("Could not extract valid JSON from response")
        return None
    
    @staticmethod
    def parse_skill_assessment_response(response: str) -> Optional[Dict[str, Any]]:
        """Parse skill assessment response into structured data"""
        json_data = ResponseParser.extract_json_from_response(response)
        
        if not json_data:
            return None
        
        # Validate the parsed data
        if not ResponseValidator.validate_skill_assessment_data(json_data):
            return None
        
        return json_data
    
    @staticmethod
    def parse_learning_path_response(response: str) -> Optional[Dict[str, Any]]:
        """Parse learning path response into structured data"""
        json_data = ResponseParser.extract_json_from_response(response)
        
        if not json_data:
            return None
        
        # Validate the parsed data
        if not ResponseValidator.validate_learning_path_data(json_data):
            return None
        
        return json_data
    
    @staticmethod
    def clean_and_normalize_text(text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
        text = re.sub(r'`(.*?)`', r'\1', text)        # Code
        
        return text


class StructuredResponseHandler:
    """Handles structured responses from AI for different use cases"""
    
    def __init__(self):
        self.parser = ResponseParser()
        self.validator = ResponseValidator()
    
    def process_skill_assessment_response(self, response: str, user_id: str = "unknown") -> SkillAssessment:
        """Process AI response into SkillAssessment object"""
        try:
            # Parse the response
            parsed_data = self.parser.parse_skill_assessment_response(response)
            
            if not parsed_data:
                logger.error("Failed to parse skill assessment response")
                return self._create_fallback_skill_assessment(user_id)
            
            # Create SkillAssessment object
            assessment = SkillAssessment(
                user_id=user_id,
                skill_area=parsed_data["skill_area"],
                overall_level=DifficultyLevel(parsed_data["overall_level"]),
                confidence_score=float(parsed_data["confidence_score"]),
                strengths=parsed_data["strengths"],
                weaknesses=parsed_data["weaknesses"],
                recommendations=parsed_data["recommendations"],
                detailed_scores=parsed_data.get("detailed_scores", {})
            )
            
            logger.info(f"Successfully processed skill assessment for {assessment.skill_area}")
            return assessment
            
        except Exception as e:
            logger.error(f"Error processing skill assessment response: {e}")
            return self._create_fallback_skill_assessment(user_id)
    
    def process_learning_path_response(self, response: str, goal: str) -> LearningPath:
        """Process AI response into LearningPath object"""
        try:
            # Parse the response
            parsed_data = self.parser.parse_learning_path_response(response)
            
            if not parsed_data:
                logger.error("Failed to parse learning path response")
                return self._create_fallback_learning_path(goal)
            
            # Create milestones
            milestones = []
            for i, milestone_data in enumerate(parsed_data["milestones"]):
                milestone = self._create_milestone_from_data(milestone_data, i)
                milestones.append(milestone)
            
            # Create learning path
            learning_path = LearningPath(
                title=parsed_data["title"],
                description=parsed_data["description"],
                goal=goal,
                milestones=milestones,
                difficulty_level=DifficultyLevel(parsed_data.get("difficulty_level", "beginner")),
                prerequisites=parsed_data.get("prerequisites", []),
                target_skills=parsed_data.get("target_skills", [])
            )
            
            logger.info(f"Successfully processed learning path: {learning_path.title}")
            return learning_path
            
        except Exception as e:
            logger.error(f"Error processing learning path response: {e}")
            return self._create_fallback_learning_path(goal)
    
    def process_conversation_response(self, response: str, context: Optional[UserContext] = None) -> str:
        """Process general conversation response"""
        try:
            # Clean and normalize the response
            cleaned_response = self.parser.clean_and_normalize_text(response)
            
            # Validate response length
            if len(cleaned_response) < 10:
                logger.warning("Response too short, using fallback")
                return self._create_fallback_conversation_response()
            
            if len(cleaned_response) > 2000:
                logger.warning("Response too long, truncating")
                cleaned_response = cleaned_response[:1997] + "..."
            
            # Add context-aware enhancements if needed
            if context and context.user_id:
                # Could add personalization here
                pass
            
            return cleaned_response
            
        except Exception as e:
            logger.error(f"Error processing conversation response: {e}")
            return self._create_fallback_conversation_response()
    
    def parse_assessment_questions(self, response: str) -> List[str]:
        """Parse assessment questions from AI response"""
        try:
            # Clean the response
            cleaned_response = response.strip()
            
            # Split by lines and filter for questions
            lines = [line.strip() for line in cleaned_response.split('\n') if line.strip()]
            questions = []
            
            for line in lines:
                # Skip empty lines and non-question lines
                if not line or not line.endswith('?'):
                    continue
                
                # Remove numbering and formatting
                question = re.sub(r'^\d+[\.\)]\s*', '', line)  # Remove "1. " or "1) "
                question = re.sub(r'^[-\*]\s*', '', question)  # Remove "- " or "* "
                question = question.strip()
                
                if question and len(question) > 10:  # Minimum meaningful length
                    questions.append(question)
            
            # Limit to 3 questions as requested
            return questions[:3]
            
        except Exception as e:
            logger.error(f"Error parsing assessment questions: {e}")
            return [
                "Can you tell me more about your experience with this skill?",
                "What challenges have you faced when working in this area?",
                "How would you rate your confidence level from 1 to 10?"
            ]
    
    def _create_milestone_from_data(self, data: Dict[str, Any], order_index: int) -> Milestone:
        """Create Milestone object from parsed data"""
        # Convert duration
        duration_days = data.get("estimated_duration_days", 7)
        estimated_duration = timedelta(days=duration_days)
        
        # Create milestone
        milestone = Milestone(
            title=data["title"],
            description=data["description"],
            skills_to_learn=data.get("skills_to_learn", []),
            prerequisites=data.get("prerequisites", []),
            estimated_duration=estimated_duration,
            difficulty_level=DifficultyLevel(data.get("difficulty_level", "beginner")),
            assessment_criteria=data.get("assessment_criteria", []),
            order_index=order_index
        )
        
        # Add resources
        for resource_data in data.get("resources", []):
            duration_hours = resource_data.get("duration_hours", 1)
            resource_duration = timedelta(hours=duration_hours)
            
            milestone.add_resource(
                title=resource_data["title"],
                url=resource_data.get("url", ""),
                resource_type=resource_data["type"],
                is_free=resource_data.get("is_free", True),
                duration=resource_duration
            )
        
        return milestone
    
    def _create_fallback_skill_assessment(self, user_id: str) -> SkillAssessment:
        """Create fallback skill assessment when parsing fails"""
        return SkillAssessment(
            user_id=user_id,
            skill_area="General",
            overall_level=DifficultyLevel.BEGINNER,
            confidence_score=0.5,
            strengths=["Willingness to learn", "Motivation to improve"],
            weaknesses=["Assessment could not be completed properly"],
            recommendations=[
                "Try the assessment again with more detailed responses",
                "Start with beginner-friendly resources",
                "Focus on building foundational knowledge"
            ]
        )
    
    def _create_fallback_learning_path(self, goal: str) -> LearningPath:
        """Create fallback learning path when parsing fails"""
        milestone = Milestone(
            title="Get Started",
            description=f"Begin your journey toward: {goal}",
            skills_to_learn=["foundational knowledge"],
            estimated_duration=timedelta(weeks=2),
            difficulty_level=DifficultyLevel.BEGINNER,
            assessment_criteria=["Complete initial research", "Identify specific learning resources"]
        )
        
        milestone.add_resource(
            title="Research Your Goal",
            url=f"https://www.google.com/search?q={goal.replace(' ', '+')}",
            resource_type="article",
            is_free=True,
            duration=timedelta(hours=2)
        )
        
        return LearningPath(
            title=f"Basic Path: {goal}",
            description=f"A simple starting point for: {goal}",
            goal=goal,
            milestones=[milestone],
            difficulty_level=DifficultyLevel.BEGINNER,
            target_skills=["basic understanding"]
        )
    
    def _create_fallback_conversation_response(self) -> str:
        """Create fallback conversation response when processing fails"""
        return ("I'm here to help with your career and learning goals! "
                "Could you please rephrase your question or provide more details "
                "so I can give you the best possible guidance?")


class ResponseEnhancer:
    """Enhances AI responses with additional context and formatting"""
    
    @staticmethod
    def enhance_skill_assessment(assessment: SkillAssessment, context: Optional[UserContext] = None) -> SkillAssessment:
        """Enhance skill assessment with additional context"""
        # Add context-specific recommendations
        if context and context.learning_preferences:
            prefs = context.learning_preferences
            
            # Add learning style specific recommendations
            if prefs.learning_style.value == "visual":
                assessment.recommendations.append("Look for video tutorials and visual diagrams")
            elif prefs.learning_style.value == "kinesthetic":
                assessment.recommendations.append("Focus on hands-on projects and practical exercises")
            
            # Add budget-specific recommendations
            if prefs.budget_preference == "free":
                assessment.recommendations.append("Prioritize free resources like YouTube and open courseware")
        
        return assessment
    
    @staticmethod
    def enhance_learning_path(path: LearningPath, context: Optional[UserContext] = None) -> LearningPath:
        """Enhance learning path with user-specific optimizations"""
        if not context:
            return path
        
        # Adjust milestones based on user preferences
        if context.learning_preferences:
            prefs = context.learning_preferences
            
            # Filter resources by budget preference
            if prefs.budget_preference == "free":
                for milestone in path.milestones:
                    milestone.resources = [r for r in milestone.resources if r.get("is_free", True)]
        
        return path
    
    @staticmethod
    def add_motivational_elements(response: str, context: Optional[UserContext] = None) -> str:
        """Add motivational elements to responses"""
        motivational_phrases = [
            "You're on the right track!",
            "Great question!",
            "I'm excited to help you with this!",
            "This is a fantastic goal!",
            "You've got this!"
        ]
        
        # Add appropriate motivational phrase based on context
        if context and context.career_goals:
            response = f"Great question! {response}"
        
        return response


# Convenience functions for easy access
def process_skill_assessment_response(response: str, user_id: str = "unknown") -> SkillAssessment:
    """Convenience function to process skill assessment response"""
    handler = StructuredResponseHandler()
    return handler.process_skill_assessment_response(response, user_id)


def process_learning_path_response(response: str, goal: str) -> LearningPath:
    """Convenience function to process learning path response"""
    handler = StructuredResponseHandler()
    return handler.process_learning_path_response(response, goal)


def process_conversation_response(response: str, context: Optional[UserContext] = None) -> str:
    """Convenience function to process conversation response"""
    handler = StructuredResponseHandler()
    return handler.process_conversation_response(response, context)