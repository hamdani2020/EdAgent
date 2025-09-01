"""
Integration test for resume analysis functionality
"""

import pytest
from datetime import date
from unittest.mock import AsyncMock, patch

from edagent.models.resume import Resume, WorkExperience, Education, IndustryType
from edagent.models.user_context import UserContext, SkillLevel, SkillLevelEnum
from edagent.services.resume_analyzer import ResumeAnalyzer
from edagent.services.conversation_manager import ConversationManager


@pytest.mark.asyncio
async def test_end_to_end_resume_analysis():
    """Test complete resume analysis workflow"""
    
    # Create a sample resume
    work_exp = WorkExperience(
        job_title="Junior Software Developer",
        company="StartupTech Inc",
        start_date=date(2022, 6, 1),
        end_date=date(2024, 1, 31),
        description="Developed web applications using React and Node.js. Collaborated with senior developers on feature implementation.",
        achievements=[
            "Improved page load times by 25%",
            "Implemented 15+ new features",
            "Reduced bug reports by 30%"
        ],
        skills_used=["JavaScript", "React", "Node.js", "MongoDB"]
    )
    
    education = Education(
        degree="Bachelor of Computer Science",
        institution="Tech University",
        graduation_date=date(2022, 5, 15),
        gpa=3.6,
        relevant_coursework=["Data Structures", "Web Development", "Database Systems"]
    )
    
    resume = Resume(
        user_id="test_user_123",
        name="Alex Johnson",
        email="alex.johnson@email.com",
        phone="+1-555-0199",
        location="San Francisco, CA",
        summary="Motivated junior developer with 1.5 years of experience in full-stack web development. Passionate about creating user-friendly applications and learning new technologies.",
        work_experience=[work_exp],
        education=[education],
        skills=["JavaScript", "React", "Node.js", "Python", "Git", "MongoDB"],
        certifications=["FreeCodeCamp Full Stack Certification"],
        target_industry=IndustryType.TECHNOLOGY,
        target_role="Software Developer"
    )
    
    # Create user context
    user_context = UserContext(
        user_id="test_user_123",
        career_goals=["become a senior software developer", "work at a tech company"],
        current_skills={
            "javascript": SkillLevel("javascript", SkillLevelEnum.INTERMEDIATE, 0.7),
            "react": SkillLevel("react", SkillLevelEnum.INTERMEDIATE, 0.6),
            "python": SkillLevel("python", SkillLevelEnum.BEGINNER, 0.4)
        }
    )
    
    # Mock AI service for testing
    mock_ai_service = AsyncMock()
    mock_ai_service.generate_response.return_value = """
    Your resume shows good technical skills and quantifiable achievements. Here are some suggestions:
    
    Issue: Limited senior-level experience shown | Suggestion: Highlight leadership or mentoring activities
    Issue: Could use more diverse project examples | Suggestion: Include personal or open-source projects
    Issue: Missing some key technologies | Suggestion: Add experience with cloud platforms like AWS
    """
    
    # Create analyzer with mocked AI service
    analyzer = ResumeAnalyzer(ai_service=mock_ai_service)
    
    # Perform analysis
    analysis = await analyzer.analyze_resume(resume, user_context)
    
    # Verify analysis results
    assert analysis is not None
    assert analysis.resume_id == resume.id
    assert analysis.user_id == resume.user_id
    assert 0 <= analysis.overall_score <= 100
    
    # Should have some feedback
    assert len(analysis.feedback) > 0
    
    # Should have some strengths (good resume with achievements)
    assert len(analysis.strengths) > 0
    
    # Should have recommendations
    assert len(analysis.recommendations) > 0
    
    # Check specific analysis aspects
    assert 0 <= analysis.industry_alignment <= 1
    assert 0 <= analysis.ats_compatibility <= 1
    assert 0 <= analysis.keyword_optimization <= 1
    
    # Should score reasonably well (has experience, education, skills, achievements)
    assert analysis.overall_score > 50
    
    print(f"Analysis completed with score: {analysis.overall_score:.1f}")
    print(f"Strengths: {len(analysis.strengths)}")
    print(f"Feedback items: {len(analysis.feedback)}")
    print(f"Recommendations: {len(analysis.recommendations)}")


@pytest.mark.asyncio
async def test_conversation_manager_resume_flow():
    """Test resume analysis through conversation manager"""
    
    with patch('edagent.services.conversation_manager.GeminiAIService'), \
         patch('edagent.services.conversation_manager.UserContextManager'), \
         patch('edagent.services.conversation_manager.ContentRecommender'), \
         patch('edagent.services.conversation_manager.EnhancedLearningPathGenerator'):
        
        # Create conversation manager
        manager = ConversationManager()
        
        # Mock dependencies
        manager.ai_service = AsyncMock()
        manager.ai_service.generate_response.return_value = "I'd be happy to help you with your resume! Here are some tips for creating an effective resume..."
        
        manager.user_context_manager = AsyncMock()
        manager.user_context_manager.get_user_context.return_value = UserContext(
            user_id="test_user",
            career_goals=["software developer"]
        )
        manager.user_context_manager.add_conversation = AsyncMock()
        
        # Test resume advice request
        response = await manager.handle_message("test_user", "Can you help me improve my resume?")
        
        assert response is not None
        assert "resume" in response.message.lower()
        assert response.response_type == "career_coaching"
        
        # Test specific resume question
        response = await manager.handle_message("test_user", "What should I include in my resume skills section?")
        
        assert response is not None
        # This should be detected as resume-related and return career coaching or general text
        assert response.response_type in ["career_coaching", "text"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])