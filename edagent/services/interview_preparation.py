"""
Interview preparation service for EdAgent
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from ..interfaces.ai_interface import AIServiceInterface
from ..models.user_context import UserContext, SkillLevel
from ..models.interview import (
    InterviewQuestion, InterviewSession, InterviewFeedback, IndustryGuidance,
    InterviewType, DifficultyLevel, FeedbackType
)
from ..services.ai_service import GeminiAIService
from ..config.settings import get_settings


logger = logging.getLogger(__name__)


class InterviewPreparationService:
    """Service for managing interview preparation and practice sessions"""
    
    def __init__(self, ai_service: Optional[AIServiceInterface] = None):
        """Initialize the interview preparation service"""
        self.ai_service = ai_service or GeminiAIService()
        self.settings = get_settings()
        self._industry_guidance_cache = {}
        
    async def create_interview_session(
        self,
        user_id: str,
        target_role: str,
        target_industry: str,
        session_type: InterviewType = InterviewType.GENERAL,
        difficulty_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE,
        num_questions: int = 5
    ) -> InterviewSession:
        """Create a new interview practice session"""
        try:
            session_name = f"{target_role} Interview - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            session = InterviewSession(
                user_id=user_id,
                session_name=session_name,
                target_role=target_role,
                target_industry=target_industry,
                session_type=session_type,
                difficulty_level=difficulty_level
            )
            
            # Generate questions for the session
            questions = await self._generate_interview_questions(
                target_role=target_role,
                target_industry=target_industry,
                session_type=session_type,
                difficulty_level=difficulty_level,
                num_questions=num_questions
            )
            
            for question in questions:
                session.add_question(question)
            
            logger.info(f"Created interview session '{session_name}' with {len(questions)} questions")
            return session
            
        except Exception as e:
            logger.error(f"Error creating interview session: {e}")
            raise
    
    async def _generate_interview_questions(
        self,
        target_role: str,
        target_industry: str,
        session_type: InterviewType,
        difficulty_level: DifficultyLevel,
        num_questions: int
    ) -> List[InterviewQuestion]:
        """Generate interview questions using AI"""
        try:
            # Build prompt for question generation
            prompt = self._build_question_generation_prompt(
                target_role, target_industry, session_type, difficulty_level, num_questions
            )
            
            # Get AI response
            response = await self.ai_service._make_api_call(
                self.ai_service._get_model("reasoning"),
                prompt,
                self.ai_service._get_generation_config("reasoning")
            )
            
            # Parse the response into InterviewQuestion objects
            questions = self._parse_questions_response(response, session_type, difficulty_level, target_industry)
            
            return questions[:num_questions]  # Ensure we don't exceed requested number
            
        except Exception as e:
            logger.error(f"Error generating interview questions: {e}")
            # Return fallback questions
            return self._get_fallback_questions(session_type, difficulty_level, num_questions)
    
    def _build_question_generation_prompt(
        self,
        target_role: str,
        target_industry: str,
        session_type: InterviewType,
        difficulty_level: DifficultyLevel,
        num_questions: int
    ) -> str:
        """Build prompt for generating interview questions"""
        return f"""You are an expert interview coach helping prepare candidates for job interviews.

Generate {num_questions} {session_type.value} interview questions for a {target_role} position in the {target_industry} industry.

Requirements:
- Difficulty level: {difficulty_level.value}
- Question type: {session_type.value}
- Industry: {target_industry}
- Role: {target_role}

For each question, provide:
1. The question text
2. 3-5 key points a good answer should cover
3. A sample answer (2-3 sentences)
4. 1-2 potential follow-up questions

Format your response as JSON with this structure:
{{
  "questions": [
    {{
      "question": "Question text here",
      "key_points": ["Point 1", "Point 2", "Point 3"],
      "sample_answer": "Sample answer here",
      "follow_up_questions": ["Follow-up 1", "Follow-up 2"],
      "tags": ["relevant", "tags"]
    }}
  ]
}}

Focus on questions that are:
- Relevant to the specific role and industry
- Appropriate for the {difficulty_level.value} level
- Commonly asked in {session_type.value} interviews
- Actionable and specific

