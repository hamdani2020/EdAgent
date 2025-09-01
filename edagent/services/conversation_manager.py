"""
Conversation flow controller for EdAgent
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from ..interfaces.conversation_interface import ConversationManagerInterface
from ..models.conversation import (
    ConversationResponse, AssessmentSession, Message, MessageType, ConversationStatus
)
from ..models.learning import LearningPath
from ..models.user_context import UserContext, SkillLevel, SkillLevelEnum
from .ai_service import GeminiAIService
from .user_context_manager import UserContextManager
from .content_recommender import ContentRecommender
from .prompt_engineering import PromptBuilder
from .response_processing import StructuredResponseHandler
from .learning_path_generator import EnhancedLearningPathGenerator
from .resume_analyzer import ResumeAnalyzer
from .interview_preparation import InterviewPreparationService
from ..models.resume import Resume, ResumeAnalysis
from ..models.interview import InterviewSession, InterviewType, DifficultyLevel, IndustryGuidance

logger = logging.getLogger(__name__)


class ConversationState:
    """Manages conversation state for a user session"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.current_context: Optional[str] = None  # "general", "assessment", "learning_path"
        self.active_assessment: Optional[AssessmentSession] = None
        self.pending_learning_path: Optional[str] = None  # Goal for learning path creation
        self.last_activity: datetime = datetime.now()
        self.message_count: int = 0
    
    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
        self.message_count += 1
    
    def is_in_assessment(self) -> bool:
        """Check if user is currently in an assessment"""
        return (self.active_assessment is not None and 
                self.active_assessment.status == ConversationStatus.ACTIVE)
    
    def is_creating_learning_path(self) -> bool:
        """Check if user is in learning path creation flow"""
        return self.pending_learning_path is not None


