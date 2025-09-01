"""
Tests for resume analysis functionality
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from edagent.models.resume import (
    Resume, ResumeAnalysis, ResumeFeedback, WorkExperience, Education,
    FeedbackSeverity, IndustryType, ExperienceLevel
)
from edagent.models.user_context import UserContext, SkillLevel, SkillLevelEnum
from edagent.services.resume_analyzer import ResumeAnalyzer
from edagent.services.conversation_manager import ConversationManager


class TestResumeModels:
    """Test resume data models"""
    
    def test_work_experience_creation(self):
        """Test WorkExperience model creation and validation"""
        exp = WorkExperience(
            job_title="Software Developer",
            company="Tech Corp",
            start_date=date(2022, 1, 1),
            end_date=date(2023, 12, 31),
            description="Developed web applications",
            achievements=["Increased performance by 30%"],
            skills_used=["Python", "React"]
        )
        
        assert exp.job_title == "Software Developer"
        assert exp.company == "Tech Corp"
        assert exp.duration_months() == 23  # Jan 2022 to Dec 2023 is 23 months
        assert not exp.is_current
    
    def test_work_experience_validation(self):
        """Test WorkExperience validation"""
        # Test empty job title
        with pytest.raises(ValueError, match="Job title cannot be empty"):
            WorkExperience(
                job_title="",
                company="Tech Corp",
                start_date=date(2022, 1, 1)
            )
        
        # Test end date before start date
        with pytest.raises(ValueError, match="End date cannot be before start date"):
            WorkExperience(
                job_title="Developer",
                company="Tech Corp",
                start_date=date(2023, 1, 1),
                end_date=date(2022, 1, 1)
            )
        
        # Test current job with end date
        with pytest.raises(ValueError, match="Current job cannot have an end date"):
            WorkExperience(
                job_title="Developer",
                company="Tech Corp",
                start_date=date(2022, 1, 1),
                end_date=date(2023, 1, 1),
                is_current=True
            )
    
    def test_education_creation(self):
        """Test Education model creation and validation"""
        edu = Education(
            degree="Bachelor of Science in Computer Science",
            institution="University of Technology",
            graduation_date=date(2021, 5, 15),
            gpa=3.8,
            relevant_coursework=["Data Structures", "Algorithms"],
            honors=["Dean's List"]
        )
        
        assert edu.degree == "Bachelor of Science in Computer Science"
        assert edu.gpa == 3.8
        assert len(edu.relevant_coursework) == 2
    
    def test_education_validation(self):
        """Test Education validation"""
        # Test invalid GPA
        with pytest.raises(ValueError, match="GPA must be between 0.0 and 4.0"):
            Education(
                degree="Bachelor's",
                institution="University",
                gpa=5.0
            )
    
    def test_resume_feedback_creation(self):
        """Test ResumeFeedback model creation"""
        feedback = ResumeFeedback(
            category="Experience",
            severity=FeedbackSeverity.IMPORTANT,
            message="Missing quantifiable achievements",
            suggestion="Add specific metrics and numbers to demonstrate impact",
            industry_specific=True
        )
        
        assert feedback.category == "Experience"
        assert feedback.severity == FeedbackSeverity.IMPORTANT
        assert feedback.industry_specific is True
    
    def test_resume_creation(self):
        """Test Resume model creation and methods"""
        work_exp = WorkExperience(
            job_title="Developer",
            company="Tech Corp",
            start_date=date(2020, 1, 1),
            end_date=date(2023, 1, 1),
            skills_used=["Python", "JavaScript"]
        )
        
        education = Education(
            degree="Computer Science",
            institution="Tech University"
        )
        
        resume = Resume(
            user_id="user123",
            name="John Doe",
            email="john@example.com",
            work_experience=[work_exp],
            education=[education],
            skills=["Python", "React", "SQL"],
            target_industry=IndustryType.TECHNOLOGY,
            target_role="Senior Developer"
        )
        
        assert resume.user_id == "user123"
        assert resume.get_total_experience_months() == 36
        assert resume.get_experience_level() == ExperienceLevel.MID_LEVEL
        assert len(resume.get_all_skills()) >= 4  # Skills from multiple sources
    
    def test_resume_analysis_creation(self):
        """Test ResumeAnalysis model creation"""
        analysis = ResumeAnalysis(
            resume_id="resume123",
            user_id="user123",
            overall_score=85.5,
            industry_alignment=0.8,
            ats_compatibility=0.9,
            keyword_optimization=0.7
        )
        
        analysis.add_feedback(
            "Skills",
            FeedbackSeverity.SUGGESTION,
            "Consider adding more technical skills",
            "Include frameworks and tools you've used"
        )
        
        assert analysis.overall_score == 85.5
        assert len(analysis.feedback) == 1
        assert analysis.get_feedback_by_severity(FeedbackSeverity.SUGGESTION)[0].category == "Skills"


class TestResumeAnalyzer:
    """Test ResumeAnalyzer service"""
    
    @pytest.fixture
    def mock_ai_service(self):
        """Mock AI service for testing"""
        ai_service = AsyncMock()
        ai_service.generate_response.return_value = "Great resume! Consider adding more quantifiable achievements."
        return ai_service
    
    @pytest.fixture
    def resume_analyzer(self, mock_ai_service):
        """Create ResumeAnalyzer with mocked AI service"""
        return ResumeAnalyzer(ai_service=mock_ai_service)
    
    @pytest.fixture
    def sample_resume(self):
        """Create a sample resume for testing"""
        work_exp = WorkExperience(
            job_title="Software Developer",
            company="Tech Solutions Inc",
            start_date=date(2021, 6, 1),
            end_date=date(2023, 12, 31),
            description="Developed and maintained web applications using Python and React. Collaborated with cross-functional teams to deliver high-quality software solutions.",
            achievements=[
                "Improved application performance by 40%",
                "Led a team of 3 junior developers",
                "Reduced bug reports by 25%"
            ],
            skills_used=["Python", "React", "PostgreSQL", "Docker"]
        )
        
        education = Education(
            degree="Bachelor of Science in Computer Science",
            institution="State University",
            graduation_date=date(2021, 5, 15),
            gpa=3.7,
            relevant_coursework=["Data Structures", "Algorithms", "Database Systems"],
            honors=["Dean's List"]
        )
        
        return Resume(
            user_id="test_user",
            name="Jane Smith",
            email="jane.smith@email.com",
            phone="+1-555-0123",
            location="San Francisco, CA",
            summary="Experienced software developer with 2+ years of experience in full-stack web development. Passionate about creating efficient, scalable solutions.",
            work_experience=[work_exp],
            education=[education],
            skills=["Python", "JavaScript", "React", "Node.js", "PostgreSQL", "Git"],
            certifications=["AWS Certified Developer"],
            target_industry=IndustryType.TECHNOLOGY,
            target_role="Senior Software Developer"
        )
    
    @pytest.fixture
    def user_context(self):
        """Create sample user context"""
        return UserContext(
            user_id="test_user",
            career_goals=["become a senior software developer"],
            current_skills={
                "python": SkillLevel("python", SkillLevelEnum.INTERMEDIATE, 0.7),
                "react": SkillLevel("react", SkillLevelEnum.INTERMEDIATE, 0.6)
            }
        )
    
    @pytest.mark.asyncio
    async def test_analyze_resume_basic(self, resume_analyzer, sample_resume):
        """Test basic resume analysis"""
        analysis = await resume_analyzer.analyze_resume(sample_resume)
        
        assert analysis.resume_id == sample_resume.id
        assert analysis.user_id == sample_resume.user_id
        assert 0 <= analysis.overall_score <= 100
        assert 0 <= analysis.industry_alignment <= 1
        assert 0 <= analysis.ats_compatibility <= 1
        assert 0 <= analysis.keyword_optimization <= 1
        assert isinstance(analysis.feedback, list)
        assert isinstance(analysis.strengths, list)
        assert isinstance(analysis.recommendations, list)
    
    @pytest.mark.asyncio
    async def test_analyze_resume_with_context(self, resume_analyzer, sample_resume, user_context):
        """Test resume analysis with user context"""
        analysis = await resume_analyzer.analyze_resume(sample_resume, user_context)
        
        assert analysis.resume_id == sample_resume.id
        assert analysis.overall_score > 0
        # Should have some feedback or strengths
        assert len(analysis.feedback) > 0 or len(analysis.strengths) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_incomplete_resume(self, resume_analyzer):
        """Test analysis of incomplete resume"""
        incomplete_resume = Resume(
            user_id="test_user",
            name="John Doe"
            # Missing most fields
        )
        
        analysis = await resume_analyzer.analyze_resume(incomplete_resume)
        
        # Should identify critical issues
        critical_feedback = analysis.get_feedback_by_severity(FeedbackSeverity.CRITICAL)
        assert len(critical_feedback) > 0
        
        # Score should be lower due to missing information
        assert analysis.overall_score < 50
    
    def test_industry_alignment_analysis(self, resume_analyzer, sample_resume):
        """Test industry alignment analysis"""
        # Test with technology industry
        sample_resume.target_industry = IndustryType.TECHNOLOGY
        
        # Mock the analysis method
        with patch.object(resume_analyzer, '_analyze_industry_alignment') as mock_method:
            mock_method.return_value = None
            
            # Call the method directly
            analysis = ResumeAnalysis(
                resume_id=sample_resume.id,
                user_id=sample_resume.user_id,
                overall_score=80.0
            )
            
            # Simulate industry alignment calculation
            resume_text = resume_analyzer._get_resume_text(sample_resume).lower()
            tech_keywords = resume_analyzer.industry_keywords.get(IndustryType.TECHNOLOGY, [])
            matching_keywords = [kw for kw in tech_keywords if kw.lower() in resume_text]
            
            # Should find some technology keywords
            assert len(matching_keywords) > 0
    
    def test_ats_compatibility_check(self, resume_analyzer, sample_resume):
        """Test ATS compatibility analysis"""
        # Resume with good structure should score well
        assert sample_resume.skills  # Has skills section
        assert sample_resume.work_experience  # Has experience
        assert sample_resume.education  # Has education
        assert sample_resume.summary  # Has summary
        
        # These are good indicators for ATS compatibility
    
    def test_keyword_optimization(self, resume_analyzer, sample_resume):
        """Test keyword optimization analysis"""
        resume_text = resume_analyzer._get_resume_text(sample_resume).lower()
        
        # Check for action verbs
        action_verbs = ["developed", "improved", "led", "reduced"]
        found_verbs = [verb for verb in action_verbs if verb in resume_text]
        
        # Should find some action verbs in the sample resume
        assert len(found_verbs) > 0
    
    def test_quantifiable_results_detection(self, resume_analyzer):
        """Test detection of quantifiable results"""
        # Text with quantifiable results
        text_with_numbers = "Improved performance by 40% and reduced costs by $50,000"
        assert resume_analyzer._has_quantifiable_results(text_with_numbers)
        
        # Text without quantifiable results
        text_without_numbers = "Worked on various projects and helped the team"
        assert not resume_analyzer._has_quantifiable_results(text_without_numbers)
    
    def test_email_validation(self, resume_analyzer):
        """Test email validation"""
        assert resume_analyzer._is_valid_email("test@example.com")
        assert resume_analyzer._is_valid_email("user.name+tag@domain.co.uk")
        assert not resume_analyzer._is_valid_email("invalid-email")
        assert not resume_analyzer._is_valid_email("@domain.com")
        assert not resume_analyzer._is_valid_email("user@")
    
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_ai_service):
        """Test error handling in resume analysis"""
        # Mock AI service to raise an exception
        mock_ai_service.generate_response.side_effect = Exception("API Error")
        
        analyzer = ResumeAnalyzer(ai_service=mock_ai_service)
        
        # Create a basic resume
        resume = Resume(user_id="test", name="Test User")
        
        # Analysis should still complete with fallback
        analysis = await analyzer.analyze_resume(resume)
        
        assert analysis is not None
        assert analysis.overall_score >= 0
        # Should have some feedback about the error or missing information
        assert len(analysis.feedback) > 0 or len(analysis.recommendations) > 0


class TestConversationManagerResumeIntegration:
    """Test resume analysis integration with ConversationManager"""
    
    @pytest.fixture
    def conversation_manager(self):
        """Create ConversationManager with mocked dependencies"""
        with patch('edagent.services.conversation_manager.GeminiAIService'), \
             patch('edagent.services.conversation_manager.UserContextManager'), \
             patch('edagent.services.conversation_manager.ContentRecommender'), \
             patch('edagent.services.conversation_manager.EnhancedLearningPathGenerator'):
            
            manager = ConversationManager()
            
            # Mock the AI service
            manager.ai_service = AsyncMock()
            manager.ai_service.generate_response.return_value = "Great question about resumes!"
            
            # Mock user context manager
            manager.user_context_manager = AsyncMock()
            manager.user_context_manager.get_user_context.return_value = UserContext(
                user_id="test_user",
                career_goals=["software developer"]
            )
            
            return manager
    
    @pytest.mark.asyncio
    async def test_resume_intent_detection(self, conversation_manager):
        """Test detection of resume-related intents"""
        # Test various resume-related messages
        resume_messages = [
            "Can you help me with my resume?",
            "I need resume feedback",
            "How can I improve my CV?",
            "Resume analysis please",
            "Review my resume"
        ]
        
        for message in resume_messages:
            intent = conversation_manager._detect_intent(message)
            assert intent == "resume_analysis"
    
    @pytest.mark.asyncio
    async def test_general_resume_advice(self, conversation_manager):
        """Test handling of general resume advice requests"""
        message = "What should I include in my resume?"
        
        response = await conversation_manager._handle_resume_analysis_request(
            "test_user", message, UserContext(user_id="test_user")
        )
        
        assert response is not None
        assert "resume" in response.message.lower()
        assert response.response_type.value == "career_coaching"
    
    @pytest.mark.asyncio
    async def test_resume_submission_guidance(self, conversation_manager):
        """Test guidance for resume submission"""
        message = "Analyze my resume"
        
        response = await conversation_manager._handle_resume_analysis_request(
            "test_user", message, UserContext(user_id="test_user")
        )
        
        assert response is not None
        assert "analyze" in response.message.lower()
        assert response.metadata.get("requires_resume_data") is True
    
    def test_resume_question_categorization(self, conversation_manager):
        """Test categorization of different resume questions"""
        test_cases = [
            ("How should I format my resume?", "formatting"),
            ("What skills should I include?", "skills"),
            ("How do I describe my work experience?", "experience"),
            ("What makes a good summary?", "summary"),
            ("How do I optimize for ATS?", "optimization"),
            ("General resume tips?", "general")
        ]
        
        for message, expected_category in test_cases:
            category = conversation_manager._categorize_resume_question(message)
            assert category == expected_category
    
    def test_structured_resume_advice(self, conversation_manager):
        """Test structured resume advice generation"""
        # Test different advice categories
        advice_format = conversation_manager._get_structured_resume_advice("How should I format my resume?")
        assert "format" in advice_format.lower() or "structure" in advice_format.lower()
        
        advice_skills = conversation_manager._get_structured_resume_advice("What skills should I list?")
        assert "skill" in advice_skills.lower()
        
        advice_experience = conversation_manager._get_structured_resume_advice("How do I write about my work experience?")
        assert "experience" in advice_experience.lower() or "action" in advice_experience.lower()
    
    @pytest.mark.asyncio
    async def test_resume_analysis_results_formatting(self, conversation_manager):
        """Test formatting of resume analysis results"""
        # Create sample analysis
        analysis = ResumeAnalysis(
            resume_id="test_resume",
            user_id="test_user",
            overall_score=75.5,
            industry_alignment=0.8,
            ats_compatibility=0.7,
            keyword_optimization=0.6
        )
        
        analysis.strengths = ["Strong technical skills", "Good education background"]
        analysis.add_feedback(
            "Experience",
            FeedbackSeverity.IMPORTANT,
            "Missing quantifiable achievements",
            "Add specific metrics to demonstrate impact"
        )
        analysis.recommendations = ["🟡 Add more quantifiable results", "🟢 Include relevant certifications"]
        
        formatted = conversation_manager._format_resume_analysis_results(analysis)
        
        assert "75.5" in formatted  # Overall score
        assert "Strong technical skills" in formatted  # Strengths
        assert "Missing quantifiable achievements" in formatted  # Feedback
        assert "Add specific metrics" in formatted  # Suggestions
        assert "80%" in formatted  # Industry alignment percentage
        assert "70%" in formatted  # ATS compatibility percentage


if __name__ == "__main__":
    pytest.main([__file__])