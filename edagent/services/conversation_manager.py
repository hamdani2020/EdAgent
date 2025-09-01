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
        self.content_recommender = ContentRecommender()
        self.prompt_builder = PromptBuilder()
        self.response_handler = StructuredResponseHandler()
        self.learning_path_generator = EnhancedLearningPathGenerator()
        
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