Generate diverse questions that cover different aspects of the role and assess various competencies."""
    
    def _parse_questions_response(
        self,
        response: str,
        session_type: InterviewType,
        difficulty_level: DifficultyLevel,
        target_industry: str
    ) -> List[InterviewQuestion]:
        """Parse AI response into InterviewQuestion objects"""
        try:
            import json
            
            # Try to extract JSON from the response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[start_idx:end_idx]
            data = json.loads(json_str)
            
            questions = []
            for q_data in data.get("questions", []):
                question = InterviewQuestion(
                    question=q_data.get("question", ""),
                    question_type=session_type,
                    difficulty=difficulty_level,
                    industry=target_industry,
                    sample_answer=q_data.get("sample_answer", ""),
                    key_points=q_data.get("key_points", []),
                    follow_up_questions=q_data.get("follow_up_questions", []),
                    tags=q_data.get("tags", [])
                )
                questions.append(question)
            
            return questions
            
        except Exception as e:
            logger.error(f"Error parsing questions response: {e}")
            return self._get_fallback_questions(session_type, difficulty_level, 3)
    
    def _get_fallback_questions(
        self,
        session_type: InterviewType,
        difficulty_level: DifficultyLevel,
        num_questions: int
    ) -> List[InterviewQuestion]:
        """Get fallback questions when AI generation fails"""
        fallback_questions = {
            InterviewType.BEHAVIORAL: [
                "Tell me about a time when you faced a challenging situation at work and how you handled it.",
                "Describe a situation where you had to work with a difficult team member.",
                "Give me an example of a goal you set and how you achieved it.",
                "Tell me about a time when you had to learn something new quickly.",
                "Describe a situation where you had to make a difficult decision."
            ],
            InterviewType.TECHNICAL: [
                "Explain a technical concept you're familiar with to someone without a technical background.",
                "Describe your approach to debugging a complex problem.",
                "How do you stay updated with the latest technologies in your field?",
                "Walk me through your process for designing a new system or feature.",
                "What are some best practices you follow in your technical work?"
            ],
            InterviewType.GENERAL: [
                "Tell me about yourself and your background.",
                "Why are you interested in this position?",
                "What are your greatest strengths and weaknesses?",
                "Where do you see yourself in 5 years?",
                "Why do you want to work for our company?"
            ]
        }
        
        questions_text = fallback_questions.get(session_type, fallback_questions[InterviewType.GENERAL])
        questions = []
        
        for i, q_text in enumerate(questions_text[:num_questions]):
            question = InterviewQuestion(
                question=q_text,
                question_type=session_type,
                difficulty=difficulty_level,
                key_points=["Provide specific examples", "Show problem-solving skills", "Demonstrate relevant experience"],
                tags=["fallback", session_type.value]
            )
            questions.append(question)
        
        return questions
    
    async def provide_feedback(
        self,
        question: InterviewQuestion,
        user_response: str,
        user_context: Optional[UserContext] = None
    ) -> InterviewFeedback:
        """Provide AI-generated feedback for an interview response"""
        try:
            # Build feedback prompt
            prompt = self._build_feedback_prompt(question, user_response, user_context)
            
            # Get AI response
            response = await self.ai_service._make_api_call(
                self.ai_service._get_model("reasoning"),
                prompt,
                self.ai_service._get_generation_config("reasoning")
            )
            
            # Parse feedback response
            feedback = self._parse_feedback_response(response, question.id, user_response)
            
            logger.info(f"Generated feedback for question {question.id}")
            return feedback
            
        except Exception as e:
            logger.error(f"Error generating feedback: {e}")
            return self._get_fallback_feedback(question.id, user_response)
    
    def _build_feedback_prompt(
        self,
        question: InterviewQuestion,
        user_response: str,
        user_context: Optional[UserContext] = None
    ) -> str:
        """Build prompt for generating interview feedback"""
        context_info = ""
        if user_context:
            skills = ", ".join([f"{name} ({skill.level.value})" for name, skill in user_context.current_skills.items()])
            context_info = f"\nCandidate background: {skills}" if skills else ""
        
        return f"""You are an expert interview coach providing constructive feedback on interview responses.

Interview Question: {question.question}
Question Type: {question.question_type.value}
Difficulty: {question.difficulty.value}
Key Points to Cover: {', '.join(question.key_points)}

Candidate's Response: {user_response}{context_info}

Provide detailed feedback in JSON format:
{{
  "score": 7.5,
  "feedback_text": "Overall assessment of the response",
  "strengths": ["Strength 1", "Strength 2"],
  "improvements": ["Improvement 1", "Improvement 2"],
  "suggestions": ["Suggestion 1", "Suggestion 2"],
  "feedback_type": "improvement"
}}

