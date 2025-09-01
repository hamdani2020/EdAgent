"""
Prompt engineering system for EdAgent
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from ..models.user_context import UserContext, SkillLevel
from ..models.learning import SkillAssessment, LearningPath


class PromptTemplates:
    """Collection of prompt templates for different EdAgent functions"""
    
    # Base system prompt for EdAgent personality
    BASE_SYSTEM_PROMPT = """You are EdAgent, a supportive and encouraging AI career coach designed to help beginners learn new skills and advance their careers. Your personality is:

- Warm, friendly, and encouraging
- Patient and understanding with beginners
- Practical and action-oriented
- Knowledgeable about career development and learning paths
- Focused on free and affordable learning resources

Your core responsibilities:
1. Provide personalized career guidance and learning recommendations
2. Help users assess their current skills and identify growth areas
3. Create structured learning paths with manageable milestones
4. Recommend high-quality, preferably free educational resources
5. Offer career coaching advice including resume tips and interview preparation
6. Maintain an encouraging tone while being realistic about challenges

Guidelines:
- Always respond within 3 seconds with relevant, encouraging advice
- Ask clarifying questions when users express uncertainty
- Remember and reference previous conversation context
- Break down complex learning paths into manageable steps
- Prioritize free resources but mention quality paid alternatives when relevant
- Provide specific, actionable advice rather than generic responses
- Celebrate user progress and milestones
- Use positive, optimistic language that keeps conversations solution-oriented
- Stay warm and friendly while being professional
- Be decisive, precise, and clear in your recommendations"""

    # Skill assessment specific prompts
    SKILL_ASSESSMENT_INTRO = """I'm going to help you assess your current skills so we can create the perfect learning path for you. This will be a friendly conversation where I'll ask you some questions about your experience and knowledge.

Don't worry if you're a complete beginner - everyone starts somewhere, and I'm here to help you succeed! Let's start with understanding your background and what you'd like to achieve."""

    SKILL_ASSESSMENT_QUESTIONS = {
        "programming": [
            "Tell me about any programming languages you've worked with, even if just a little bit.",
            "Have you built any projects, even small ones? What were they?",
            "What programming concepts do you feel most comfortable with?",
            "What areas of programming do you find most challenging or confusing?",
            "How do you typically approach solving a coding problem?"
        ],
        "web_development": [
            "What experience do you have with HTML, CSS, and JavaScript?",
            "Have you built any websites or web applications?",
            "Are you familiar with any web frameworks or libraries?",
            "How comfortable are you with responsive design and mobile-first development?",
            "What aspects of web development interest you most?"
        ],
        "data_science": [
            "What's your experience with data analysis or statistics?",
            "Have you worked with any data analysis tools like Excel, Python, or R?",
            "Tell me about any data projects you've worked on.",
            "How comfortable are you with mathematics and statistics?",
            "What type of data problems interest you most?"
        ],
        "design": [
            "What design tools have you used (Figma, Photoshop, Canva, etc.)?",
            "Have you created any designs for websites, apps, or print?",
            "How do you approach the design process?",
            "What design principles are you familiar with?",
            "What type of design work interests you most?"
        ]
    }

    # Learning path creation prompts
    LEARNING_PATH_SYSTEM_PROMPT = """You are an expert learning path designer. Create comprehensive, beginner-friendly learning paths that:

1. Start from the user's current skill level
2. Progress logically through foundational to advanced concepts
3. Include practical, hands-on projects
4. Prioritize free, high-quality resources
5. Break learning into manageable 1-3 week milestones
6. Include diverse learning formats (videos, articles, practice exercises)
7. Provide clear success criteria for each milestone

Focus on creating paths that are:
- Achievable and motivating
- Practical and job-relevant
- Supported by excellent free resources
- Designed to build confidence progressively"""

    # Career coaching prompts
    RESUME_REVIEW_PROMPT = """As an experienced career coach, provide specific, actionable feedback on this resume. Focus on:

1. Content and relevance to target roles
2. Structure and formatting
3. Achievement quantification
4. Keyword optimization
5. Areas for improvement
6. Strengths to highlight

Provide encouraging but honest feedback with specific suggestions for improvement."""

    INTERVIEW_PREP_PROMPT = """As a career coach specializing in interview preparation, help this user prepare for interviews in their target field. Provide:

1. Common interview questions for their field
2. Specific examples of how to answer behavioral questions
3. Technical questions they should be prepared for
4. Tips for showcasing their skills and experience
5. Advice on questions to ask the interviewer
6. Confidence-building strategies

Tailor your advice to their experience level and target role."""

    # Content recommendation prompts
    CONTENT_SEARCH_PROMPT = """Find high-quality, beginner-friendly educational content for: {topic}

Prioritize:
1. Free resources (YouTube, free courses, documentation)
2. Highly-rated content with good reviews
3. Recent and up-to-date materials
4. Diverse formats (video, text, interactive)
5. Content that builds practical skills

Consider the user's learning style: {learning_style}
Time commitment: {time_commitment}
Budget preference: {budget_preference}"""


