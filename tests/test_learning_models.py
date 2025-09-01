"""
Unit tests for learning path and milestone models
"""

import pytest
import json
from datetime import datetime, timedelta
from edagent.models.learning import (
    Milestone,
    LearningPath,
    SkillAssessment,
    DifficultyLevel,
    MilestoneStatus
)


class TestMilestone:
    """Test cases for Milestone model"""
    
    def test_valid_milestone_creation(self):
        """Test creating a valid milestone"""
        milestone = Milestone(
            title="Learn Python Basics",
            description="Master fundamental Python concepts",
            skills_to_learn=["variables", "functions", "loops"],
            prerequisites=["basic programming"],
            estimated_duration=timedelta(weeks=2),
            difficulty_level=DifficultyLevel.BEGINNER
        )
        
        assert milestone.title == "Learn Python Basics"
        assert milestone.description == "Master fundamental Python concepts"
        assert milestone.skills_to_learn == ["variables", "functions", "loops"]
        assert milestone.prerequisites == ["basic programming"]
        assert milestone.estimated_duration == timedelta(weeks=2)
        assert milestone.difficulty_level == DifficultyLevel.BEGINNER
        assert milestone.status == MilestoneStatus.NOT_STARTED
        assert milestone.resources == []
        assert milestone.assessment_criteria == []
        assert milestone.order_index == 0
        assert isinstance(milestone.id, str)
    
    def test_milestone_with_string_enums(self):
        """Test creating milestone with string enum values"""
        milestone = Milestone(
            title="Advanced JavaScript",
            difficulty_level="advanced",
            status="in_progress"
        )
        
        assert milestone.difficulty_level == DifficultyLevel.ADVANCED
        assert milestone.status == MilestoneStatus.IN_PROGRESS
    
    def test_invalid_title(self):
        """Test validation with invalid title"""
        with pytest.raises(ValueError, match="Milestone title cannot be empty"):
            Milestone(title="")
    
    def test_invalid_difficulty_level(self):
        """Test validation with invalid difficulty level"""
        with pytest.raises(ValueError, match="Invalid difficulty level"):
            Milestone(
                title="Test Milestone",
                difficulty_level="impossible"
            )
    
    def test_add_resource(self):
        """Test adding a resource to milestone"""
        milestone = Milestone(title="Learn React")
        
        duration = timedelta(hours=3)
        milestone.add_resource(
            title="React Official Tutorial",
            url="https://reactjs.org/tutorial",
            resource_type="tutorial",
            is_free=True,
            duration=duration
        )
        
        assert len(milestone.resources) == 1
        resource = milestone.resources[0]
        assert resource["title"] == "React Official Tutorial"
        assert resource["url"] == "https://reactjs.org/tutorial"
        assert resource["type"] == "tutorial"
        assert resource["is_free"] is True
        assert resource["duration"] == duration.total_seconds()
    
    def test_invalid_resource(self):
        """Test validation with invalid resource"""
        milestone = Milestone(title="Test Milestone")
        
        with pytest.raises(ValueError, match="Resource title cannot be empty"):
            milestone.add_resource(title="", url="https://example.com", resource_type="video")
        
        with pytest.raises(ValueError, match="Resource URL cannot be empty"):
            milestone.add_resource(title="Test Resource", url="", resource_type="video")
    
    def test_milestone_status_changes(self):
        """Test milestone status change methods"""
        milestone = Milestone(title="Test Milestone")
        
        assert milestone.status == MilestoneStatus.NOT_STARTED
        
        milestone.mark_in_progress()
        assert milestone.status == MilestoneStatus.IN_PROGRESS
        
        milestone.mark_completed()
        assert milestone.status == MilestoneStatus.COMPLETED
    
    def test_milestone_serialization(self):
        """Test serialization to dictionary"""
        duration = timedelta(days=7)
        milestone = Milestone(
            id="milestone-123",
            title="Database Fundamentals",
            description="Learn SQL and database design",
            skills_to_learn=["SQL", "database design"],
            prerequisites=["basic programming"],
            estimated_duration=duration,
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            status=MilestoneStatus.IN_PROGRESS,
            assessment_criteria=["Complete SQL exercises"],
            order_index=2
        )
        
        data = milestone.to_dict()
        
        assert data["id"] == "milestone-123"
        assert data["title"] == "Database Fundamentals"
        assert data["estimated_duration"] == duration.total_seconds()
        assert data["difficulty_level"] == "intermediate"
        assert data["status"] == "in_progress"
        assert data["order_index"] == 2
    
    def test_milestone_deserialization(self):
        """Test deserialization from dictionary"""
        data = {
            "id": "milestone-456",
            "title": "Web APIs",
            "description": "Learn to build REST APIs",
            "skills_to_learn": ["REST", "HTTP", "JSON"],
            "prerequisites": ["web development basics"],
            "estimated_duration": 604800,  # 1 week in seconds
            "difficulty_level": "intermediate",
            "status": "not_started",
            "resources": [],
            "assessment_criteria": ["Build a REST API"],
            "order_index": 1
        }
        
        milestone = Milestone.from_dict(data)
        
        assert milestone.id == "milestone-456"
        assert milestone.title == "Web APIs"
        assert milestone.estimated_duration == timedelta(seconds=604800)
        assert milestone.difficulty_level == DifficultyLevel.INTERMEDIATE
        assert milestone.status == MilestoneStatus.NOT_STARTED
        assert milestone.order_index == 1