Scoring Guidelines:
- 9-10: Excellent response covering all key points with specific examples
- 7-8: Good response with most key points and some examples
- 5-6: Average response missing some key points or examples
- 3-4: Below average response with significant gaps
- 1-2: Poor response missing most key points

Feedback should be:
- Constructive and encouraging
- Specific and actionable
- Focused on interview best practices
- Tailored to the question type and difficulty level

Consider:
- Structure and clarity of the response
- Use of specific examples and evidence
- Relevance to the question asked
- Professional communication style
- Completeness of the answer"""
    
    def _parse_feedback_response(
        self,
        response: str,
        question_id: str,
        user_response: str
    ) -> InterviewFeedback:
        """Parse AI feedback response into InterviewFeedback object"""
        try:
            import json
            
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[start_idx:end_idx]
            data = json.loads(json_str)
            
            feedback = InterviewFeedback(
                question_id=question_id,
                user_response=user_response,
                feedback_text=data.get("feedback_text", ""),
                score=float(data.get("score", 5.0)),
                strengths=data.get("strengths", []),
                improvements=data.get("improvements", []),
                suggestions=data.get("suggestions", []),
                feedback_type=FeedbackType(data.get("feedback_type", "improvement"))
            )
            
            return feedback
            
        except Exception as e:
            logger.error(f"Error parsing feedback response: {e}")
            return self._get_fallback_feedback(question_id, user_response)
    
    def _get_fallback_feedback(self, question_id: str, user_response: str) -> InterviewFeedback:
        """Get fallback feedback when AI generation fails"""
        return InterviewFeedback(
            question_id=question_id,
            user_response=user_response,
            feedback_text="Thank you for your response. Consider providing more specific examples and details to strengthen your answer.",
            score=6.0,
            strengths=["Attempted to answer the question"],
            improvements=["Add more specific examples", "Provide more detail", "Structure your response clearly"],
            suggestions=["Use the STAR method (Situation, Task, Action, Result)", "Practice articulating your thoughts clearly"],
            feedback_type=FeedbackType.IMPROVEMENT
        )
    
    async def get_industry_guidance(self, industry: str) -> IndustryGuidance:
        """Get industry-specific interview guidance"""
        try:
            # Check cache first
            if industry in self._industry_guidance_cache:
                return self._industry_guidance_cache[industry]
            
            # Generate guidance using AI
            prompt = self._build_industry_guidance_prompt(industry)
            
            response = await self.ai_service._make_api_call(
                self.ai_service._get_model("reasoning"),
                prompt,
                self.ai_service._get_generation_config("reasoning")
            )
            
            guidance = self._parse_industry_guidance_response(response, industry)
            
            # Cache the result
            self._industry_guidance_cache[industry] = guidance
            
            logger.info(f"Generated industry guidance for {industry}")
            return guidance
            
        except Exception as e:
            logger.error(f"Error generating industry guidance: {e}")
            return self._get_fallback_industry_guidance(industry)
    
    def _build_industry_guidance_prompt(self, industry: str) -> str:
        """Build prompt for generating industry-specific guidance"""
        return f"""You are an expert career coach providing industry-specific interview guidance.

Generate comprehensive interview guidance for the {industry} industry.

Provide guidance in JSON format:
{{
  "common_questions": ["Question 1", "Question 2", "Question 3"],
  "key_skills": ["Skill 1", "Skill 2", "Skill 3"],
  "interview_format": "Description of typical interview process",
  "preparation_tips": ["Tip 1", "Tip 2", "Tip 3"],
  "red_flags": ["Red flag 1", "Red flag 2"],
  "success_factors": ["Factor 1", "Factor 2", "Factor 3"]
}}

Focus on:
- Industry-specific questions commonly asked
- Technical and soft skills valued in this industry
- Typical interview formats and processes
- Specific preparation strategies
- Common mistakes to avoid
- Key factors that lead to success