class PromptBuilder:
    """Builds context-aware prompts for different EdAgent functions"""
    
    def __init__(self):
        self.templates = PromptTemplates()
    
    def build_conversation_prompt(self, user_message: str, context: UserContext) -> str:
        """Build a prompt for general conversation with user context"""
        system_prompt = self._build_base_system_prompt(context)
        
        # Add conversation context
        conversation_context = self._build_conversation_context(context)
        
        full_prompt = f"""{system_prompt}

{conversation_context}

User message: {user_message}

Response:"""
        
        return full_prompt
    
    def build_skill_assessment_prompt(self, skill_area: str, user_responses: List[str]) -> str:
        """Build a prompt for skill assessment analysis"""
        prompt = f"""Analyze the following user responses to assess their skill level in {skill_area}. 

User responses:
{self._format_responses(user_responses)}

Provide a structured assessment in JSON format with the following structure:
{{
    "skill_area": "{skill_area}",
    "overall_level": "beginner|intermediate|advanced",
    "confidence_score": 0.0-1.0,
    "strengths": ["list", "of", "identified", "strengths"],
    "weaknesses": ["list", "of", "areas", "for", "improvement"],
    "recommendations": ["specific", "learning", "recommendations"],
    "detailed_scores": {{
        "category1": 0.0-1.0,
        "category2": 0.0-1.0
    }}
}}

Assessment Guidelines:
- Be encouraging while providing honest evaluation
- Focus on specific, actionable feedback
- Identify concrete next steps for improvement
- Consider the user's enthusiasm and willingness to learn
- Provide realistic but optimistic recommendations"""
        
        return prompt
    
    def build_learning_path_prompt(self, goal: str, current_skills: Dict[str, SkillLevel], 
                                 user_context: Optional[UserContext] = None) -> str:
        """Build a prompt for learning path creation"""
        
        # Prepare current skills summary
        skills_summary = self._format_skills_summary(current_skills)
        
        # Add user preferences if available
        preferences_text = ""
        if user_context and user_context.learning_preferences:
            prefs = user_context.learning_preferences
            preferences_text = f"""
User Learning Preferences:
- Learning style: {prefs.learning_style.value}
- Time commitment: {prefs.time_commitment}
- Budget preference: {prefs.budget_preference}
- Preferred content types: {', '.join(prefs.content_types)}
- Difficulty preference: {prefs.difficulty_preference}"""
        
        prompt = f"""{self.templates.LEARNING_PATH_SYSTEM_PROMPT}

Goal: {goal}

Current Skills:
{skills_summary}
{preferences_text}

Create a structured learning path with the following JSON format:
{{
    "title": "Learning Path Title",
    "description": "Brief description of what this path will achieve",
    "difficulty_level": "beginner|intermediate|advanced",
    "prerequisites": ["list", "of", "prerequisites"],
    "target_skills": ["skills", "that", "will", "be", "learned"],
    "milestones": [
        {{
            "title": "Milestone Title",
            "description": "What will be accomplished",
            "skills_to_learn": ["specific", "skills"],
            "prerequisites": ["required", "knowledge"],
            "estimated_duration_days": 14,
            "difficulty_level": "beginner|intermediate|advanced",
            "assessment_criteria": ["how", "to", "measure", "completion"],
            "resources": [
                {{
                    "title": "Resource Title",
                    "url": "https://example.com",
                    "type": "video|course|article|interactive",
                    "is_free": true,
                    "duration_hours": 2
                }}
            ]
        }}
    ]
}}

Guidelines:
- Create 4-8 milestones that build progressively
- Prioritize free resources (YouTube, free courses, documentation)
- Include realistic time estimates
- Make each milestone achievable in 1-3 weeks
- Include diverse learning formats
- Provide specific, actionable assessment criteria
- Consider the user's current skill level and preferences"""
        
        return prompt
    
    def build_resume_review_prompt(self, resume_text: str, target_role: str = "") -> str:
        """Build a prompt for resume review and feedback"""
        role_context = f" for {target_role} positions" if target_role else ""
        
        prompt = f"""{self.templates.RESUME_REVIEW_PROMPT}

Target Role{role_context}

Resume Content:
{resume_text}

Provide detailed feedback in the following format:
1. Overall Impression
2. Strengths
3. Areas for Improvement
4. Specific Suggestions
5. Action Items

Be encouraging but provide honest, actionable feedback."""
        
        return prompt
    
    def build_interview_prep_prompt(self, target_role: str, user_background: str, 
                                  experience_level: str = "entry") -> str:
        """Build a prompt for interview preparation"""
        prompt = f"""{self.templates.INTERVIEW_PREP_PROMPT}

Target Role: {target_role}
Experience Level: {experience_level}
User Background: {user_background}

Provide comprehensive interview preparation including:
1. Common Questions (5-7 questions)
2. Technical Questions (if applicable)
3. Behavioral Question Examples
4. Questions to Ask the Interviewer
5. Preparation Tips
6. Confidence Building Advice

Tailor all advice to their experience level and target role."""
        
        return prompt
    
    def build_content_recommendation_prompt(self, topic: str, user_context: Optional[UserContext] = None) -> str:
        """Build a prompt for content recommendation"""
        learning_style = "mixed"
        time_commitment = "flexible"
        budget_preference = "free"
        
        if user_context and user_context.learning_preferences:
            prefs = user_context.learning_preferences
            learning_style = prefs.learning_style.value
            time_commitment = prefs.time_commitment
            budget_preference = prefs.budget_preference
        
        return self.templates.CONTENT_SEARCH_PROMPT.format(
            topic=topic,
            learning_style=learning_style,
            time_commitment=time_commitment,
            budget_preference=budget_preference
        )
    
    def _build_base_system_prompt(self, context: Optional[UserContext] = None) -> str:
        """Build the base system prompt with user context"""
        base_prompt = self.templates.BASE_SYSTEM_PROMPT
        
        if context:
            context_info = self._build_user_context_summary(context)
            base_prompt += f"\n\nCurrent user context:\n{context_info}"
        
        return base_prompt
    
    def _build_user_context_summary(self, context: UserContext) -> str:
        """Build a summary of user context for prompt inclusion"""
        summary_parts = [f"- User ID: {context.user_id}"]
        
        if context.career_goals:
            summary_parts.append(f"- Career goals: {', '.join(context.career_goals)}")
        
        if context.current_skills:
            skills_list = []
            for skill_name, skill_level in context.current_skills.items():
                skills_list.append(f"{skill_name} ({skill_level.level.value})")
            summary_parts.append(f"- Current skills: {', '.join(skills_list)}")
        
        if context.learning_preferences:
            prefs = context.learning_preferences
            summary_parts.extend([
                f"- Learning style: {prefs.learning_style.value}",
                f"- Time commitment: {prefs.time_commitment}",
                f"- Budget preference: {prefs.budget_preference}"
            ])
        
        return "\n".join(summary_parts)
    
    def _build_conversation_context(self, context: UserContext) -> str:
        """Build conversation context from user history"""
        if not context.conversation_history:
            return "This is the start of a new conversation."
        
        # Include last few messages for context (limit to avoid token overflow)
        recent_messages = context.conversation_history[-5:] if len(context.conversation_history) > 5 else context.conversation_history
        
        context_text = "Recent conversation context:\n"
        for i, message in enumerate(recent_messages, 1):
            context_text += f"{i}. {message}\n"
        
        return context_text
    
    def _format_responses(self, responses: List[str]) -> str:
        """Format user responses for assessment prompt"""
        formatted = []
        for i, response in enumerate(responses, 1):
            formatted.append(f"{i}. {response}")
        return "\n".join(formatted)
    
    def _format_skills_summary(self, skills: Dict[str, SkillLevel]) -> str:
        """Format skills summary for learning path prompt"""
        if not skills:
            return "No specific skills assessed yet - complete beginner"
        
        skills_list = []
        for skill_name, skill_level in skills.items():
            skills_list.append(f"- {skill_name}: {skill_level.level.value} (confidence: {skill_level.confidence_score:.1f})")
        
        return "\n".join(skills_list)


