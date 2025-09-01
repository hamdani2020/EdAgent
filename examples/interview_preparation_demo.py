"""
Demo script for interview preparation functionality
"""

import asyncio
import os
from datetime import datetime

# Add the parent directory to the path so we can import edagent
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from edagent.models.interview import (
    InterviewQuestion, InterviewSession, InterviewFeedback, IndustryGuidance,
    InterviewType, DifficultyLevel, FeedbackType
)
from edagent.models.user_context import UserContext, SkillLevel, SkillLevelEnum, UserPreferences
from edagent.services.interview_preparation import InterviewPreparationService
from edagent.services.conversation_manager import ConversationManager


async def demo_interview_models():
    """Demonstrate interview data models"""
    print("=" * 60)
    print("INTERVIEW PREPARATION MODELS DEMO")
    print("=" * 60)
    
    # Create an interview question
    print("\n1. Creating an Interview Question:")
    question = InterviewQuestion(
        question="Tell me about a time when you had to work with a difficult team member and how you handled the situation.",
        question_type=InterviewType.BEHAVIORAL,
        difficulty=DifficultyLevel.INTERMEDIATE,
        industry="Technology",
        role_level="mid",
        sample_answer="In my previous role, I worked with a colleague who was resistant to feedback. I approached this by first trying to understand their perspective through one-on-one conversations, then finding common ground on project goals, and finally establishing clear communication protocols that worked for both of us. This resulted in improved collaboration and successful project completion.",
        key_points=[
            "Specific situation description",
            "Actions taken to address the difficulty", 
            "Communication strategies used",
            "Outcome and lessons learned"
        ],
        follow_up_questions=[
            "How do you typically handle conflict in the workplace?",
            "What would you do if the situation hadn't improved?"
        ],
        tags=["behavioral", "teamwork", "conflict-resolution"]
    )
    
    print(f"Question: {question.question}")
    print(f"Type: {question.question_type.value}")
    print(f"Difficulty: {question.difficulty.value}")
    print(f"Key Points: {', '.join(question.key_points)}")
    
    # Create interview feedback
    print("\n2. Creating Interview Feedback:")
    feedback = InterviewFeedback(
        question_id=question.id,
        user_response="I once worked with someone who was always negative and criticized everyone's ideas. I tried to stay positive and focus on the work, and eventually things got better.",
        feedback_type=FeedbackType.IMPROVEMENT,
        feedback_text="Your response shows good intentions, but could be strengthened with more specific details about your actions and the outcomes.",
        score=6.5,
        strengths=[
            "Maintained positive attitude",
            "Focused on work objectives"
        ],
        improvements=[
            "Add specific examples of actions taken",
            "Include measurable outcomes",
            "Describe communication strategies used",
            "Explain what you learned from the experience"
        ],
        suggestions=[
            "Use the STAR method (Situation, Task, Action, Result)",
            "Practice with more detailed examples",
            "Focus on your proactive role in resolving the situation"
        ]
    )
    
    print(f"Score: {feedback.score}/10")
    print(f"Feedback: {feedback.feedback_text}")
    print(f"Strengths: {', '.join(feedback.strengths)}")
    print(f"Improvements: {', '.join(feedback.improvements[:2])}...")
    
    # Create interview session
    print("\n3. Creating Interview Session:")
    session = InterviewSession(
        user_id="demo-user-123",
        session_name="Software Developer Interview Practice",
        target_role="Software Developer",
        target_industry="Technology",
        session_type=InterviewType.BEHAVIORAL,
        difficulty_level=DifficultyLevel.INTERMEDIATE
    )
    
    # Add questions to session
    session.add_question(question)
    
    # Add another question
    technical_question = InterviewQuestion(
        question="Describe your approach to debugging a complex technical issue.",
        question_type=InterviewType.TECHNICAL,
        difficulty=DifficultyLevel.INTERMEDIATE,
        key_points=["Systematic approach", "Tools and techniques", "Problem isolation", "Documentation"]
    )
    session.add_question(technical_question)
    
    print(f"Session: {session.session_name}")
    print(f"Target Role: {session.target_role}")
    print(f"Questions: {len(session.questions)}")
    print(f"Current Question: {session.get_current_question().question[:50]}...")
    
    # Simulate answering questions
    print("\n4. Simulating Interview Responses:")
    session.add_response("I once worked with someone who was always negative...")
    session.add_feedback(feedback)
    
    session.add_response("When debugging, I start by reproducing the issue...")
    
    # Complete session
    session.complete_session()
    
    print(f"Session completed at: {session.completed_at}")
    print(f"Session summary: {session.session_summary}")
    
    # Create industry guidance
    print("\n5. Creating Industry Guidance:")
    guidance = IndustryGuidance(
        industry="Technology",
        common_questions=[
            "Describe your technical background",
            "How do you approach debugging complex issues?",
            "Tell me about a challenging project you worked on"
        ],
        key_skills=["Programming", "Problem-solving", "Communication", "Teamwork"],
        interview_format="Phone screening, technical assessment, system design, behavioral interview",
        preparation_tips=[
            "Practice coding problems on LeetCode",
            "Review system design fundamentals", 
            "Prepare behavioral examples using STAR method"
        ],
        red_flags=["Lack of technical depth", "Poor communication skills"],
        success_factors=["Strong technical foundation", "Clear communication", "Cultural fit"]
    )
    
    print(f"Industry: {guidance.industry}")
    print(f"Common Questions: {len(guidance.common_questions)}")
    print(f"Key Skills: {', '.join(guidance.key_skills)}")
    print(f"Preparation Tips: {len(guidance.preparation_tips)}")