Make the guidance practical, specific, and actionable for someone preparing for interviews in the {industry} industry."""
    
    def _parse_industry_guidance_response(self, response: str, industry: str) -> IndustryGuidance:
        """Parse AI response into IndustryGuidance object"""
        try:
            import json
            
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[start_idx:end_idx]
            data = json.loads(json_str)
            
            guidance = IndustryGuidance(
                industry=industry,
                common_questions=data.get("common_questions", []),
                key_skills=data.get("key_skills", []),
                interview_format=data.get("interview_format", ""),
                preparation_tips=data.get("preparation_tips", []),
                red_flags=data.get("red_flags", []),
                success_factors=data.get("success_factors", [])
            )
            
            return guidance
            
        except Exception as e:
            logger.error(f"Error parsing industry guidance response: {e}")
            return self._get_fallback_industry_guidance(industry)
    
    def _get_fallback_industry_guidance(self, industry: str) -> IndustryGuidance:
        """Get fallback industry guidance when AI generation fails"""
        return IndustryGuidance(
            industry=industry,
            common_questions=[
                "Why are you interested in this industry?",
                "What do you know about our company?",
                "How do you stay updated with industry trends?"
            ],
            key_skills=[
                "Communication skills",
                "Problem-solving abilities",
                "Industry knowledge",
                "Adaptability"
            ],
            interview_format="Typically includes phone screening, technical assessment, and in-person/video interviews",
            preparation_tips=[
                "Research the company and industry thoroughly",
                "Prepare specific examples from your experience",
                "Practice common interview questions",
                "Prepare thoughtful questions to ask the interviewer"
            ],
            red_flags=[
                "Lack of preparation or research",
                "Inability to provide specific examples"
            ],
            success_factors=[
                "Strong preparation and research",
                "Clear communication",
                "Relevant experience and skills",
                "Cultural fit with the organization"
            ]
        )
    
    async def generate_practice_questions(
        self,
        user_context: UserContext,
        target_role: str,
        num_questions: int = 3
    ) -> List[InterviewQuestion]:
        """Generate practice questions based on user context and target role"""
        try:
            # Determine appropriate difficulty based on user skills
            difficulty = self._determine_difficulty_from_context(user_context)
            
            # Infer industry from career goals or use "General"
            industry = self._infer_industry_from_context(user_context)
            
            # Generate mixed question types for practice
            questions = []
            
            # Generate behavioral questions
            behavioral_questions = await self._generate_interview_questions(
                target_role=target_role,
                target_industry=industry,
                session_type=InterviewType.BEHAVIORAL,
                difficulty_level=difficulty,
                num_questions=max(1, num_questions // 2)
            )
            questions.extend(behavioral_questions)
            
            # Generate technical/general questions
            remaining = num_questions - len(questions)
            if remaining > 0:
                tech_questions = await self._generate_interview_questions(
                    target_role=target_role,
                    target_industry=industry,
                    session_type=InterviewType.TECHNICAL if "developer" in target_role.lower() or "engineer" in target_role.lower() else InterviewType.GENERAL,
                    difficulty_level=difficulty,
                    num_questions=remaining
                )
                questions.extend(tech_questions)
            
            return questions[:num_questions]
            
        except Exception as e:
            logger.error(f"Error generating practice questions: {e}")
            return self._get_fallback_questions(InterviewType.GENERAL, DifficultyLevel.INTERMEDIATE, num_questions)
    
    def _determine_difficulty_from_context(self, user_context: UserContext) -> DifficultyLevel:
        """Determine appropriate difficulty level based on user context"""
        if not user_context.current_skills:
            return DifficultyLevel.BEGINNER
        
        # Calculate average skill level
        skill_levels = [skill.level for skill in user_context.current_skills.values()]
        beginner_count = sum(1 for level in skill_levels if level.value == "beginner")
        intermediate_count = sum(1 for level in skill_levels if level.value == "intermediate")
        advanced_count = sum(1 for level in skill_levels if level.value == "advanced")
        
        total_skills = len(skill_levels)
        
        if advanced_count / total_skills >= 0.5:
            return DifficultyLevel.ADVANCED
        elif intermediate_count / total_skills >= 0.3:
            return DifficultyLevel.INTERMEDIATE
        else:
            return DifficultyLevel.BEGINNER
    
    def _infer_industry_from_context(self, user_context: UserContext) -> str:
        """Infer target industry from user context"""
        if user_context.career_goals:
            goals_text = " ".join(user_context.career_goals).lower()
            
            industry_keywords = {
                "technology": ["software", "developer", "programming", "tech", "engineer", "data"],
                "healthcare": ["healthcare", "medical", "nurse", "doctor", "health"],
                "finance": ["finance", "banking", "investment", "accounting", "financial"],
                "education": ["education", "teacher", "instructor", "academic", "training"],
                "marketing": ["marketing", "advertising", "social media", "brand", "digital marketing"],
                "consulting": ["consulting", "consultant", "advisory", "strategy"]
            }
            
            for industry, keywords in industry_keywords.items():
                if any(keyword in goals_text for keyword in keywords):
                    return industry.title()
        
        return "General"