class SkillAssessmentQuestionGenerator:
    """Generates contextual questions for skill assessments"""
    
    def __init__(self):
        self.templates = PromptTemplates()
    
    def get_assessment_questions(self, skill_area: str, num_questions: int = 5) -> List[str]:
        """Get assessment questions for a specific skill area"""
        skill_area_lower = skill_area.lower().replace(" ", "_")
        
        # Find matching question set
        question_set = None
        
        # Direct match first
        if skill_area_lower in self.templates.SKILL_ASSESSMENT_QUESTIONS:
            question_set = self.templates.SKILL_ASSESSMENT_QUESTIONS[skill_area_lower]
        else:
            # Partial match
            for area, questions in self.templates.SKILL_ASSESSMENT_QUESTIONS.items():
                if area in skill_area_lower or any(word in skill_area_lower for word in area.split("_")):
                    question_set = questions
                    break
        
        # If no specific questions found, use generic programming questions
        if not question_set:
            question_set = self.templates.SKILL_ASSESSMENT_QUESTIONS.get("programming", [])
        
        # Return requested number of questions (or all if fewer available)
        return question_set[:num_questions] if len(question_set) >= num_questions else question_set
    
    def generate_followup_question(self, skill_area: str, previous_response: str) -> str:
        """Generate a follow-up question based on user's previous response"""
        # This could be enhanced with AI generation, but for now use predefined logic
        response_lower = previous_response.lower()
        
        if "beginner" in response_lower or "new" in response_lower or "just started" in response_lower:
            return f"That's great that you're getting started with {skill_area}! What motivated you to begin learning this skill?"
        
        elif "project" in response_lower or "built" in response_lower:
            return "Tell me more about that project. What was the most challenging part, and how did you overcome it?"
        
        elif "difficult" in response_lower or "challenging" in response_lower or "struggle" in response_lower:
            return "What specific aspects do you find most challenging? Understanding these will help me recommend the best resources for you."
        
        else:
            return f"Can you give me a specific example of how you've applied your {skill_area} knowledge?"


# Convenience functions for easy access
def build_conversation_prompt(user_message: str, context: UserContext) -> str:
    """Convenience function to build conversation prompt"""
    builder = PromptBuilder()
    return builder.build_conversation_prompt(user_message, context)


def build_skill_assessment_prompt(skill_area: str, user_responses: List[str]) -> str:
    """Convenience function to build skill assessment prompt"""
    builder = PromptBuilder()
    return builder.build_skill_assessment_prompt(skill_area, user_responses)


def build_learning_path_prompt(goal: str, current_skills: Dict[str, SkillLevel], 
                             user_context: Optional[UserContext] = None) -> str:
    """Convenience function to build learning path prompt"""
    builder = PromptBuilder()
    return builder.build_learning_path_prompt(goal, current_skills, user_context)


def get_assessment_questions(skill_area: str, num_questions: int = 5) -> List[str]:
    """Convenience function to get assessment questions"""
    generator = SkillAssessmentQuestionGenerator()
    return generator.get_assessment_questions(skill_area, num_questions)