async def demo_interview_service():
    """Demonstrate interview preparation service with mock AI"""
    print("\n" + "=" * 60)
    print("INTERVIEW PREPARATION SERVICE DEMO")
    print("=" * 60)
    
    # Create a mock AI service for demo purposes
    class MockAIService:
        async def _make_api_call(self, model, prompt, config):
            if "questions" in prompt.lower():
                return '''
                {
                    "questions": [
                        {
                            "question": "Why are you interested in this position?",
                            "key_points": ["Company research", "Role alignment", "Career goals"],
                            "sample_answer": "I'm excited about this opportunity because it aligns with my career goals and allows me to contribute to meaningful projects.",
                            "follow_up_questions": ["What do you know about our company culture?"],
                            "tags": ["motivation", "company-fit"]
                        },
                        {
                            "question": "Describe a challenging project you worked on.",
                            "key_points": ["Project complexity", "Your role", "Challenges faced", "Solutions implemented", "Results achieved"],
                            "sample_answer": "I worked on a project that required integrating multiple systems with tight deadlines. I took the lead on architecture design and coordinated with different teams to ensure successful delivery.",
                            "follow_up_questions": ["What would you do differently?", "How did you handle the pressure?"],
                            "tags": ["experience", "leadership", "problem-solving"]
                        }
                    ]
                }
                '''
            elif "feedback" in prompt.lower():
                return '''
                {
                    "score": 8.0,
                    "feedback_text": "Strong response that demonstrates clear motivation and research about the company. Good structure and specific examples.",
                    "strengths": ["Shows genuine interest", "Demonstrates research", "Clear communication"],
                    "improvements": ["Could mention specific company projects", "Add more personal connection"],
                    "suggestions": ["Research recent company news", "Practice with more examples"],
                    "feedback_type": "positive"
                }
                '''
            elif "industry" in prompt.lower():
                return '''
                {
                    "common_questions": [
                        "Describe your technical background",
                        "How do you stay updated with technology trends?",
                        "Tell me about a time you had to learn a new technology quickly"
                    ],
                    "key_skills": ["Programming", "Problem-solving", "Communication", "Continuous learning"],
                    "interview_format": "Technical screening, coding challenge, system design, behavioral interview",
                    "preparation_tips": [
                        "Practice coding problems",
                        "Review system design concepts",
                        "Prepare behavioral examples"
                    ],
                    "red_flags": ["Lack of technical curiosity", "Poor communication"],
                    "success_factors": ["Technical competence", "Cultural fit", "Growth mindset"]
                }
                '''
        
        def _get_model(self, model_type):
            return "mock-model"
        
        def _get_generation_config(self, model_type):
            return {"temperature": 0.7}
    
    # Create interview service with mock AI
    mock_ai = MockAIService()
    interview_service = InterviewPreparationService(ai_service=mock_ai)
    
    print("\n1. Creating Interview Session:")
    session = await interview_service.create_interview_session(
        user_id="demo-user-123",
        target_role="Software Engineer",
        target_industry="Technology",
        session_type=InterviewType.BEHAVIORAL,
        difficulty_level=DifficultyLevel.INTERMEDIATE,
        num_questions=2
    )
    
    print(f"Created session: {session.session_name}")
    print(f"Number of questions: {len(session.questions)}")
    
    # Display first question
    first_question = session.get_current_question()
    print(f"\nFirst Question: {first_question.question}")
    print(f"Key Points: {', '.join(first_question.key_points)}")
    
    print("\n2. Providing Feedback:")
    user_response = "I'm interested in this position because I want to grow my career and work on interesting projects with a great team."
    
    feedback = await interview_service.provide_feedback(first_question, user_response)
    
    print(f"User Response: {user_response}")
    print(f"Score: {feedback.score}/10")
    print(f"Feedback: {feedback.feedback_text}")
    print(f"Strengths: {', '.join(feedback.strengths)}")
    print(f"Improvements: {', '.join(feedback.improvements)}")
    
    print("\n3. Getting Industry Guidance:")
    guidance = await interview_service.get_industry_guidance("Technology")
    
    print(f"Industry: {guidance.industry}")
    print(f"Common Questions:")
    for i, question in enumerate(guidance.common_questions, 1):
        print(f"  {i}. {question}")
    
    print(f"Key Skills: {', '.join(guidance.key_skills)}")
    print(f"Interview Format: {guidance.interview_format}")
    
    print("\n4. Generating Practice Questions:")
    user_context = UserContext(
        user_id="demo-user-123",
        current_skills={
            "python": SkillLevel("python", SkillLevelEnum.INTERMEDIATE, 0.7),
            "javascript": SkillLevel("javascript", SkillLevelEnum.BEGINNER, 0.4)
        },
        career_goals=["become a full-stack developer"],
        learning_preferences=UserPreferences(
            learning_style="visual",
            time_commitment="10 hours/week"
        )
    )
    
    practice_questions = await interview_service.generate_practice_questions(
        user_context=user_context,
        target_role="Full Stack Developer",
        num_questions=2
    )
    
    print(f"Generated {len(practice_questions)} practice questions:")
    for i, question in enumerate(practice_questions, 1):
        print(f"  {i}. {question.question}")