class ConversationManager(ConversationManagerInterface):
    """
    Central orchestrator for all user conversations and interactions
    """
    
    def __init__(self):
        """Initialize the conversation manager with required services"""
        self.ai_service = GeminiAIService()
        self.user_context_manager = UserContextManager()
        from ..config import get_settings
        settings = get_settings()
        self.content_recommender = ContentRecommender(settings)
        self.prompt_builder = PromptBuilder()
        self.response_handler = StructuredResponseHandler()
        self.learning_path_generator = EnhancedLearningPathGenerator()
        self.resume_analyzer = ResumeAnalyzer(self.ai_service)
        self.interview_service = InterviewPreparationService(self.ai_service)
        
        # Track conversation states for active users
        self._conversation_states: Dict[str, ConversationState] = {}
        
        # Conversation flow keywords for routing
        self._assessment_keywords = [
            "assess", "assessment", "evaluate", "skill level", "test my", 
            "check my skills", "what can i do", "how good am i"
        ]
        self._learning_path_keywords = [
            "learning path", "roadmap", "plan", "how to learn", "career path",
            "become a", "learn to be", "study plan", "curriculum"
        ]
        self._content_keywords = [
            "recommend", "suggest", "find course", "tutorial", "video",
            "resource", "material", "book", "learn about"
        ]
        self._resume_keywords = [
            "resume", "cv", "curriculum vitae", "review my resume", "resume feedback",
            "resume analysis", "improve my resume", "resume help", "job application"
        ]
        self._interview_keywords = [
            "interview", "interview prep", "interview preparation", "practice interview",
            "interview questions", "interview practice", "mock interview", "job interview",
            "interview tips", "interview coaching", "interview feedback"
        ]
    
    def _get_conversation_state(self, user_id: str) -> ConversationState:
        """Get or create conversation state for user"""
        if user_id not in self._conversation_states:
            self._conversation_states[user_id] = ConversationState(user_id)
        
        state = self._conversation_states[user_id]
        state.update_activity()
        return state
    
    def _detect_intent(self, message: str) -> str:
        """Detect user intent from message content"""
        message_lower = message.lower()
        
        # Check for assessment intent
        if any(keyword in message_lower for keyword in self._assessment_keywords):
            return "assessment"
        
        # Check for learning path intent
        if any(keyword in message_lower for keyword in self._learning_path_keywords):
            return "learning_path"
        
        # Check for content recommendation intent
        if any(keyword in message_lower for keyword in self._content_keywords):
            return "content_recommendation"
        
        # Check for resume analysis intent
        if any(keyword in message_lower for keyword in self._resume_keywords):
            return "resume_analysis"
        
        # Check for interview preparation intent
        if any(keyword in message_lower for keyword in self._interview_keywords):
            return "interview_preparation"
        
        # Default to general conversation
        return "general"
    
    async def handle_message(self, user_id: str, message: str) -> ConversationResponse:
        """
        Handle incoming user message and generate appropriate response
        
        Args:
            user_id: Unique user identifier
            message: User's input message
            
        Returns:
            Structured conversation response
        """
        try:
            # Get conversation state
            conv_state = self._get_conversation_state(user_id)
            
            # Get or create user context
            user_context = await self._get_or_create_user_context(user_id)
            
            # Handle ongoing assessment
            if conv_state.is_in_assessment():
                return await self._handle_assessment_response(user_id, message, conv_state)
            
            # Handle learning path creation flow
            if conv_state.is_creating_learning_path():
                return await self._handle_learning_path_creation(user_id, message, conv_state)
            
            # Detect intent for new conversation
            intent = self._detect_intent(message)
            
            # Route to appropriate handler
            if intent == "assessment":
                return await self._initiate_skill_assessment(user_id, message, user_context)
            elif intent == "learning_path":
                return await self._initiate_learning_path_creation(user_id, message, user_context)
            elif intent == "content_recommendation":
                return await self._handle_content_request(user_id, message, user_context)
            elif intent == "resume_analysis":
                return await self._handle_resume_analysis_request(user_id, message, user_context)
            elif intent == "interview_preparation":
                return await self._handle_interview_preparation_request(user_id, message, user_context)
            else:
                return await self._handle_general_conversation(user_id, message, user_context)
        
        except Exception as e:
            logger.error(f"Error handling message for user {user_id}: {e}")
            return ConversationResponse(
                message="I'm having trouble processing your message right now. Could you please try again?",
                response_type="text",
                confidence_score=0.5
            )
        finally:
            # Save conversation to history
            try:
                if 'user_context' in locals():
                    await self._save_conversation(user_id, message, locals().get('response'))
            except Exception as e:
                logger.error(f"Error saving conversation for user {user_id}: {e}")
    
    async def start_skill_assessment(self, user_id: str) -> AssessmentSession:
        """
        Start a skill assessment session
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            New assessment session
        """
        try:
            # Get conversation state
            conv_state = self._get_conversation_state(user_id)
            
            # Create new assessment session
            assessment = AssessmentSession(
                user_id=user_id,
                skill_area="General",  # Will be refined based on responses
                status=ConversationStatus.ACTIVE
            )
            
            # Add initial assessment questions
            self._add_initial_assessment_questions(assessment)
            
            # Update conversation state
            conv_state.active_assessment = assessment
            conv_state.current_context = "assessment"
            
            logger.info(f"Started skill assessment for user {user_id}")
            return assessment
        
        except Exception as e:
            logger.error(f"Error starting skill assessment for user {user_id}: {e}")
            raise
    
    async def generate_learning_path(self, user_id: str, goal: str) -> LearningPath:
        """
        Generate a comprehensive personalized learning path
        
        Args:
            user_id: Unique user identifier
            goal: User's learning or career goal
            
        Returns:
            Comprehensive personalized learning path
        """
        try:
            # Get user context and skills
            user_context = await self._get_or_create_user_context(user_id)
            current_skills = await self.user_context_manager.get_user_skills(user_id)
            
            # Generate comprehensive learning path using enhanced generator
            learning_path = await self.learning_path_generator.create_comprehensive_learning_path(
                goal=goal,
                current_skills=current_skills,
                user_context=user_context
            )
            
            # Save learning path to database
            await self.user_context_manager.create_learning_path(
                user_id=user_id,
                goal=goal,
                milestones=[milestone.to_dict() for milestone in learning_path.milestones],
                estimated_duration_days=learning_path.estimated_duration.days if learning_path.estimated_duration else None,
                difficulty_level=learning_path.difficulty_level.value
            )
            
            logger.info(f"Generated comprehensive learning path for user {user_id}: {goal}")
            return learning_path
        
        except Exception as e:
            logger.error(f"Error generating learning path for user {user_id}: {e}")
            raise
    
    async def get_conversation_history(self, user_id: str) -> List[Message]:
        """
        Retrieve conversation history for a user
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            List of conversation messages
        """
        try:
            # Get conversation history from user context manager
            history_data = await self.user_context_manager.get_conversation_history(user_id)
            
            # Convert to Message objects
            messages = []
            for msg_data in history_data:
                message = Message(
                    id=msg_data["id"],
                    content=msg_data["content"],
                    message_type=MessageType(msg_data["message_type"]),
                    timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                    metadata=msg_data.get("metadata", {})
                )
                messages.append(message)
            
            logger.info(f"Retrieved {len(messages)} messages for user {user_id}")
            return messages
        
        except Exception as e:
            logger.error(f"Error retrieving conversation history for user {user_id}: {e}")
            return []
    
    async def _get_or_create_user_context(self, user_id: str) -> UserContext:
        """Get existing user context or create new one"""
        user_context = await self.user_context_manager.get_user_context(user_id)
        
        if user_context is None:
            # Create new user context
            user_context = await self.user_context_manager.create_user_context(user_id)
            logger.info(f"Created new user context for {user_id}")
        
        return user_context
    
    async def _handle_general_conversation(
        self, 
        user_id: str, 
        message: str, 
        user_context: UserContext
    ) -> ConversationResponse:
        """Handle general conversation flow"""
        try:
            # Generate AI response
            ai_response = await self.ai_service.generate_response(message, user_context)
            
            # Create conversation response
            response = ConversationResponse(
                message=ai_response,
                response_type="text",
                confidence_score=0.9
            )
            
            # Add contextual follow-up questions based on user context
            if not user_context.current_skills:
                response.add_follow_up_question("Would you like me to assess your current skills?")
            
            if not user_context.career_goals:
                response.add_follow_up_question("What are your career goals? I can help create a learning path.")
            
            return response
        
        except Exception as e:
            logger.error(f"Error in general conversation for user {user_id}: {e}")
            return ConversationResponse(
                message="I'm here to help with your career and learning goals. What would you like to discuss?",
                response_type="text",
                confidence_score=0.5
            )
    
    async def _initiate_skill_assessment(
        self, 
        user_id: str, 
        message: str, 
        user_context: UserContext
    ) -> ConversationResponse:
        """Initiate skill assessment flow"""
        try:
            # Start assessment session
            assessment = await self.start_skill_assessment(user_id)
            
            # Get first question
            if assessment.questions:
                first_question = assessment.questions[0]["question"]
                
                response = ConversationResponse(
                    message=f"Great! I'll help assess your skills. {first_question}",
                    response_type="assessment",
                    confidence_score=0.95,
                    metadata={"assessment_id": assessment.id, "question_index": 0}
                )
                
                return response
            else:
                raise ValueError("No assessment questions generated")
        
        except Exception as e:
            logger.error(f"Error initiating skill assessment for user {user_id}: {e}")
            return ConversationResponse(
                message="I'd love to help assess your skills, but I'm having technical difficulties. Let's try a general conversation instead.",
                response_type="text",
                confidence_score=0.5
            )
    
    async def _handle_assessment_response(
        self, 
        user_id: str, 
        message: str, 
        conv_state: ConversationState
    ) -> ConversationResponse:
        """Handle user response during skill assessment"""
        try:
            assessment = conv_state.active_assessment
            user_context = await self._get_or_create_user_context(user_id)
            
            # Add user response to assessment
            assessment.add_response(message)
            
            # Generate adaptive questions after initial responses (only once)
            if len(assessment.responses) == 3 and len(assessment.questions) == 5:
                try:
                    await self._generate_adaptive_questions(assessment, user_context)
                except Exception as e:
                    logger.error(f"Error generating adaptive questions: {e}")
                    # Continue with original questions if adaptive generation fails
            
            # Check if assessment is complete
            if assessment.is_complete():
                # Process assessment results
                responses = [resp["response"] for resp in assessment.responses]
                skill_assessment = await self.ai_service.assess_skills(responses)
                
                # Update user skills based on assessment
                skills_dict = {}
                # Create a skill level based on the assessment results
                skill_level = SkillLevel(
                    skill_name=skill_assessment.skill_area,
                    level=SkillLevelEnum(skill_assessment.overall_level.value),
                    confidence_score=skill_assessment.confidence_score,
                    last_updated=datetime.now()
                )
                skills_dict[skill_assessment.skill_area] = skill_level
                
                await self.user_context_manager.update_skills(user_id, skills_dict)
                
                # Save assessment results to user context
                await self.user_context_manager.save_assessment_results(user_id, skill_assessment.to_dict())
                
                # Complete assessment
                assessment.complete_assessment(skill_assessment.to_dict())
                conv_state.active_assessment = None
                conv_state.current_context = None
                
                # Create response with results and next steps
                summary = self._create_assessment_summary(skill_assessment)
                next_steps = self._generate_assessment_next_steps(skill_assessment)
                
                response = ConversationResponse(
                    message=f"Assessment complete! Here's what I found:\n\n{summary}\n\n{next_steps}",
                    response_type="assessment",
                    confidence_score=0.9,
                    suggested_actions=[
                        "Create a learning path based on your skills",
                        "Get content recommendations for improvement areas",
                        "Take a more detailed assessment in a specific area"
                    ]
                )
                
                return response
            
            else:
                # Get next question with progress indicator
                progress = assessment.get_progress()
                next_question = assessment.questions[assessment.current_question_index]["question"]
                
                # Add encouraging message based on progress
                encouragement = self._get_assessment_encouragement(progress, assessment.current_question_index)
                
                response = ConversationResponse(
                    message=f"{encouragement} {next_question}",
                    response_type="assessment",
                    confidence_score=0.95,
                    metadata={
                        "assessment_id": assessment.id, 
                        "question_index": assessment.current_question_index,
                        "progress": progress,
                        "total_questions": len(assessment.questions)
                    }
                )
                
                return response
        
        except Exception as e:
            logger.error(f"Error handling assessment response for user {user_id}: {e}")
            # Reset assessment state
            conv_state.active_assessment = None
            conv_state.current_context = None
            
            return ConversationResponse(
                message="I had trouble processing your assessment response. Let's start over or try something else.",
                response_type="text",
                confidence_score=0.5
            )
    
    def _get_assessment_encouragement(self, progress: float, question_index: int) -> str:
        """Get encouraging message based on assessment progress"""
        if question_index == 0:
            return "Great start!"
        elif progress < 0.3:
            return "Thanks for that answer!"
        elif progress < 0.6:
            return "You're doing great!"
        elif progress < 0.9:
            return "Almost there!"
        else:
            return "Last question!"
    
    def _generate_assessment_next_steps(self, skill_assessment) -> str:
        """Generate personalized next steps based on assessment results"""
        next_steps = "**Recommended Next Steps:**\n"
        
        if skill_assessment.overall_level.value == "beginner":
            next_steps += "• Start with foundational courses in your area of interest\n"
            next_steps += "• Focus on hands-on practice with simple projects\n"
        elif skill_assessment.overall_level.value == "intermediate":
            next_steps += "• Build more complex projects to strengthen your skills\n"
            next_steps += "• Consider specializing in specific areas\n"
        else:
            next_steps += "• Take on challenging projects or contribute to open source\n"
            next_steps += "• Consider mentoring others or teaching\n"
        
        if skill_assessment.weaknesses:
            next_steps += f"• Focus on improving: {', '.join(skill_assessment.weaknesses[:2])}\n"
        
        if skill_assessment.recommendations:
            next_steps += f"• {skill_assessment.recommendations[0]}\n"
        
        return next_steps
    
    async def _initiate_learning_path_creation(
        self, 
        user_id: str, 
        message: str, 
        user_context: UserContext
    ) -> ConversationResponse:
        """Initiate learning path creation flow"""
        try:
            # Extract goal from message or ask for clarification
            goal = self._extract_learning_goal(message)
            
            if goal:
                # Generate learning path
                learning_path = await self.generate_learning_path(user_id, goal)
                
                # Format response with learning path
                path_summary = self._format_learning_path_summary(learning_path)
                
                response = ConversationResponse(
                    message=f"I've created a personalized learning path for '{goal}':\n\n{path_summary}",
                    response_type="learning_path",
                    confidence_score=0.9,
                    suggested_actions=[
                        "Get content recommendations for the first milestone",
                        "Adjust the learning path timeline",
                        "Start with prerequisite skills"
                    ]
                )
                
                return response
            
            else:
                # Ask for goal clarification
                conv_state = self._get_conversation_state(user_id)
                conv_state.current_context = "learning_path"
                conv_state.pending_learning_path = "pending"
                
                response = ConversationResponse(
                    message="I'd love to create a learning path for you! What specific career goal or skill would you like to work towards?",
                    response_type="text",
                    confidence_score=0.8,
                    follow_up_questions=[
                        "What career are you interested in?",
                        "What skills do you want to develop?",
                        "Are you looking to change careers or advance in your current field?"
                    ]
                )
                
                return response
        
        except Exception as e:
            logger.error(f"Error initiating learning path creation for user {user_id}: {e}")
            return ConversationResponse(
                message="I'd love to help create a learning path, but I'm having technical difficulties. What specific goal would you like to work towards?",
                response_type="text",
                confidence_score=0.5
            )
    
    async def _handle_learning_path_creation(
        self, 
        user_id: str, 
        message: str, 
        conv_state: ConversationState
    ) -> ConversationResponse:
        """Handle learning path creation flow"""
        try:
            # Extract goal from user's response
            goal = message.strip()
            
            if len(goal) < 5:  # Too short to be a meaningful goal
                return ConversationResponse(
                    message="Could you be more specific about your learning goal? For example, 'become a web developer' or 'learn data analysis'.",
                    response_type="text",
                    confidence_score=0.7
                )
            
            # Generate learning path
            learning_path = await self.generate_learning_path(user_id, goal)
            
            # Clear pending state
            conv_state.pending_learning_path = None
            conv_state.current_context = None
            
            # Format response
            path_summary = self._format_learning_path_summary(learning_path)
            
            response = ConversationResponse(
                message=f"Perfect! I've created a learning path for '{goal}':\n\n{path_summary}",
                response_type="learning_path",
                confidence_score=0.9,
                suggested_actions=[
                    "Get content recommendations for the first milestone",
                    "Start with prerequisite skills if needed"
                ]
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error handling learning path creation for user {user_id}: {e}")
            # Reset state
            conv_state.pending_learning_path = None
            conv_state.current_context = None
            
            return ConversationResponse(
                message="I had trouble creating your learning path. Let's try again - what would you like to learn?",
                response_type="text",
                confidence_score=0.5
            )
    
    async def _handle_content_request(
        self, 
        user_id: str, 
        message: str, 
        user_context: UserContext
    ) -> ConversationResponse:
        """Handle content recommendation requests"""
        try:
            # Extract topic from message
            topic = self._extract_content_topic(message)
            
            if not topic:
                return ConversationResponse(
                    message="What specific topic or skill would you like me to find resources for?",
                    response_type="text",
                    confidence_score=0.7
                )
            
            # Get content recommendations
            recommendations = await self.content_recommender.get_recommendations(
                topic=topic,
                user_context=user_context,
                limit=5
            )
            
            # Format recommendations
            if recommendations:
                rec_text = self._format_content_recommendations(recommendations)
                
                response = ConversationResponse(
                    message=f"Here are some great resources for {topic}:\n\n{rec_text}",
                    response_type="content_recommendation",
                    confidence_score=0.9,
                    content_recommendations=[rec.to_dict() for rec in recommendations]
                )
            else:
                response = ConversationResponse(
                    message=f"I couldn't find specific resources for '{topic}' right now. Could you try a different topic or be more specific?",
                    response_type="text",
                    confidence_score=0.6
                )
            
            return response
        
        except Exception as e:
            logger.error(f"Error handling content request for user {user_id}: {e}")
            return ConversationResponse(
                message="I'm having trouble finding content recommendations right now. What specific topic are you interested in?",
                response_type="text",
                confidence_score=0.5
            )
    
    def _add_initial_assessment_questions(self, assessment: AssessmentSession) -> None:
        """Add initial assessment questions"""
        questions = [
            "What's your current experience level with technology and computers?",
            "Have you done any programming or coding before? If so, what languages or tools?",
            "What type of career or role are you most interested in pursuing?",
            "How much time can you dedicate to learning each week?",
            "What's your preferred way of learning - videos, reading, hands-on practice, or a mix?"
        ]
        
        for question in questions:
            assessment.add_question(question, question_type="open")
    
    async def _generate_adaptive_questions(self, assessment: AssessmentSession, user_context: UserContext) -> None:
        """Generate adaptive follow-up questions based on previous responses"""
        try:
            if len(assessment.responses) < 2:
                return  # Need at least 2 responses to adapt
            
            # Analyze responses to determine skill area focus
            responses_text = [resp["response"] for resp in assessment.responses]
            skill_area = self.ai_service._infer_skill_area(responses_text)
            
            # Update assessment skill area if it's more specific than "General"
            if skill_area != "General" and assessment.skill_area == "General":
                assessment.skill_area = skill_area
            
            # Generate skill-specific questions using AI service
            try:
                adaptive_questions = await self._get_skill_specific_questions(skill_area, responses_text)
            except Exception as e:
                logger.error(f"Error getting adaptive questions: {e}")
                adaptive_questions = self._get_fallback_questions_for_skill(skill_area)
            
            # Add adaptive questions to assessment (limit to 2 to keep assessment manageable)
            for question in adaptive_questions[:2]:
                assessment.add_question(question, question_type="adaptive")
                
            logger.info(f"Added {len(adaptive_questions[:2])} adaptive questions for {skill_area}")
            
        except Exception as e:
            logger.error(f"Error generating adaptive questions: {e}")
            # Add fallback questions if adaptive generation fails
            self._add_fallback_questions(assessment)
    
    async def _get_skill_specific_questions(self, skill_area: str, previous_responses: List[str]) -> List[str]:
        """Get skill-specific assessment questions from AI service"""
        try:
            # Use AI service to generate targeted questions
            prompt = self.prompt_builder.build_adaptive_assessment_prompt(skill_area, previous_responses)
            model = self.ai_service._get_model("reasoning")
            generation_config = self.ai_service._get_generation_config("reasoning")
            
            response = await self.ai_service._make_api_call(model, prompt, generation_config)
            
            # Parse questions from response
            questions = self.response_handler.parse_assessment_questions(response)
            
            return questions[:3]  # Limit to 3 additional questions
            
        except Exception as e:
            logger.error(f"Error getting skill-specific questions: {e}")
            return self._get_fallback_questions_for_skill(skill_area)
    
    def _add_fallback_questions(self, assessment: AssessmentSession) -> None:
        """Add fallback questions if adaptive generation fails"""
        fallback_questions = [
            "Can you describe a project or task you've worked on recently?",
            "What would you say is your biggest learning challenge right now?"
        ]
        
        for question in fallback_questions:
            assessment.add_question(question, question_type="fallback")
    
    def _get_fallback_questions_for_skill(self, skill_area: str) -> List[str]:
        """Get fallback questions specific to a skill area"""
        skill_questions = {
            "Programming": [
                "What programming languages have you used, if any?",
                "Have you built any applications or websites?",
                "How comfortable are you with debugging code?"
            ],
            "Web Development": [
                "Have you created any websites before?",
                "Are you familiar with HTML, CSS, or JavaScript?",
                "What web development tools have you used?"
            ],
            "Data Science": [
                "Have you worked with data analysis before?",
                "Are you familiar with Excel, SQL, or Python for data?",
                "What types of data problems interest you?"
            ],
            "Design": [
                "Have you created any visual designs or graphics?",
                "What design tools have you used?",
                "How do you approach solving design problems?"
            ]
        }
        
        return skill_questions.get(skill_area, [
            "What specific skills in this area interest you most?",
            "Have you had any formal or informal training in this field?",
            "What would success look like for you in this area?"
        ])
    
    def _extract_learning_goal(self, message: str) -> Optional[str]:
        """Extract learning goal from user message"""
        message_lower = message.lower()
        
        # Skip questions entirely
        if message.strip().endswith("?") or message_lower.startswith("how"):
            return None
        
        # Look for goal patterns
        goal_patterns = [
            "become a", "become an", "learn to be", "want to be",
            "career in", "work as", "job as", "learn", "study"
        ]
        
        for pattern in goal_patterns:
            if pattern in message_lower:
                # Extract text after the pattern
                start_idx = message_lower.find(pattern) + len(pattern)
                goal = message[start_idx:].strip()
                
                # Clean up the goal - be more careful with article removal
                if goal.startswith("a ") and len(goal) > 2:
                    goal = goal[2:].strip()
                elif goal.startswith("an ") and len(goal) > 3:
                    goal = goal[3:].strip()
                
                if len(goal) > 3:  # Minimum meaningful length
                    return goal
        
        # If no pattern found, check if the whole message could be a goal
        if len(message.strip()) > 5:
            return message.strip()
        
        return None
    
    def _extract_content_topic(self, message: str) -> Optional[str]:
        """Extract content topic from user message"""
        message_lower = message.lower()
        
        # Remove common request words
        remove_words = [
            "recommend", "suggest", "find", "show me", "help me find",
            "course", "tutorial", "video", "resource", "material", "about"
        ]
        
        topic = message_lower
        for word in remove_words:
            topic = topic.replace(word, "")
        
        topic = topic.strip()
        
        # Clean up common phrases
        if topic.startswith("for "):
            topic = topic[4:]
        if topic.startswith("on "):
            topic = topic[3:]
        
        return topic.strip() if len(topic.strip()) > 2 else None
    
    def _format_learning_path_summary(self, learning_path: LearningPath) -> str:
        """Format learning path for display"""
        summary = f"**{learning_path.title}**\n"
        summary += f"Difficulty: {learning_path.difficulty_level.value}\n"
        
        if learning_path.estimated_duration:
            days = learning_path.estimated_duration.days
            if days > 0:
                summary += f"Estimated Duration: {days} days\n"
        
        summary += "\n**Milestones:**\n"
        
        for i, milestone in enumerate(learning_path.milestones[:5], 1):  # Show first 5
            summary += f"{i}. {milestone.title}\n"
            if milestone.description:
                summary += f"   {milestone.description[:100]}...\n"
        
        if len(learning_path.milestones) > 5:
            summary += f"... and {len(learning_path.milestones) - 5} more milestones\n"
        
        return summary
    
    def _format_content_recommendations(self, recommendations: List[Any]) -> str:
        """Format content recommendations for display"""
        formatted = ""
        
        for i, rec in enumerate(recommendations, 1):
            formatted += f"{i}. **{rec.title}**\n"
            formatted += f"   Platform: {rec.platform}\n"
            formatted += f"   Type: {rec.content_type}\n"
            
            if hasattr(rec, 'is_free') and rec.is_free:
                formatted += "   💰 Free\n"
            
            if hasattr(rec, 'rating') and rec.rating:
                formatted += f"   ⭐ Rating: {rec.rating:.1f}\n"
            
            formatted += f"   🔗 {rec.url}\n\n"
        
        return formatted
    
    def _create_assessment_summary(self, assessment: Any) -> str:
        """Create a summary of the skill assessment results"""
        summary = f"**Skill Area:** {assessment.skill_area}\n"
        summary += f"**Overall Level:** {assessment.overall_level.value.title()}\n"
        summary += f"**Confidence Score:** {assessment.confidence_score:.1f}/1.0\n\n"
        
        if assessment.strengths:
            summary += "**Strengths:**\n"
            for strength in assessment.strengths[:3]:  # Show top 3
                summary += f"• {strength}\n"
            summary += "\n"
        
        if assessment.weaknesses:
            summary += "**Areas for Improvement:**\n"
            for weakness in assessment.weaknesses[:3]:  # Show top 3
                summary += f"• {weakness}\n"
            summary += "\n"
        
        if assessment.recommendations:
            summary += "**Recommendations:**\n"
            for rec in assessment.recommendations[:3]:  # Show top 3
                summary += f"• {rec}\n"
        
        return summary
    
    async def _save_conversation(
        self, 
        user_id: str, 
        user_message: str, 
        response: Optional[ConversationResponse]
    ) -> None:
        """Save conversation to user history"""
        try:
            if response:
                await self.user_context_manager.add_conversation(
                    user_id=user_id,
                    user_message=user_message,
                    assistant_response=response.message,
                    message_type=response.response_type,
                    context_data=response.metadata
                )
        except Exception as e:
            logger.error(f"Error saving conversation for user {user_id}: {e}")
    
    async def _handle_resume_analysis_request(self, user_id: str, message: str, 
                                            user_context: UserContext) -> ConversationResponse:
        """Handle resume analysis requests"""
        try:
            logger.info(f"Handling resume analysis request for user {user_id}")
            
            # Check if user is asking for general resume advice or has specific resume data
            if self._is_general_resume_question(message):
                return await self._provide_general_resume_advice(user_id, message, user_context)
            
            # For now, provide guidance on how to submit resume for analysis
            # In a full implementation, this would handle file uploads or structured input
            response_message = self._create_resume_submission_guidance(user_context)
            
            return ConversationResponse(
                message=response_message,
                response_type=MessageType.CAREER_COACHING,
                metadata={
                    "intent": "resume_analysis",
                    "requires_resume_data": True
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling resume analysis request: {e}")
            return ConversationResponse(
                message="I'd love to help you with your resume! Could you tell me what specific aspect of your resume you'd like feedback on?",
                response_type=MessageType.CAREER_COACHING
            )
    
    async def analyze_resume_data(self, user_id: str, resume: Resume) -> ConversationResponse:
        """Analyze provided resume data and return feedback"""
        try:
            logger.info(f"Analyzing resume for user {user_id}")
            
            # Get user context for personalized analysis
            user_context = await self._get_or_create_user_context(user_id)
            
            # Perform resume analysis
            analysis = await self.resume_analyzer.analyze_resume(resume, user_context)
            
            # Format analysis results for conversation
            response_message = self._format_resume_analysis_results(analysis)
            
            # Save analysis results to user context
            await self._save_resume_analysis(user_id, analysis)
            
            return ConversationResponse(
                message=response_message,
                response_type=MessageType.CAREER_COACHING,
                metadata={
                    "intent": "resume_analysis_results",
                    "analysis_id": analysis.resume_id,
                    "overall_score": analysis.overall_score,
                    "critical_issues": len(analysis.get_feedback_by_severity(FeedbackSeverity.CRITICAL))
                }
            )
            
        except Exception as e:
            logger.error(f"Error analyzing resume: {e}")
            return ConversationResponse(
                message="I encountered an issue analyzing your resume. Please try again or contact support if the problem persists.",
                response_type=MessageType.ERROR
            )
    
    async def _provide_general_resume_advice(self, user_id: str, message: str, 
                                           user_context: UserContext) -> ConversationResponse:
        """Provide general resume advice based on user question"""
        try:
            # Use AI service to generate personalized resume advice
            advice_prompt = self._build_resume_advice_prompt(message, user_context)
            ai_response = await self.ai_service.generate_response(advice_prompt, user_context)
            
            # Add some structured advice
            structured_advice = self._get_structured_resume_advice(message)
            
            combined_response = f"{ai_response}\n\n{structured_advice}"
            
            return ConversationResponse(
                message=combined_response,
                response_type=MessageType.CAREER_COACHING,
                metadata={
                    "intent": "general_resume_advice",
                    "advice_type": self._categorize_resume_question(message)
                }
            )
            
        except Exception as e:
            logger.error(f"Error providing resume advice: {e}")
            return ConversationResponse(
                message="Here are some general resume tips: Keep it concise (1-2 pages), use action verbs, quantify achievements, and tailor it to each job application.",
                response_type=MessageType.CAREER_COACHING
            )
    
    def _is_general_resume_question(self, message: str) -> bool:
        """Check if message is asking for general resume advice vs. specific analysis"""
        general_patterns = [
            "how to", "what should", "tips for", "advice on", "help with",
            "best practices", "how do i", "what makes", "should i include"
        ]
        
        message_lower = message.lower()
        return any(pattern in message_lower for pattern in general_patterns)
    
    def _create_resume_submission_guidance(self, user_context: UserContext) -> str:
        """Create guidance for submitting resume for analysis"""
        guidance = """I'd be happy to analyze your resume and provide personalized feedback! 

Here's what I can help you with:
• Overall resume structure and formatting
• Content quality and impact
• Industry-specific optimization
• ATS (Applicant Tracking System) compatibility
• Keyword optimization for your target role

To get started, you can:
1. Share specific sections of your resume for targeted feedback
2. Ask about resume best practices for your industry
3. Get advice on how to highlight your achievements

What specific aspect of your resume would you like to work on first?"""
        
        # Personalize based on user context
        if user_context.career_goals:
            goal = user_context.career_goals[0]
            guidance += f"\n\nSince you're interested in {goal}, I can provide industry-specific advice to make your resume stand out in that field."
        
        return guidance
    
    def _build_resume_advice_prompt(self, message: str, user_context: UserContext) -> str:
        """Build prompt for AI-generated resume advice"""
        context_info = ""
        if user_context.career_goals:
            context_info += f"Career goals: {', '.join(user_context.career_goals[:2])}\n"
        
        if user_context.current_skills:
            skills = list(user_context.current_skills.keys())[:5]
            context_info += f"Current skills: {', '.join(skills)}\n"
        
        prompt = f"""
        User is asking for resume advice: "{message}"
        
        User context:
        {context_info}
        
        Provide specific, actionable resume advice that addresses their question. 
        Focus on practical tips they can implement immediately.
        Keep the response encouraging and supportive.
        """
        
        return prompt
    
    def _get_structured_resume_advice(self, message: str) -> str:
        """Get structured resume advice based on question category"""
        message_lower = message.lower()
        
        if "format" in message_lower or "structure" in message_lower:
            return """
**Resume Structure Tips:**
• Use a clean, professional format with consistent fonts
• Include: Contact info, Summary, Experience, Education, Skills
• Use bullet points for easy scanning
• Keep to 1-2 pages maximum
• Use reverse chronological order for experience"""
        
        elif "skill" in message_lower:
            return """
**Skills Section Tips:**
• Include both technical and soft skills
• Match skills to job requirements
• Use specific tools/technologies, not just general terms
• Consider skill categories (Technical, Languages, etc.)
• Include proficiency levels if relevant"""
        
        elif "experience" in message_lower or "work" in message_lower:
            return """
**Experience Section Tips:**
• Start with strong action verbs (achieved, managed, developed)
• Quantify results with numbers and percentages
• Focus on achievements, not just responsibilities
• Use the STAR method (Situation, Task, Action, Result)
• Tailor descriptions to target role"""
        
        elif "summary" in message_lower or "objective" in message_lower:
            return """
**Professional Summary Tips:**
• Write 2-3 sentences highlighting your value proposition
• Include years of experience and key skills
• Mention your career goals or target role
• Use keywords from job descriptions
• Make it compelling and specific to you"""
        
        else:
            return """
**General Resume Tips:**
• Tailor your resume for each application
• Use keywords from the job description
• Proofread carefully for errors
• Save as PDF to preserve formatting
• Include relevant certifications and projects"""
    
    def _categorize_resume_question(self, message: str) -> str:
        """Categorize the type of resume question"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["format", "structure", "layout"]):
            return "formatting"
        elif any(word in message_lower for word in ["skill", "abilities", "competencies"]):
            return "skills"
        elif any(word in message_lower for word in ["experience", "work", "job"]):
            return "experience"
        elif any(word in message_lower for word in ["summary", "objective", "profile"]):
            return "summary"
        elif any(word in message_lower for word in ["keyword", "ats", "applicant tracking"]):
            return "optimization"
        else:
            return "general"
    
    def _format_resume_analysis_results(self, analysis: ResumeAnalysis) -> str:
        """Format resume analysis results for conversation display"""
        # Start with overall score
        score_emoji = "🟢" if analysis.overall_score >= 80 else "🟡" if analysis.overall_score >= 60 else "🔴"
        
        result = f"{score_emoji} **Resume Analysis Complete**\n"
        result += f"Overall Score: {analysis.overall_score:.1f}/100\n\n"
        
        # Add strengths
        if analysis.strengths:
            result += "**✅ Strengths:**\n"
            for strength in analysis.strengths[:3]:
                result += f"• {strength}\n"
            result += "\n"
        
        # Add critical feedback
        critical_feedback = analysis.get_feedback_by_severity(FeedbackSeverity.CRITICAL)
        if critical_feedback:
            result += "**🔴 Critical Issues:**\n"
            for feedback in critical_feedback:
                result += f"• {feedback.message}\n"
                result += f"  💡 {feedback.suggestion}\n"
            result += "\n"
        
        # Add important feedback
        important_feedback = analysis.get_feedback_by_severity(FeedbackSeverity.IMPORTANT)
        if important_feedback:
            result += "**🟡 Important Improvements:**\n"
            for feedback in important_feedback[:3]:
                result += f"• {feedback.message}\n"
                result += f"  💡 {feedback.suggestion}\n"
            result += "\n"
        
        # Add top recommendations
        if analysis.recommendations:
            result += "**🎯 Top Recommendations:**\n"
            for rec in analysis.recommendations[:3]:
                result += f"{rec}\n"
            result += "\n"
        
        # Add specific scores
        result += "**📊 Detailed Scores:**\n"
        result += f"• Industry Alignment: {analysis.industry_alignment*100:.0f}%\n"
        result += f"• ATS Compatibility: {analysis.ats_compatibility*100:.0f}%\n"
        result += f"• Keyword Optimization: {analysis.keyword_optimization*100:.0f}%\n\n"
        
        result += "Would you like me to elaborate on any specific area or help you improve a particular section?"
        
        return result
    
    async def _save_resume_analysis(self, user_id: str, analysis: ResumeAnalysis) -> None:
        """Save resume analysis results to user context"""
        try:
            # In a full implementation, this would save to database
            # For now, we'll add it to the user's conversation history
            await self.user_context_manager.add_conversation(
                user_id=user_id,
                user_message="Resume analysis completed",
                assistant_response=f"Analysis completed with score: {analysis.overall_score:.1f}",
                message_type=MessageType.CAREER_COACHING,
                context_data={
                    "analysis_id": analysis.resume_id,
                    "overall_score": analysis.overall_score,
                    "analysis_date": analysis.analyzed_at.isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error saving resume analysis: {e}")
    
    async def _handle_interview_preparation_request(self, user_id: str, message: str, 
                                                  user_context: UserContext) -> ConversationResponse:
        """Handle interview preparation requests"""
        try:
            logger.info(f"Handling interview preparation request for user {user_id}")
            
            # Check if user is asking for general interview advice or wants to start a practice session
            if self._is_general_interview_question(message):
                return await self._provide_general_interview_advice(user_id, message, user_context)
            
            # Check if user wants to start a practice session
            if self._wants_practice_session(message):
                return await self._initiate_interview_practice_session(user_id, message, user_context)
            
            # Check if user wants industry-specific guidance
            if self._wants_industry_guidance(message):
                return await self._provide_industry_interview_guidance(user_id, message, user_context)
            
            # Default to general interview preparation guidance
            response_message = self._create_interview_preparation_guidance(user_context)
            
            return ConversationResponse(
                message=response_message,
                response_type="career_coaching",
                metadata={
                    "intent": "interview_preparation",
                    "guidance_type": "general"
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling interview preparation request: {e}")
            return ConversationResponse(
                message="I'd love to help you prepare for interviews! What specific aspect of interview preparation would you like to work on?",
                response_type="career_coaching"
            )
    
    def _is_general_interview_question(self, message: str) -> bool:
        """Check if message is asking for general interview advice"""
        message_lower = message.lower()
        general_patterns = [
            "interview tips", "how to prepare", "interview advice", "what should i expect",
            "interview best practices", "how to answer", "common mistakes"
        ]
        return any(pattern in message_lower for pattern in general_patterns)
    
    def _wants_practice_session(self, message: str) -> bool:
        """Check if user wants to start a practice interview session"""
        message_lower = message.lower()
        practice_patterns = [
            "practice interview", "mock interview", "practice questions", "interview practice",
            "let's practice", "can we practice", "start practice", "practice session"
        ]
        return any(pattern in message_lower for pattern in practice_patterns)
    
    def _wants_industry_guidance(self, message: str) -> bool:
        """Check if user wants industry-specific interview guidance"""
        message_lower = message.lower()
        industry_patterns = [
            "tech interview", "software interview", "finance interview", "healthcare interview",
            "marketing interview", "consulting interview", "industry specific", "what to expect in"
        ]
        return any(pattern in message_lower for pattern in industry_patterns)
    
    async def _provide_general_interview_advice(self, user_id: str, message: str, 
                                              user_context: UserContext) -> ConversationResponse:
        """Provide AI-generated general interview advice"""
        try:
            # Build prompt for interview advice
            prompt = self._build_interview_advice_prompt(message, user_context)
            
            # Get AI response
            advice = await self.ai_service.generate_response(prompt, user_context)
            
            return ConversationResponse(
                message=advice,
                response_type="career_coaching",
                suggested_actions=[
                    "Start a practice interview session",
                    "Get industry-specific guidance",
                    "Practice common interview questions"
                ],
                metadata={
                    "intent": "interview_advice",
                    "advice_type": "general"
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating interview advice: {e}")
            return ConversationResponse(
                message=self._get_structured_interview_advice(message),
                response_type="career_coaching"
            )
    
    async def _initiate_interview_practice_session(self, user_id: str, message: str, 
                                                 user_context: UserContext) -> ConversationResponse:
        """Initiate an interview practice session"""
        try:
            # Extract target role and industry from message or user context
            target_role = self._extract_target_role(message, user_context)
            target_industry = self._extract_target_industry(message, user_context)
            
            # Create interview session
            session = await self.interview_service.create_interview_session(
                user_id=user_id,
                target_role=target_role,
                target_industry=target_industry,
                session_type=InterviewType.GENERAL,
                difficulty_level=DifficultyLevel.INTERMEDIATE,
                num_questions=5
            )
            
            # Get first question
            first_question = session.get_current_question()
            
            if first_question:
                response_message = f"""Great! I've created a practice interview session for a {target_role} position.

**Question 1 of {len(session.questions)}:**
{first_question.question}

Take your time to think about your answer. When you're ready, share your response and I'll provide detailed feedback to help you improve!

*Tip: Try to use the STAR method (Situation, Task, Action, Result) for behavioral questions.*"""
            else:
                response_message = "I've set up your practice session, but encountered an issue generating questions. Let me help you with some general interview preparation instead."
            
            return ConversationResponse(
                message=response_message,
                response_type="career_coaching",
                metadata={
                    "intent": "interview_practice",
                    "session_id": session.id,
                    "current_question": 0,
                    "total_questions": len(session.questions)
                }
            )
            
        except Exception as e:
            logger.error(f"Error initiating interview practice session: {e}")
            return ConversationResponse(
                message="I'd love to help you practice! Could you tell me what role you're preparing for?",
                response_type="career_coaching"
            )
    
    async def _provide_industry_interview_guidance(self, user_id: str, message: str, 
                                                 user_context: UserContext) -> ConversationResponse:
        """Provide industry-specific interview guidance"""
        try:
            # Extract industry from message
            industry = self._extract_industry_from_message(message)
            
            if not industry:
                industry = self._infer_industry_from_context(user_context)
            
            # Get industry guidance
            guidance = await self.interview_service.get_industry_guidance(industry)
            
            # Format guidance for display
            response_message = self._format_industry_guidance(guidance)
            
            return ConversationResponse(
                message=response_message,
                response_type="career_coaching",
                suggested_actions=[
                    f"Practice {industry.lower()} interview questions",
                    "Start a mock interview session",
                    "Get specific role preparation tips"
                ],
                metadata={
                    "intent": "industry_guidance",
                    "industry": industry
                }
            )
            
        except Exception as e:
            logger.error(f"Error providing industry guidance: {e}")
            return ConversationResponse(
                message="I can help you prepare for industry-specific interviews! Which industry are you targeting?",
                response_type="career_coaching"
            )
    
    def _extract_target_role(self, message: str, user_context: UserContext) -> str:
        """Extract target role from message or user context"""
        message_lower = message.lower()
        
        # Common role patterns
        role_patterns = {
            "software developer": ["software developer", "developer", "programmer", "software engineer"],
            "data scientist": ["data scientist", "data analyst", "machine learning engineer"],
            "product manager": ["product manager", "pm", "product owner"],
            "marketing manager": ["marketing manager", "marketing", "digital marketing"],
            "sales representative": ["sales rep", "sales", "account manager"],
            "consultant": ["consultant", "consulting", "advisor"]
        }
        
        for role, patterns in role_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                return role
        
        # Check user context career goals
        if user_context.career_goals:
            for goal in user_context.career_goals:
                goal_lower = goal.lower()
                for role, patterns in role_patterns.items():
                    if any(pattern in goal_lower for pattern in patterns):
                        return role
        
        return "Software Developer"  # Default role
    
    def _extract_target_industry(self, message: str, user_context: UserContext) -> str:
        """Extract target industry from message or user context"""
        return self._extract_industry_from_message(message) or self._infer_industry_from_context(user_context)
    
    def _extract_industry_from_message(self, message: str) -> Optional[str]:
        """Extract industry from message text"""
        message_lower = message.lower()
        
        industry_keywords = {
            "Technology": ["tech", "technology", "software", "it", "startup"],
            "Healthcare": ["healthcare", "medical", "health", "hospital", "pharma"],
            "Finance": ["finance", "banking", "investment", "fintech", "financial"],
            "Education": ["education", "academic", "university", "school", "teaching"],
            "Marketing": ["marketing", "advertising", "media", "digital marketing"],
            "Consulting": ["consulting", "advisory", "strategy", "management consulting"]
        }
        
        for industry, keywords in industry_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return industry
        
        return None
    
    def _infer_industry_from_context(self, user_context: UserContext) -> str:
        """Infer industry from user context"""
        if user_context.career_goals:
            goals_text = " ".join(user_context.career_goals).lower()
            
            industry_keywords = {
                "Technology": ["software", "developer", "programming", "tech", "engineer", "data"],
                "Healthcare": ["healthcare", "medical", "nurse", "doctor", "health"],
                "Finance": ["finance", "banking", "investment", "accounting", "financial"],
                "Education": ["education", "teacher", "instructor", "academic", "training"],
                "Marketing": ["marketing", "advertising", "social media", "brand", "digital marketing"],
                "Consulting": ["consulting", "consultant", "advisory", "strategy"]
            }
            
            for industry, keywords in industry_keywords.items():
                if any(keyword in goals_text for keyword in keywords):
                    return industry
        
        return "Technology"  # Default industry
    
    def _create_interview_preparation_guidance(self, user_context: UserContext) -> str:
        """Create general interview preparation guidance"""
        guidance = """I'm here to help you ace your interviews! Here's how I can assist you:

**🎯 Interview Preparation Options:**

**1. Practice Interview Session**
- Mock interview with realistic questions
- Personalized feedback on your responses
- Industry and role-specific questions

**2. General Interview Tips**
- Best practices for answering common questions
- How to structure your responses (STAR method)
- Body language and communication tips

**3. Industry-Specific Guidance**
- What to expect in your target industry
- Common questions and formats
- Key skills employers look for

**4. Question Practice**
- Behavioral interview questions
- Technical questions (for relevant roles)
- Situational and problem-solving scenarios

What would you like to focus on? Just let me know:
- "Start a practice session" for mock interviews
- "Interview tips" for general advice
- "Tech interview prep" for industry-specific guidance
- Or ask about any specific interview concern!"""

        return guidance
    
    def _build_interview_advice_prompt(self, message: str, user_context: UserContext) -> str:
        """Build prompt for AI-generated interview advice"""
        context_info = ""
        if user_context.career_goals:
            context_info = f"\nUser's career goals: {', '.join(user_context.career_goals)}"
        
        if user_context.current_skills:
            skills = ", ".join([f"{name} ({skill.level.value})" for name, skill in user_context.current_skills.items()])
            context_info += f"\nUser's skills: {skills}"
        
        prompt = f"""You are EdAgent, a supportive career coach helping with interview preparation.

User's question: {message}{context_info}

Provide helpful, specific interview advice that is:
- Encouraging and confidence-building
- Practical and actionable
- Tailored to their background when possible
- Focused on interview best practices

Keep your response conversational and supportive, as if you're a mentor helping them succeed."""
        
        return prompt
    
    def _get_structured_interview_advice(self, message: str) -> str:
        """Get structured interview advice based on question category"""
        message_lower = message.lower()
        
        if "nervous" in message_lower or "anxiety" in message_lower:
            return """**Managing Interview Nerves:**

• **Preparation is key** - The more prepared you are, the more confident you'll feel
• **Practice out loud** - Rehearse your answers to common questions
• **Arrive early** - Give yourself time to settle in and collect your thoughts
• **Deep breathing** - Take slow, deep breaths to calm your nerves
• **Positive visualization** - Imagine the interview going well
• **Remember it's a conversation** - They want you to succeed too!

Would you like to practice some questions to build your confidence?"""
        
        elif "questions to ask" in message_lower or "ask interviewer" in message_lower:
            return """**Great Questions to Ask Interviewers:**

**About the Role:**
• "What does a typical day look like in this position?"
• "What are the biggest challenges facing the team right now?"
• "How do you measure success in this role?"

**About Growth:**
• "What opportunities are there for professional development?"
• "Where do you see this role evolving in the next year?"

**About Culture:**
• "How would you describe the team dynamics?"
• "What do you enjoy most about working here?"

**About Next Steps:**
• "What are the next steps in the interview process?"
• "Is there anything else I can clarify about my background?"

Asking thoughtful questions shows genuine interest and helps you evaluate if it's the right fit!"""
        
        elif "what to wear" in message_lower or "dress code" in message_lower:
            return """**Interview Attire Guidelines:**

**General Rule:** Dress one level above the company's daily dress code

**Business Professional:**
• Suit (navy, charcoal, or black)
• Conservative shirt/blouse
• Professional shoes
• Minimal jewelry and accessories

**Business Casual:**
• Dress pants/skirt with button-down shirt
• Blazer (optional but recommended)
• Clean, polished shoes
• Professional but slightly relaxed

**Tips:**
• Research the company culture beforehand
• When in doubt, err on the side of being overdressed
• Ensure clothes are clean, pressed, and fit well
• Pay attention to grooming details

Remember: You want your skills and personality to be the focus, not your outfit!"""
        
        else:
            return """**Essential Interview Tips:**

**Before the Interview:**
• Research the company thoroughly
• Review the job description and match your experience
• Prepare specific examples using the STAR method
• Plan your route and arrive 10-15 minutes early

**During the Interview:**
• Make eye contact and offer a firm handshake
• Listen actively and ask clarifying questions
• Use specific examples to demonstrate your skills
• Show enthusiasm for the role and company

**Common Questions to Prepare:**
• "Tell me about yourself"
• "Why are you interested in this position?"
• "What are your strengths and weaknesses?"
• "Describe a challenge you overcame"

Would you like to practice answering any of these questions?"""
    
    def _format_industry_guidance(self, guidance: IndustryGuidance) -> str:
        """Format industry guidance for display"""
        result = f"**Interview Guidance for {guidance.industry} Industry**\n\n"
        
        if guidance.interview_format:
            result += f"**Typical Interview Process:**\n{guidance.interview_format}\n\n"
        
        if guidance.common_questions:
            result += "**Common Questions:**\n"
            for i, question in enumerate(guidance.common_questions[:5], 1):
                result += f"{i}. {question}\n"
            result += "\n"
        
        if guidance.key_skills:
            result += "**Key Skills Employers Look For:**\n"
            for skill in guidance.key_skills[:6]:
                result += f"• {skill}\n"
            result += "\n"
        
        if guidance.preparation_tips:
            result += "**Preparation Tips:**\n"
            for tip in guidance.preparation_tips[:5]:
                result += f"• {tip}\n"
            result += "\n"
        
        if guidance.red_flags:
            result += "**Things to Avoid:**\n"
            for flag in guidance.red_flags[:3]:
                result += f"• {flag}\n"
            result += "\n"
        
        result += "Would you like to start a practice session with industry-specific questions?"
        
        return result