class TestLearningPath:
    """Test cases for LearningPath model"""
    
    def test_valid_learning_path_creation(self):
        """Test creating a valid learning path"""
        path = LearningPath(
            title="Full Stack Web Development",
            description="Complete web development curriculum",
            goal="Become a full stack developer",
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            prerequisites=["basic programming"],
            target_skills=["HTML", "CSS", "JavaScript", "React", "Node.js"]
        )
        
        assert path.title == "Full Stack Web Development"
        assert path.description == "Complete web development curriculum"
        assert path.goal == "Become a full stack developer"
        assert path.difficulty_level == DifficultyLevel.INTERMEDIATE
        assert path.prerequisites == ["basic programming"]
        assert path.target_skills == ["HTML", "CSS", "JavaScript", "React", "Node.js"]
        assert path.milestones == []
        assert path.estimated_duration is None
        assert isinstance(path.id, str)
        assert isinstance(path.created_at, datetime)
        assert isinstance(path.updated_at, datetime)
    
    def test_invalid_title(self):
        """Test validation with invalid title"""
        with pytest.raises(ValueError, match="Learning path title cannot be empty"):
            LearningPath(title="", goal="Test goal")
    
    def test_invalid_goal(self):
        """Test validation with invalid goal"""
        with pytest.raises(ValueError, match="Learning path goal cannot be empty"):
            LearningPath(title="Test Path", goal="")
    
    def test_add_milestone(self):
        """Test adding a milestone to learning path"""
        path = LearningPath(
            title="Python Development",
            goal="Learn Python programming"
        )
        
        milestone1 = Milestone(
            title="Python Basics",
            estimated_duration=timedelta(weeks=2)
        )
        milestone2 = Milestone(
            title="Advanced Python",
            estimated_duration=timedelta(weeks=3)
        )
        
        path.add_milestone(milestone1)
        path.add_milestone(milestone2)
        
        assert len(path.milestones) == 2
        assert path.milestones[0].order_index == 0
        assert path.milestones[1].order_index == 1
        assert path.estimated_duration == timedelta(weeks=5)
    
    def test_get_milestone_by_id(self):
        """Test getting milestone by ID"""
        path = LearningPath(title="Test Path", goal="Test goal")
        
        milestone = Milestone(id="test-123", title="Test Milestone")
        path.add_milestone(milestone)
        
        found_milestone = path.get_milestone_by_id("test-123")
        assert found_milestone is not None
        assert found_milestone.id == "test-123"
        
        # Test non-existent milestone
        assert path.get_milestone_by_id("non-existent") is None
    
    def test_get_current_milestone(self):
        """Test getting current milestone"""
        path = LearningPath(title="Test Path", goal="Test goal")
        
        # No milestones
        assert path.get_current_milestone() is None
        
        # Add milestones
        milestone1 = Milestone(title="Milestone 1", status=MilestoneStatus.COMPLETED)
        milestone2 = Milestone(title="Milestone 2", status=MilestoneStatus.NOT_STARTED)
        milestone3 = Milestone(title="Milestone 3", status=MilestoneStatus.NOT_STARTED)
        
        path.add_milestone(milestone1)
        path.add_milestone(milestone2)
        path.add_milestone(milestone3)
        
        # Should return first non-completed milestone
        current = path.get_current_milestone()
        assert current is not None
        assert current.title == "Milestone 2"
    
    def test_get_progress(self):
        """Test getting learning path progress"""
        path = LearningPath(title="Test Path", goal="Test goal")
        
        # No milestones = 0% progress
        assert path.get_progress() == 0.0
        
        # Add milestones
        milestone1 = Milestone(title="Milestone 1", status=MilestoneStatus.COMPLETED)
        milestone2 = Milestone(title="Milestone 2", status=MilestoneStatus.COMPLETED)
        milestone3 = Milestone(title="Milestone 3", status=MilestoneStatus.NOT_STARTED)
        
        path.add_milestone(milestone1)
        path.add_milestone(milestone2)
        path.add_milestone(milestone3)
        
        # 2 out of 3 completed = 66.67% progress
        progress = path.get_progress()
        assert abs(progress - 0.6667) < 0.01
    
    def test_get_completed_milestones(self):
        """Test getting completed milestones"""
        path = LearningPath(title="Test Path", goal="Test goal")
        
        milestone1 = Milestone(title="Milestone 1", status=MilestoneStatus.COMPLETED)
        milestone2 = Milestone(title="Milestone 2", status=MilestoneStatus.IN_PROGRESS)
        milestone3 = Milestone(title="Milestone 3", status=MilestoneStatus.COMPLETED)
        
        path.add_milestone(milestone1)
        path.add_milestone(milestone2)
        path.add_milestone(milestone3)
        
        completed = path.get_completed_milestones()
        assert len(completed) == 2
        assert completed[0].title == "Milestone 1"
        assert completed[1].title == "Milestone 3"
    
    def test_get_remaining_milestones(self):
        """Test getting remaining milestones"""
        path = LearningPath(title="Test Path", goal="Test goal")
        
        milestone1 = Milestone(title="Milestone 1", status=MilestoneStatus.COMPLETED)
        milestone2 = Milestone(title="Milestone 2", status=MilestoneStatus.IN_PROGRESS)
        milestone3 = Milestone(title="Milestone 3", status=MilestoneStatus.NOT_STARTED)
        
        path.add_milestone(milestone1)
        path.add_milestone(milestone2)
        path.add_milestone(milestone3)
        
        remaining = path.get_remaining_milestones()
        assert len(remaining) == 2
        assert remaining[0].title == "Milestone 2"
        assert remaining[1].title == "Milestone 3"
    
    def test_learning_path_serialization(self):
        """Test serialization to dictionary"""
        now = datetime.now()
        path = LearningPath(
            id="path-123",
            title="Data Science Path",
            description="Complete data science curriculum",
            goal="Become a data scientist",
            difficulty_level=DifficultyLevel.ADVANCED,
            prerequisites=["statistics", "programming"],
            target_skills=["Python", "pandas", "scikit-learn"],
            created_at=now,
            updated_at=now
        )
        
        milestone = Milestone(title="Python for Data Science")
        path.add_milestone(milestone)
        
        data = path.to_dict()
        
        assert data["id"] == "path-123"
        assert data["title"] == "Data Science Path"
        assert data["goal"] == "Become a data scientist"
        assert data["difficulty_level"] == "advanced"
        assert data["prerequisites"] == ["statistics", "programming"]
        assert data["target_skills"] == ["Python", "pandas", "scikit-learn"]
        assert len(data["milestones"]) == 1
        assert data["created_at"] == now.isoformat()
    
    def test_learning_path_deserialization(self):
        """Test deserialization from dictionary"""
        now = datetime.now()
        data = {
            "id": "path-456",
            "title": "Mobile Development",
            "description": "Learn mobile app development",
            "goal": "Build mobile apps",
            "milestones": [
                {
                    "id": "milestone-1",
                    "title": "React Native Basics",
                    "description": "Learn React Native",
                    "skills_to_learn": ["React Native"],
                    "prerequisites": ["React"],
                    "estimated_duration": 1209600,  # 2 weeks
                    "difficulty_level": "intermediate",
                    "status": "not_started",
                    "resources": [],
                    "assessment_criteria": [],
                    "order_index": 0
                }
            ],
            "estimated_duration": 1209600,
            "difficulty_level": "intermediate",
            "prerequisites": ["React"],
            "target_skills": ["React Native", "mobile development"],
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        path = LearningPath.from_dict(data)
        
        assert path.id == "path-456"
        assert path.title == "Mobile Development"
        assert path.goal == "Build mobile apps"
        assert path.difficulty_level == DifficultyLevel.INTERMEDIATE
        assert len(path.milestones) == 1
        assert path.milestones[0].title == "React Native Basics"
        assert path.estimated_duration == timedelta(seconds=1209600)
        assert path.created_at == now


class TestSkillAssessment:
    """Test cases for SkillAssessment model"""
    
    def test_valid_assessment_creation(self):
        """Test creating a valid skill assessment"""
        assessment = SkillAssessment(
            user_id="user123",
            skill_area="Python Programming",
            overall_level=DifficultyLevel.INTERMEDIATE,
            confidence_score=0.75
        )
        
        assert assessment.user_id == "user123"
        assert assessment.skill_area == "Python Programming"
        assert assessment.overall_level == DifficultyLevel.INTERMEDIATE
        assert assessment.confidence_score == 0.75
        assert assessment.strengths == []
        assert assessment.weaknesses == []
        assert assessment.recommendations == []
        assert assessment.detailed_scores == {}
        assert isinstance(assessment.id, str)
        assert isinstance(assessment.assessment_date, datetime)
    
    def test_invalid_user_id(self):
        """Test validation with invalid user ID"""
        with pytest.raises(ValueError, match="User ID cannot be empty"):
            SkillAssessment(
                user_id="",
                skill_area="Python"
            )
    
    def test_invalid_skill_area(self):
        """Test validation with invalid skill area"""
        with pytest.raises(ValueError, match="Skill area cannot be empty"):
            SkillAssessment(
                user_id="user123",
                skill_area=""
            )
    
    def test_invalid_confidence_score(self):
        """Test validation with invalid confidence score"""
        with pytest.raises(ValueError, match="Confidence score must be between 0.0 and 1.0"):
            SkillAssessment(
                user_id="user123",
                skill_area="Python",
                confidence_score=1.5
            )
    
    def test_add_strength(self):
        """Test adding a strength"""
        assessment = SkillAssessment(
            user_id="user123",
            skill_area="JavaScript"
        )
        
        assessment.add_strength("Good understanding of closures")
        
        assert len(assessment.strengths) == 1
        assert assessment.strengths[0] == "Good understanding of closures"
    
    def test_add_weakness(self):
        """Test adding a weakness"""
        assessment = SkillAssessment(
            user_id="user123",
            skill_area="JavaScript"
        )
        
        assessment.add_weakness("Needs work on async programming")
        
        assert len(assessment.weaknesses) == 1
        assert assessment.weaknesses[0] == "Needs work on async programming"
    
    def test_add_recommendation(self):
        """Test adding a recommendation"""
        assessment = SkillAssessment(
            user_id="user123",
            skill_area="JavaScript"
        )
        
        assessment.add_recommendation("Practice with Promise-based APIs")
        
        assert len(assessment.recommendations) == 1
        assert assessment.recommendations[0] == "Practice with Promise-based APIs"
    
    def test_set_detailed_score(self):
        """Test setting detailed scores"""
        assessment = SkillAssessment(
            user_id="user123",
            skill_area="Python"
        )
        
        assessment.set_detailed_score("syntax", 0.9)
        assessment.set_detailed_score("algorithms", 0.6)
        
        assert assessment.detailed_scores["syntax"] == 0.9
        assert assessment.detailed_scores["algorithms"] == 0.6
    
    def test_invalid_detailed_score(self):
        """Test validation with invalid detailed score"""
        assessment = SkillAssessment(
            user_id="user123",
            skill_area="Python"
        )
        
        with pytest.raises(ValueError, match="Score must be between 0.0 and 1.0"):
            assessment.set_detailed_score("syntax", 1.5)
    
    def test_assessment_serialization(self):
        """Test serialization to dictionary"""
        now = datetime.now()
        assessment = SkillAssessment(
            id="assess-123",
            user_id="user456",
            skill_area="Data Science",
            overall_level=DifficultyLevel.ADVANCED,
            confidence_score=0.85,
            assessment_date=now
        )
        
        assessment.add_strength("Strong statistical knowledge")
        assessment.add_weakness("Limited ML experience")
        assessment.add_recommendation("Take ML course")
        assessment.set_detailed_score("statistics", 0.9)
        assessment.set_detailed_score("programming", 0.8)
        
        data = assessment.to_dict()
        
        assert data["id"] == "assess-123"
        assert data["user_id"] == "user456"
        assert data["skill_area"] == "Data Science"
        assert data["overall_level"] == "advanced"
        assert data["confidence_score"] == 0.85
        assert data["strengths"] == ["Strong statistical knowledge"]
        assert data["weaknesses"] == ["Limited ML experience"]
        assert data["recommendations"] == ["Take ML course"]
        assert data["detailed_scores"] == {"statistics": 0.9, "programming": 0.8}
        assert data["assessment_date"] == now.isoformat()
    
    def test_assessment_deserialization(self):
        """Test deserialization from dictionary"""
        now = datetime.now()
        data = {
            "id": "assess-789",
            "user_id": "user789",
            "skill_area": "Web Development",
            "overall_level": "intermediate",
            "confidence_score": 0.7,
            "strengths": ["Good HTML/CSS skills"],
            "weaknesses": ["Limited JavaScript experience"],
            "recommendations": ["Practice JavaScript fundamentals"],
            "detailed_scores": {"html": 0.9, "css": 0.8, "javascript": 0.5},
            "assessment_date": now.isoformat()
        }
        
        assessment = SkillAssessment.from_dict(data)
        
        assert assessment.id == "assess-789"
        assert assessment.user_id == "user789"
        assert assessment.skill_area == "Web Development"
        assert assessment.overall_level == DifficultyLevel.INTERMEDIATE
        assert assessment.confidence_score == 0.7
        assert assessment.strengths == ["Good HTML/CSS skills"]
        assert assessment.weaknesses == ["Limited JavaScript experience"]
        assert assessment.recommendations == ["Practice JavaScript fundamentals"]
        assert assessment.detailed_scores == {"html": 0.9, "css": 0.8, "javascript": 0.5}
        assert assessment.assessment_date == now


if __name__ == "__main__":
    pytest.main([__file__])