async def demo_conversation_integration():
    """Demonstrate interview preparation integration with conversation manager"""
    print("\n" + "=" * 60)
    print("CONVERSATION MANAGER INTEGRATION DEMO")
    print("=" * 60)
    
    # Create conversation manager (this will use mocked services in a real demo)
    conversation_manager = ConversationManager()
    
    # Mock the dependencies for demo
    class MockUserContextManager:
        async def get_user_context(self, user_id):
            return UserContext(
                user_id=user_id,
                current_skills={
                    "python": SkillLevel("python", SkillLevelEnum.INTERMEDIATE, 0.7)
                },
                career_goals=["become a software engineer"]
            )
        
        async def create_user_context(self, user_id):
            return await self.get_user_context(user_id)
        
        async def add_conversation(self, **kwargs):
            pass
    
    class MockAIService:
        async def generate_response(self, prompt, context):
            return """Here are some essential interview tips:

1. **Research the company** - Know their mission, values, and recent news
2. **Prepare specific examples** - Use the STAR method for behavioral questions
3. **Practice common questions** - "Tell me about yourself", "Why do you want this job?"
4. **Prepare thoughtful questions** - Show genuine interest in the role and company
5. **Dress appropriately** - When in doubt, err on the side of being overdressed

Would you like to practice some interview questions together?"""
        
        async def _make_api_call(self, model, prompt, config):
            return '''
            {
                "questions": [
                    {
                        "question": "Tell me about yourself and your background in software development",
                        "key_points": ["Professional background", "Technical skills", "Career goals"],
                        "sample_answer": "I'm a software developer with 3 years of experience...",
                        "follow_up_questions": ["What programming languages do you prefer?"],
                        "tags": ["introduction", "background"]
                    }
                ]
            }
            '''
        
        def _get_model(self, model_type):
            return "mock-model"
        
        def _get_generation_config(self, model_type):
            return {"temperature": 0.7}
    
    # Replace with mocks for demo
    conversation_manager.user_context_manager = MockUserContextManager()
    conversation_manager.ai_service = MockAIService()
    conversation_manager.interview_service.ai_service = MockAIService()
    
    print("\n1. Testing Interview Intent Detection:")
    test_messages = [
        "I need help with interview preparation",
        "Can we practice interview questions?", 
        "I'm nervous about my upcoming interview",
        "What should I expect in a tech interview?"
    ]
    
    for message in test_messages:
        intent = conversation_manager._detect_intent(message)
        print(f"Message: '{message}' -> Intent: {intent}")
    
    print("\n2. Handling Interview Advice Request:")
    response = await conversation_manager.handle_message(
        user_id="demo-user-123",
        message="Can you give me some interview tips?"
    )
    
    print(f"User: Can you give me some interview tips?")
    print(f"EdAgent: {response.message[:200]}...")
    print(f"Response Type: {response.response_type}")
    print(f"Suggested Actions: {response.suggested_actions}")
    
    print("\n3. Handling Practice Session Request:")
    response = await conversation_manager.handle_message(
        user_id="demo-user-123", 
        message="I want to practice interview questions for a software engineer position"
    )
    
    print(f"User: I want to practice interview questions for a software engineer position")
    print(f"EdAgent: {response.message[:200]}...")
    print(f"Metadata: {response.metadata}")


async def main():
    """Run all demos"""
    print("🎯 INTERVIEW PREPARATION SYSTEM DEMO")
    print("This demo showcases the interview preparation functionality of EdAgent")
    
    try:
        await demo_interview_models()
        await demo_interview_service()
        await demo_conversation_integration()
        
        print("\n" + "=" * 60)
        print("✅ DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nThe interview preparation system includes:")
        print("• Comprehensive data models for questions, sessions, and feedback")
        print("• AI-powered question generation and feedback")
        print("• Industry-specific interview guidance")
        print("• Integration with the conversation manager")
        print("• Support for different interview types and difficulty levels")
        print("• Session management and progress tracking")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())