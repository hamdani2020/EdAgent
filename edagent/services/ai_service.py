"""
Gemini AI service implementation for EdAgent
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential, 
    retry_if_exception_type,
    before_sleep_log
)

from ..interfaces.ai_interface import AIServiceInterface
from ..models.user_context import UserContext, SkillLevel, SkillLevelEnum
from ..models.learning import SkillAssessment, LearningPath, Milestone, DifficultyLevel
from ..config.settings import get_settings
from .prompt_engineering import PromptBuilder
from .response_processing import StructuredResponseHandler


logger = logging.getLogger(__name__)


class GeminiAPIError(Exception):
    """Custom exception for Gemini API errors"""
    pass


class RateLimitError(GeminiAPIError):
    """Exception for rate limit errors"""
    pass


class QuotaExceededError(GeminiAPIError):
    """Exception for quota exceeded errors"""
    pass


class GeminiAIService(AIServiceInterface):
    """Gemini AI service implementation with rate limiting and retry logic"""
    
    def __init__(self):
        """Initialize the Gemini AI service"""
        self.settings = get_settings()
        self.prompt_builder = PromptBuilder()
        self.response_handler = StructuredResponseHandler()
        self._configure_gemini()
        self._request_count = 0
        self._last_request_time = datetime.now()
        self._rate_limit_window = timedelta(minutes=1)
        
    def _configure_gemini(self) -> None:
        """Configure the Gemini API client"""
        try:
            genai.configure(api_key=self.settings.gemini_api_key)
            logger.info("Gemini API client configured successfully")
        except Exception as e:
            logger.error(f"Failed to configure Gemini API: {e}")
            raise GeminiAPIError(f"Failed to configure Gemini API: {e}")
    
    def _get_model(self, model_type: str = "chat") -> genai.GenerativeModel:
        """Get the appropriate Gemini model"""
        if model_type == "reasoning":
            model_name = self.settings.gemini_model_reasoning
        else:
            model_name = self.settings.gemini_model_chat
        
        # Configure safety settings to be less restrictive for educational content
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        return genai.GenerativeModel(
            model_name=model_name,
            safety_settings=safety_settings
        )
    
    def _get_generation_config(self, model_type: str = "chat") -> Dict[str, Any]:
        """Get generation configuration for the model"""
        if model_type == "reasoning":
            return {
                "temperature": self.settings.gemini_temperature_reasoning,
                "max_output_tokens": self.settings.gemini_max_tokens_learning_path,
                "top_p": 0.8,
                "top_k": 40
            }
        else:
            return {
                "temperature": self.settings.gemini_temperature_chat,
                "max_output_tokens": self.settings.gemini_max_tokens_response,
                "top_p": 0.9,
                "top_k": 40
            }
    
    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting"""
        current_time = datetime.now()
        
        # Reset counter if window has passed
        if current_time - self._last_request_time > self._rate_limit_window:
            self._request_count = 0
            self._last_request_time = current_time
        
        # Check if we've exceeded the rate limit
        if self._request_count >= self.settings.rate_limit_requests_per_minute:
            wait_time = self._rate_limit_window - (current_time - self._last_request_time)
            if wait_time.total_seconds() > 0:
                logger.warning(f"Rate limit exceeded, waiting {wait_time.total_seconds():.2f} seconds")
                await asyncio.sleep(wait_time.total_seconds())
                self._request_count = 0
                self._last_request_time = datetime.now()
        
        self._request_count += 1
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((RateLimitError, ConnectionError, TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def _make_api_call(self, model: genai.GenerativeModel, prompt: str, 
                           generation_config: Dict[str, Any]) -> str:
        """Make an API call to Gemini with retry logic"""
        await self._check_rate_limit()
        
        try:
            # Use asyncio to run the synchronous API call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
            )
            
            if not response.text:
                raise GeminiAPIError("Empty response from Gemini API")
            
            logger.debug(f"Gemini API call successful, response length: {len(response.text)}")
            return response.text.strip()
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # Handle specific error types
            if "quota" in error_msg or "limit" in error_msg:
                if "rate" in error_msg:
                    raise RateLimitError(f"Rate limit exceeded: {e}")
                else:
                    raise QuotaExceededError(f"Quota exceeded: {e}")
            elif "connection" in error_msg or "network" in error_msg:
                raise ConnectionError(f"Network error: {e}")
            elif "timeout" in error_msg:
                raise TimeoutError(f"Request timeout: {e}")
            else:
                raise GeminiAPIError(f"Gemini API error: {e}")
    
    def build_system_prompt(self, user_context: UserContext) -> str:
        """Build context-aware system prompt for EdAgent"""
        return self.prompt_builder._build_base_system_prompt(user_context)
    
    async def generate_response(self, prompt: str, context: UserContext) -> str:
        """Generate a conversational response using Gemini"""
        try:
            model = self._get_model("chat")
            generation_config = self._get_generation_config("chat")
            
            # Build the full prompt using prompt engineering system
            full_prompt = self.prompt_builder.build_conversation_prompt(prompt, context)
            
            response = await self._make_api_call(model, full_prompt, generation_config)
            
            # Process the response for better formatting and validation
            processed_response = self.response_handler.process_conversation_response(response, context)
            
            logger.info(f"Generated response for user {context.user_id if context else 'unknown'}")
            return processed_response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Provide fallback response
            return ("I'm having trouble connecting right now, but I'm here to help with your career "
                   "and learning goals. Could you please try asking your question again?")
    
    async def assess_skills(self, responses: List[str]) -> SkillAssessment:
        """Assess user skills based on their responses"""
        try:
            model = self._get_model("reasoning")
            generation_config = self._get_generation_config("reasoning")
            
            # Create assessment prompt using prompt engineering system
            # Infer skill area from responses or use "General" as default
            skill_area = self._infer_skill_area(responses)
            assessment_prompt = self.prompt_builder.build_skill_assessment_prompt(skill_area, responses)
            
            response = await self._make_api_call(model, assessment_prompt, generation_config)
            
            # Process the response using the structured response handler
            assessment = self.response_handler.process_skill_assessment_response(response, "unknown")
            
            logger.info(f"Skill assessment completed for {assessment.skill_area}")
            return assessment
                
        except Exception as e:
            logger.error(f"Error in skill assessment: {e}")
            # Return fallback assessment using response handler
            return self.response_handler._create_fallback_skill_assessment("unknown")
    
    async def create_learning_path(self, goal: str, current_skills: Dict[str, SkillLevel]) -> LearningPath:
        """Create a personalized learning path"""
        try:
            model = self._get_model("reasoning")
            generation_config = self._get_generation_config("reasoning")
            
            # Prepare current skills summary
            skills_summary = []
            for skill_name, skill_level in current_skills.items():
                skills_summary.append(f"{skill_name}: {skill_level.level.value} (confidence: {skill_level.confidence_score:.1f})")
            
            skills_text = "\n".join(skills_summary) if skills_summary else "No specific skills assessed yet"
            
            # Create learning path prompt using prompt engineering system
            learning_path_prompt = self.prompt_builder.build_learning_path_prompt(goal, current_skills)
            
            response = await self._make_api_call(model, learning_path_prompt, generation_config)
            
            # Process the response using the structured response handler
            learning_path = self.response_handler.process_learning_path_response(response, goal)
            
            logger.info(f"Learning path created: {learning_path.title} with {len(learning_path.milestones)} milestones")
            return learning_path
                
        except Exception as e:
            logger.error(f"Error creating learning path: {e}")
            return self.response_handler._create_fallback_learning_path(goal)
    

    
    def _infer_skill_area(self, responses: List[str]) -> str:
        """Infer the skill area being assessed from user responses"""
        combined_text = " ".join(responses).lower()
        
        # Common skill area keywords
        skill_keywords = {
            "programming": ["code", "coding", "program", "python", "javascript", "java", "c++", "software", "development"],
            "web_development": ["website", "web", "html", "css", "frontend", "backend", "react", "angular", "vue"],
            "data_science": ["data", "analysis", "statistics", "machine learning", "pandas", "numpy", "sql", "database"],
            "design": ["design", "ui", "ux", "figma", "photoshop", "graphic", "visual", "layout"],
            "marketing": ["marketing", "social media", "seo", "advertising", "campaign", "brand"],
            "business": ["business", "management", "strategy", "finance", "accounting", "operations"]
        }
        
        # Count keyword matches
        skill_scores = {}
        for skill_area, keywords in skill_keywords.items():
            score = sum(1 for keyword in keywords if keyword in combined_text)
            if score > 0:
                skill_scores[skill_area] = score
        
        # Return the skill area with the highest score, or "General" if no matches
        if skill_scores:
            return max(skill_scores, key=skill_scores.get).replace("_", " ").title()
        else:
            return "General"