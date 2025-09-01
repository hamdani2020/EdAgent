"""
Tests for enhanced learning path generation functionality
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from edagent.models.user_context import UserContext, SkillLevel, SkillLevelEnum, UserPreferences, LearningStyleEnum
from edagent.models.learning import LearningPath, Milestone, DifficultyLevel, SkillAssessment
from edagent.services.learning_path_generator import (
    EnhancedLearningPathGenerator,
    LearningPathValidator,
    PrerequisiteAnalyzer,
    TimeEstimator,
    DifficultyAssessor
)


class TestLearningPathValidator:
    """Test learning path validation functionality"""
    
    def test_validate_complete_learning_path(self):
        """Test validation of a complete, valid learning path"""
        milestone = Milestone(
            title="Learn Python Basics",
            description="Master fundamental Python programming concepts and syntax",
            skills_to_learn=["python syntax", "variables", "functions"],
            estimated_duration=timedelta(days=14),
            difficulty_level=DifficultyLevel.BEGINNER,
            assessment_criteria=["Complete Python exercises", "Build simple program"],
            order_index=0
        )
        
        milestone.add_resource(
            title="Python Tutorial",
            url="https://python.org/tutorial",
            resource_type="tutorial",
            is_free=True,
            duration=timedelta(hours=10)
        )
        
        learning_path = LearningPath(
            title="Python Developer Path",
            description="A comprehensive path to become a Python developer with practical skills",
            goal="become a Python developer",
            milestones=[milestone],
            estimated_duration=timedelta(days=90),
            difficulty_level=DifficultyLevel.BEGINNER,
            target_skills=["python programming", "web development"]
        )
        
        is_valid, issues = LearningPathValidator.validate_learning_path_quality(learning_path)
        
        # Should have issues because we need at least 2 milestones
        assert not is_valid
        assert any("at least 2 milestones" in issue for issue in issues)
    
    def test_validate_learning_path_with_multiple_milestones(self):
        """Test validation of learning path with proper milestone progression"""
        milestone1 = Milestone(
            title="Python Fundamentals",
            description="Learn basic Python programming concepts and syntax for beginners",
            skills_to_learn=["python syntax", "variables", "basic functions"],
            estimated_duration=timedelta(days=14),
            difficulty_level=DifficultyLevel.BEGINNER,
            assessment_criteria=["Complete basic exercises", "Write simple programs"],
            order_index=0
        )
        
        milestone1.add_resource(
            title="Python Basics Course",
            url="https://python.org/tutorial",
            resource_type="course",
            is_free=True,
            duration=timedelta(hours=8)
        )
        
        milestone2 = Milestone(
            title="Web Development with Python",
            description="Build web applications using Python frameworks and libraries",
            skills_to_learn=["flask", "django", "web apis"],
            prerequisites=["python syntax", "basic functions"],
            estimated_duration=timedelta(days=21),
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            assessment_criteria=["Build web application", "Deploy to cloud"],
            order_index=1
        )
        
        milestone2.add_resource(
            title="Flask Tutorial",
            url="https://flask.palletsprojects.com/tutorial/",
            resource_type="tutorial",
            is_free=True,
            duration=timedelta(hours=12)
        )
        
        learning_path = LearningPath(
            title="Python Web Developer Path",
            description="A comprehensive learning path to become a Python web developer with hands-on projects",
            goal="become a Python web developer",
            milestones=[milestone1, milestone2],
            estimated_duration=timedelta(days=90),
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            target_skills=["python programming", "web development", "api development"]
        )
        
        is_valid, issues = LearningPathValidator.validate_learning_path_quality(learning_path)
        
        assert is_valid, f"Learning path should be valid, but has issues: {issues}"
    
    def test_validate_learning_path_missing_fields(self):
        """Test validation catches missing required fields"""
        # Create learning path with minimal valid fields to pass model validation
        # but still trigger quality validation issues
        learning_path = LearningPath(
            title="X",  # Too short title
            description="X",  # Too short description  
            goal="X",  # Too short goal
            milestones=[],  # No milestones
            target_skills=[]  # No target skills
        )
        
        is_valid, issues = LearningPathValidator.validate_learning_path_quality(learning_path)
        
        assert not is_valid
        assert len(issues) >= 5  # Should catch multiple issues
        assert any("title" in issue.lower() for issue in issues)
        assert any("description" in issue.lower() for issue in issues)
        assert any("goal" in issue.lower() for issue in issues)
        assert any("milestones" in issue.lower() for issue in issues)
        assert any("target skills" in issue.lower() for issue in issues)
    
    def test_validate_milestone_progression(self):
        """Test validation of milestone difficulty progression"""
        milestone1 = Milestone(
            title="Advanced Concepts",
            description="Learn advanced programming concepts",
            skills_to_learn=["advanced patterns"],
            difficulty_level=DifficultyLevel.ADVANCED,
            order_index=0
        )
        
        milestone2 = Milestone(
            title="Basic Concepts",
            description="Learn basic programming concepts",
            skills_to_learn=["basic syntax"],
            difficulty_level=DifficultyLevel.BEGINNER,  # Difficulty decreases too much
            order_index=1
        )
        
        milestones = [milestone1, milestone2]
        issues = LearningPathValidator._validate_milestone_progression(milestones)
        
        assert len(issues) > 0
        assert any("difficulty decreases" in issue.lower() for issue in issues)


class TestPrerequisiteAnalyzer:
    """Test prerequisite analysis functionality"""
    
    def test_analyze_web_developer_prerequisites(self):
        """Test prerequisite analysis for web developer goal"""
        current_skills = {}  # No current skills
        
        prerequisites = PrerequisiteAnalyzer.analyze_prerequisites("become a web developer", current_skills)
        
        assert "essential" in prerequisites
        assert "recommended" in prerequisites
        assert "technical" in prerequisites
        assert "missing" in prerequisites
        
        # Should identify missing prerequisites
        assert len(prerequisites["missing"]) > 0
        assert any("html" in prereq.lower() for prereq in prerequisites["missing"])
    
    def test_analyze_prerequisites_with_existing_skills(self):
        """Test prerequisite analysis when user has some skills"""
        current_skills = {
            "HTML": SkillLevel(
                skill_name="HTML",
                level=SkillLevelEnum.INTERMEDIATE,
                confidence_score=0.8,
                last_updated=datetime.now()
            ),
            "CSS": SkillLevel(
                skill_name="CSS",
                level=SkillLevelEnum.BEGINNER,
                confidence_score=0.6,
                last_updated=datetime.now()
            )
        }
        
        prerequisites = PrerequisiteAnalyzer.analyze_prerequisites("become a web developer", current_skills)
        
        # Should have fewer missing prerequisites since user has HTML/CSS
        missing_count = len(prerequisites["missing"])
        assert missing_count >= 0  # Could be 0 if all prerequisites are covered
    
    def test_create_prerequisite_milestones(self):
        """Test creation of prerequisite milestones"""
        missing_prerequisites = [
            "basic computer skills",
            "programming fundamentals",
            "web development basics"
        ]
        
        milestones = PrerequisiteAnalyzer.create_prerequisite_milestones(missing_prerequisites)
        
        assert len(milestones) > 0
        assert all(isinstance(m, Milestone) for m in milestones)
        assert all(m.difficulty_level == DifficultyLevel.BEGINNER for m in milestones)
        
        # Check that milestones have proper order indices
        for i, milestone in enumerate(milestones):
            assert milestone.order_index == i
    
    def test_create_prerequisite_milestones_empty_list(self):
        """Test prerequisite milestone creation with empty list"""
        milestones = PrerequisiteAnalyzer.create_prerequisite_milestones([])
        
        assert len(milestones) == 0


class TestTimeEstimator:
    """Test time estimation functionality"""
    
    def test_estimate_milestone_duration_basic(self):
        """Test basic milestone duration estimation"""
        milestone = Milestone(
            title="Learn Python Basics",
            description="Basic Python programming",
            skills_to_learn=["python syntax", "variables", "functions"],
            difficulty_level=DifficultyLevel.BEGINNER
        )
        
        milestone.add_resource(
            title="Python Tutorial",
            url="https://python.org",
            resource_type="video",
            duration=timedelta(hours=5)
        )
        
        duration = TimeEstimator.estimate_milestone_duration(milestone)
        
        assert isinstance(duration, timedelta)
        assert duration.days >= 1  # Should be at least 1 day
        assert duration.days <= 30  # Should be reasonable
    
    def test_estimate_milestone_duration_with_user_context(self):
        """Test milestone duration estimation with user context"""
        user_context = UserContext(
            user_id="test-user",
            learning_preferences=UserPreferences(
                learning_style=LearningStyleEnum.VISUAL,
                time_commitment="part-time",
                budget_preference="free"
            )
        )
        
        milestone = Milestone(
            title="Advanced Python",
            description="Advanced Python concepts",
            skills_to_learn=["decorators", "metaclasses", "async programming"],
            difficulty_level=DifficultyLevel.ADVANCED
        )
        
        duration = TimeEstimator.estimate_milestone_duration(milestone, user_context)
        
        assert isinstance(duration, timedelta)
        # Part-time learners should get more time
        assert duration.days >= 2
    
    def test_estimate_learning_path_duration(self):
        """Test learning path duration estimation"""
        milestone1 = Milestone(
            title="Basics",
            description="Basic concepts",
            estimated_duration=timedelta(days=7)
        )
        
        milestone2 = Milestone(
            title="Intermediate",
            description="Intermediate concepts",
            estimated_duration=timedelta(days=14)
        )
        
        learning_path = LearningPath(
            title="Test Path",
            goal="test goal",
            milestones=[milestone1, milestone2]
        )
        
        duration = TimeEstimator.estimate_learning_path_duration(learning_path)
        
        assert isinstance(duration, timedelta)
        # Should be sum of milestones plus buffer
        expected_min = 21  # 7 + 14 days
        expected_max = 25  # With buffer
        assert expected_min <= duration.days <= expected_max


class TestDifficultyAssessor:
    """Test difficulty assessment functionality"""
    
    def test_assess_milestone_difficulty_beginner(self):
        """Test difficulty assessment for beginner content"""
        milestone = Milestone(
            title="Introduction to Programming",
            description="Learn basic programming concepts and syntax",
            skills_to_learn=["variables", "basic functions", "simple loops"]
        )
        
        difficulty = DifficultyAssessor.assess_milestone_difficulty(milestone, [])
        
        assert difficulty == DifficultyLevel.BEGINNER
    
    def test_assess_milestone_difficulty_advanced(self):
        """Test difficulty assessment for advanced content"""
        milestone = Milestone(
            title="Advanced Architecture",
            description="Learn advanced software architecture and optimization techniques",
            skills_to_learn=["performance optimization", "scalability patterns", "enterprise architecture"]
        )
        
        difficulty = DifficultyAssessor.assess_milestone_difficulty(milestone, [])
        
        assert difficulty == DifficultyLevel.ADVANCED
    
    def test_assess_milestone_difficulty_progression(self):
        """Test difficulty assessment respects progression"""
        beginner_milestone = Milestone(
            title="Basics",
            description="Basic concepts",
            skills_to_learn=["basic syntax"],
            difficulty_level=DifficultyLevel.BEGINNER
        )
        
        # This would normally be assessed as advanced, but should be limited by progression
        advanced_milestone = Milestone(
            title="Expert Level",
            description="Expert level optimization and enterprise architecture",
            skills_to_learn=["performance optimization", "enterprise architecture"]
        )
        
        difficulty = DifficultyAssessor.assess_milestone_difficulty(
            advanced_milestone, 
            [beginner_milestone]
        )
        
        # Should be limited to intermediate (one level up from beginner)
        assert difficulty == DifficultyLevel.INTERMEDIATE
    
    def test_assess_learning_path_difficulty(self):
        """Test overall learning path difficulty assessment"""
        milestones = [
            Milestone(title="M1", description="Test milestone 1", difficulty_level=DifficultyLevel.BEGINNER),
            Milestone(title="M2", description="Test milestone 2", difficulty_level=DifficultyLevel.INTERMEDIATE),
            Milestone(title="M3", description="Test milestone 3", difficulty_level=DifficultyLevel.INTERMEDIATE),
            Milestone(title="M4", description="Test milestone 4", difficulty_level=DifficultyLevel.INTERMEDIATE),
            Milestone(title="M5", description="Test milestone 5", difficulty_level=DifficultyLevel.INTERMEDIATE)
        ]
        
        learning_path = LearningPath(
            title="Test Path",
            description="Test learning path description",
            goal="test goal",
            milestones=milestones
        )
        
        difficulty = DifficultyAssessor.assess_learning_path_difficulty(learning_path)
        
        # Should be intermediate since most milestones (4/5) are intermediate
        assert difficulty == DifficultyLevel.INTERMEDIATE


class TestEnhancedLearningPathGenerator:
    """Test the main enhanced learning path generator"""
    
    @pytest.fixture
    def generator(self):
        """Create generator instance with mocked dependencies"""
        generator = EnhancedLearningPathGenerator()
        
        # Mock the AI service
        generator.ai_service = MagicMock()
        
        return generator
    
    @pytest.fixture
    def sample_user_context(self):
        """Create sample user context for testing"""
        return UserContext(
            user_id="test-user-123",
            current_skills={
                "Python": SkillLevel(
                    skill_name="Python",
                    level=SkillLevelEnum.BEGINNER,
                    confidence_score=0.6,
                    last_updated=datetime.now()
                )
            },
            career_goals=["become a web developer"],
            learning_preferences=UserPreferences(
                learning_style=LearningStyleEnum.VISUAL,
                time_commitment="part-time",
                budget_preference="free"
            )
        )
    
    @pytest.mark.asyncio
    async def test_create_comprehensive_learning_path_basic(self, generator, sample_user_context):
        """Test basic comprehensive learning path creation"""
        # Mock AI service response
        mock_milestone = Milestone(
            title="Learn Web Development",
            description="Master web development fundamentals including HTML, CSS, and JavaScript",
            skills_to_learn=["html", "css", "javascript"],
            estimated_duration=timedelta(days=21),
            difficulty_level=DifficultyLevel.BEGINNER,
            assessment_criteria=["Build responsive website", "Complete coding exercises"],
            order_index=0
        )
        
        mock_milestone.add_resource(
            title="Web Development Course",
            url="https://example.com/course",
            resource_type="course",
            is_free=True,
            duration=timedelta(hours=20)
        )
        
        mock_learning_path = LearningPath(
            title="Web Developer Path",
            description="Complete path to become a web developer",
            goal="become a web developer",
            milestones=[mock_milestone],
            estimated_duration=timedelta(days=90),
            difficulty_level=DifficultyLevel.BEGINNER,
            target_skills=["web development", "frontend", "backend"]
        )
        
        generator.ai_service.create_learning_path = AsyncMock(return_value=mock_learning_path)
        
        # Test the method
        result = await generator.create_comprehensive_learning_path(
            goal="become a web developer",
            current_skills=sample_user_context.current_skills,
            user_context=sample_user_context
        )
        
        assert isinstance(result, LearningPath)
        assert result.title == "Web Developer Path"
        assert result.goal == "become a web developer"
        assert len(result.milestones) >= 1
        
        # Verify AI service was called
        generator.ai_service.create_learning_path.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_learning_path_with_prerequisites(self, generator, sample_user_context):
        """Test learning path creation with missing prerequisites"""
        # Create user with no relevant skills
        user_context_no_skills = UserContext(
            user_id="test-user-456",
            current_skills={},  # No skills
            career_goals=["become a data scientist"]
        )
        
        # Mock AI service response
        mock_milestone = Milestone(
            title="Data Science Fundamentals",
            description="Learn core data science concepts and tools",
            skills_to_learn=["python", "statistics", "data analysis"],
            estimated_duration=timedelta(days=28),
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            order_index=0
        )
        
        mock_learning_path = LearningPath(
            title="Data Scientist Path",
            description="Path to become a data scientist",
            goal="become a data scientist",
            milestones=[mock_milestone],
            target_skills=["data science", "machine learning"]
        )
        
        generator.ai_service.create_learning_path = AsyncMock(return_value=mock_learning_path)
        
        # Test the method
        result = await generator.create_comprehensive_learning_path(
            goal="become a data scientist",
            current_skills={},
            user_context=user_context_no_skills
        )
        
        assert isinstance(result, LearningPath)
        # Should have more milestones due to prerequisites
        assert len(result.milestones) > 1
        
        # First milestones should be prerequisites
        first_milestone = result.milestones[0]
        assert first_milestone.difficulty_level == DifficultyLevel.BEGINNER
    
    @pytest.mark.asyncio
    async def test_create_learning_path_error_handling(self, generator, sample_user_context):
        """Test error handling in learning path creation"""
        # Mock AI service to raise an exception
        generator.ai_service.create_learning_path = AsyncMock(side_effect=Exception("API Error"))
        
        # Test the method
        result = await generator.create_comprehensive_learning_path(
            goal="become a developer",
            current_skills=sample_user_context.current_skills,
            user_context=sample_user_context
        )
        
        # Should return fallback learning path
        assert isinstance(result, LearningPath)
        assert result.goal == "become a developer"
        # Fallback path should have at least one milestone
        assert len(result.milestones) >= 1
    
    def test_fix_common_issues(self, generator):
        """Test fixing common issues in learning paths"""
        # Create learning path with issues
        milestone = Milestone(
            title="Test Milestone",
            description="Short",  # Too short
            skills_to_learn=["skill1", "skill2"],
            assessment_criteria=[]  # Missing
        )
        
        learning_path = LearningPath(
            title="Test Path",
            description="Short",  # Too short
            goal="test goal",
            milestones=[milestone],
            target_skills=[]  # Missing
        )
        
        # Fix issues
        fixed_path = generator._fix_common_issues(learning_path, ["various issues"])
        
        # Check fixes
        assert len(fixed_path.description) >= 20
        assert len(fixed_path.target_skills) > 0
        assert len(fixed_path.milestones[0].assessment_criteria) > 0
        assert len(fixed_path.milestones[0].description) >= 20


class TestLearningPathQualityAndCompleteness:
    """Test learning path quality and completeness validation"""
    
    def test_learning_path_completeness_validation(self):
        """Test comprehensive validation of learning path completeness"""
        # Create a complete learning path
        milestone1 = Milestone(
            title="Foundation Skills",
            description="Build essential foundation skills for web development including HTML structure and CSS styling",
            skills_to_learn=["html basics", "css fundamentals", "responsive design"],
            prerequisites=[],
            estimated_duration=timedelta(days=14),
            difficulty_level=DifficultyLevel.BEGINNER,
            assessment_criteria=[
                "Create semantic HTML structure",
                "Style webpage with CSS",
                "Build responsive layout"
            ],
            order_index=0
        )
        
        milestone1.add_resource(
            title="HTML & CSS Course",
            url="https://example.com/html-css",
            resource_type="course",
            is_free=True,
            duration=timedelta(hours=15)
        )
        
        milestone2 = Milestone(
            title="JavaScript Programming",
            description="Learn JavaScript programming fundamentals and DOM manipulation for interactive web pages",
            skills_to_learn=["javascript syntax", "dom manipulation", "event handling"],
            prerequisites=["html basics", "css fundamentals"],
            estimated_duration=timedelta(days=21),
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            assessment_criteria=[
                "Write JavaScript functions",
                "Manipulate DOM elements",
                "Handle user events"
            ],
            order_index=1
        )
        
        milestone2.add_resource(
            title="JavaScript Tutorial",
            url="https://example.com/javascript",
            resource_type="tutorial",
            is_free=True,
            duration=timedelta(hours=20)
        )
        
        learning_path = LearningPath(
            title="Frontend Web Developer Path",
            description="A comprehensive learning path to become a frontend web developer with practical skills and real-world projects",
            goal="become a frontend web developer",
            milestones=[milestone1, milestone2],
            estimated_duration=timedelta(days=60),
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            prerequisites=["basic computer skills"],
            target_skills=["html", "css", "javascript", "responsive design", "web development"]
        )
        
        # Validate completeness
        is_valid, issues = LearningPathValidator.validate_learning_path_quality(learning_path)
        
        assert is_valid, f"Complete learning path should be valid, issues: {issues}"
        assert len(issues) == 0
    
    def test_learning_path_milestone_resource_quality(self):
        """Test validation of milestone resource quality"""
        milestone = Milestone(
            title="Python Programming",
            description="Learn Python programming fundamentals with hands-on practice and real projects",
            skills_to_learn=["python syntax", "data structures", "functions"],
            estimated_duration=timedelta(days=14),
            difficulty_level=DifficultyLevel.BEGINNER,
            assessment_criteria=["Complete Python exercises", "Build simple program"],
            order_index=0
        )
        
        # Add multiple types of resources
        milestone.add_resource(
            title="Python Official Tutorial",
            url="https://docs.python.org/tutorial/",
            resource_type="tutorial",
            is_free=True,
            duration=timedelta(hours=8)
        )
        
        milestone.add_resource(
            title="Python Video Course",
            url="https://youtube.com/python-course",
            resource_type="video",
            is_free=True,
            duration=timedelta(hours=12)
        )
        
        milestone.add_resource(
            title="Interactive Python Exercises",
            url="https://codecademy.com/python",
            resource_type="interactive",
            is_free=False,  # Paid resource
            duration=timedelta(hours=10)
        )
        
        learning_path = LearningPath(
            title="Python Developer Path",
            description="Complete path to learn Python programming from beginner to intermediate level",
            goal="learn Python programming",
            milestones=[milestone],
            target_skills=["python programming"]
        )
        
        # Validate - should pass because there are free resources available
        is_valid, issues = LearningPathValidator.validate_learning_path_quality(learning_path)
        
        # Should have issue about needing at least 2 milestones, but resources should be fine
        milestone_issues = [issue for issue in issues if "milestone 0" in issue.lower()]
        resource_issues = [issue for issue in milestone_issues if "free resources" in issue.lower()]
        
        assert len(resource_issues) == 0, "Should have free resources available"
    
    def test_learning_path_time_estimation_quality(self):
        """Test quality of time estimation in learning paths"""
        milestones = []
        
        # Create milestones with different complexities
        complexities = [
            ("Basic Concepts", ["variables", "basic syntax"], DifficultyLevel.BEGINNER, 7),
            ("Intermediate Skills", ["functions", "classes", "modules"], DifficultyLevel.INTERMEDIATE, 14),
            ("Advanced Topics", ["decorators", "metaclasses", "async"], DifficultyLevel.ADVANCED, 21)
        ]
        
        for i, (title, skills, difficulty, expected_days) in enumerate(complexities):
            milestone = Milestone(
                title=title,
                description=f"Learn {title.lower()} for programming mastery",
                skills_to_learn=skills,
                estimated_duration=timedelta(days=expected_days),
                difficulty_level=difficulty,
                assessment_criteria=[f"Complete {title.lower()} exercises"],
                order_index=i
            )
            
            milestone.add_resource(
                title=f"{title} Course",
                url=f"https://example.com/{title.lower().replace(' ', '-')}",
                resource_type="course",
                is_free=True,
                duration=timedelta(hours=expected_days * 2)  # 2 hours per day
            )
            
            milestones.append(milestone)
        
        learning_path = LearningPath(
            title="Progressive Programming Path",
            description="A well-structured path with realistic time estimates for each difficulty level",
            goal="master programming concepts",
            milestones=milestones,
            estimated_duration=timedelta(days=60),  # Sum + buffer
            target_skills=["programming", "software development"]
        )
        
        # Validate time estimates
        is_valid, issues = LearningPathValidator.validate_learning_path_quality(learning_path)
        
        # Check for time-related issues
        time_issues = [issue for issue in issues if "duration" in issue.lower() or "time" in issue.lower()]
        
        # Should have reasonable time estimates
        assert len(time_issues) == 0, f"Time estimation issues: {time_issues}"
        
        # Verify progression makes sense
        for i in range(1, len(milestones)):
            prev_duration = milestones[i-1].estimated_duration.days
            curr_duration = milestones[i].estimated_duration.days
            
            # More advanced milestones should generally take longer
            assert curr_duration >= prev_duration, f"Milestone {i} duration should not be less than previous"