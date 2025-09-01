"""
Unit tests for content recommendation and course models
"""

import pytest
import json
from datetime import datetime, timedelta
from edagent.models.content import (
    ContentRecommendation,
    YouTubeVideo,
    Course,
    ContentType,
    Platform,
    DifficultyLevel
)


class TestContentRecommendation:
    """Test cases for ContentRecommendation model"""
    
    def test_valid_content_creation(self):
        """Test creating a valid content recommendation"""
        content = ContentRecommendation(
            title="Learn Python Basics",
            url="https://example.com/python-basics",
            platform=Platform.YOUTUBE,
            content_type=ContentType.VIDEO,
            description="A comprehensive Python tutorial",
            rating=4.5,
            is_free=True,
            difficulty_level=DifficultyLevel.BEGINNER
        )
        
        assert content.title == "Learn Python Basics"
        assert content.url == "https://example.com/python-basics"
        assert content.platform == Platform.YOUTUBE
        assert content.content_type == ContentType.VIDEO
        assert content.description == "A comprehensive Python tutorial"
        assert content.rating == 4.5
        assert content.is_free is True
        assert content.difficulty_level == DifficultyLevel.BEGINNER
        assert isinstance(content.id, str)
        assert len(content.id) > 0
    
    def test_content_with_string_enums(self):
        """Test creating content with string enum values"""
        content = ContentRecommendation(
            title="JavaScript Course",
            url="https://example.com/js",
            platform="coursera",
            content_type="course",
            difficulty_level="intermediate"
        )
        
        assert content.platform == Platform.COURSERA
        assert content.content_type == ContentType.COURSE
        assert content.difficulty_level == DifficultyLevel.INTERMEDIATE
    
    def test_invalid_title(self):
        """Test validation with invalid title"""
        with pytest.raises(ValueError, match="Content title cannot be empty"):
            ContentRecommendation(
                title="",
                url="https://example.com"
            )
    
    def test_invalid_url(self):
        """Test validation with invalid URL"""
        with pytest.raises(ValueError, match="Content URL cannot be empty"):
            ContentRecommendation(
                title="Test Content",
                url=""
            )
    
    def test_invalid_rating(self):
        """Test validation with invalid rating"""
        with pytest.raises(ValueError, match="Rating must be between 0.0 and 5.0"):
            ContentRecommendation(
                title="Test Content",
                url="https://example.com",
                rating=6.0
            )
    
    def test_invalid_price(self):
        """Test validation with invalid price"""
        with pytest.raises(ValueError, match="Price cannot be negative"):
            ContentRecommendation(
                title="Test Content",
                url="https://example.com",
                price=-10.0
            )
    
    def test_invalid_scores(self):
        """Test validation with invalid scores"""
        with pytest.raises(ValueError, match="Skill match score must be between 0.0 and 1.0"):
            ContentRecommendation(
                title="Test Content",
                url="https://example.com",
                skill_match_score=1.5
            )
    
    def test_calculate_overall_score(self):
        """Test overall score calculation"""
        content = ContentRecommendation(
            title="Test Content",
            url="https://example.com",
            rating=4.0,
            skill_match_score=0.8,
            relevance_score=0.7,
            quality_score=0.9
        )
        
        # Test with default weights
        score = content.calculate_overall_score()
        expected = 0.4 * 0.8 + 0.3 * 0.7 + 0.2 * 0.9 + 0.1 * 0.8  # rating normalized to 0.8
        assert abs(score - expected) < 0.01
        
        # Test with custom weights
        custom_weights = {"skill_match": 0.5, "relevance": 0.3, "quality": 0.2, "rating": 0.0}
        score = content.calculate_overall_score(custom_weights)
        expected = 0.5 * 0.8 + 0.3 * 0.7 + 0.2 * 0.9
        assert abs(score - expected) < 0.01
    
    def test_matches_preferences(self):
        """Test preference matching"""
        content = ContentRecommendation(
            title="Free Python Video",
            url="https://example.com",
            platform=Platform.YOUTUBE,
            content_type=ContentType.VIDEO,
            is_free=True,
            difficulty_level=DifficultyLevel.BEGINNER
        )
        
        # Test matching preferences
        preferences = {
            "budget_preference": "free",
            "content_types": ["video", "article"],
            "preferred_platforms": ["YouTube"],
            "difficulty_preference": "gradual"
        }
        
        assert content.matches_preferences(preferences) is True
        
        # Test non-matching budget
        preferences["budget_preference"] = "free"
        content.is_free = False
        assert content.matches_preferences(preferences) is False
        
        # Test non-matching content type
        content.is_free = True
        preferences["content_types"] = ["article", "book"]
        assert content.matches_preferences(preferences) is False
    
    def test_content_serialization(self):
        """Test serialization to dictionary"""
        now = datetime.now()
        duration = timedelta(hours=2, minutes=30)
        
        content = ContentRecommendation(
            id="content-123",
            title="Advanced Python",
            url="https://example.com/advanced-python",
            platform=Platform.UDEMY,
            content_type=ContentType.COURSE,
            description="Advanced Python concepts",
            duration=duration,
            rating=4.8,
            is_free=False,
            price=49.99,
            currency="USD",
            difficulty_level=DifficultyLevel.ADVANCED,
            skills_covered=["decorators", "metaclasses"],
            prerequisites=["basic python"],
            tags=["python", "advanced"],
            author="John Doe",
            published_date=now,
            skill_match_score=0.9,
            relevance_score=0.85,
            quality_score=0.95
        )
        
        data = content.to_dict()
        
        assert data["id"] == "content-123"
        assert data["title"] == "Advanced Python"
        assert data["platform"] == "udemy"
        assert data["content_type"] == "course"
        assert data["duration"] == duration.total_seconds()
        assert data["rating"] == 4.8
        assert data["is_free"] is False
        assert data["price"] == 49.99
        assert data["difficulty_level"] == "advanced"
        assert data["skills_covered"] == ["decorators", "metaclasses"]
        assert data["published_date"] == now.isoformat()
    
    def test_content_deserialization(self):
        """Test deserialization from dictionary"""
        now = datetime.now()
        data = {
            "id": "content-456",
            "title": "React Fundamentals",
            "url": "https://example.com/react",
            "platform": "other",
            "content_type": "tutorial",
            "description": "Learn React basics",
            "duration": 7200,  # 2 hours in seconds
            "rating": 4.2,
            "is_free": True,
            "price": None,
            "currency": "USD",
            "difficulty_level": "beginner",
            "skills_covered": ["jsx", "components"],
            "prerequisites": ["html", "javascript"],
            "tags": ["react", "frontend"],
            "author": "Jane Smith",
            "published_date": now.isoformat(),
            "last_updated": None,
            "skill_match_score": 0.75,
            "relevance_score": 0.8,
            "quality_score": 0.7,
            "metadata": {"source": "tutorial_site"}
        }
        
        content = ContentRecommendation.from_dict(data)
        
        assert content.id == "content-456"
        assert content.title == "React Fundamentals"
        assert content.platform == Platform.OTHER
        assert content.content_type == ContentType.TUTORIAL
        assert content.duration == timedelta(seconds=7200)
        assert content.rating == 4.2
        assert content.is_free is True
        assert content.difficulty_level == DifficultyLevel.BEGINNER
        assert content.skills_covered == ["jsx", "components"]
        assert content.published_date == now
        assert content.metadata == {"source": "tutorial_site"}


class TestYouTubeVideo:
    """Test cases for YouTubeVideo model"""
    
    def test_valid_youtube_video_creation(self):
        """Test creating a valid YouTube video"""
        video = YouTubeVideo(
            title="Python Tutorial for Beginners",
            url="https://youtube.com/watch?v=abc123",
            video_id="abc123",
            channel_name="Python Academy",
            view_count=100000,
            like_count=5000,
            comment_count=500
        )
        
        assert video.title == "Python Tutorial for Beginners"
        assert video.platform == Platform.YOUTUBE
        assert video.content_type == ContentType.VIDEO
        assert video.video_id == "abc123"
        assert video.channel_name == "Python Academy"
        assert video.view_count == 100000
        assert video.like_count == 5000
        assert video.comment_count == 500
    
    def test_invalid_video_id(self):
        """Test validation with invalid video ID"""
        with pytest.raises(ValueError, match="Video ID cannot be empty"):
            YouTubeVideo(
                title="Test Video",
                url="https://youtube.com/watch?v=",
                video_id=""
            )
    
    def test_calculate_engagement_score(self):
        """Test engagement score calculation"""
        video = YouTubeVideo(
            title="Test Video",
            url="https://youtube.com/watch?v=test",
            video_id="test",
            view_count=10000,
            like_count=500,  # 5% like ratio
            comment_count=100  # 1% comment ratio
        )
        
        engagement_score = video.calculate_engagement_score()
        expected = (0.05 * 0.6 + 0.01 * 0.4)  # Weighted engagement (no *100)
        assert abs(engagement_score - expected) < 0.01
        
        # Test with zero views
        video.view_count = 0
        assert video.calculate_engagement_score() == 0.0
    
    def test_youtube_video_serialization(self):
        """Test YouTube video serialization"""
        video = YouTubeVideo(
            title="JavaScript Basics",
            url="https://youtube.com/watch?v=xyz789",
            video_id="xyz789",
            channel_name="JS Channel",
            channel_id="UC123456",
            view_count=50000,
            like_count=2500,
            comment_count=250,
            subscriber_count=100000,
            thumbnail_url="https://img.youtube.com/vi/xyz789/maxresdefault.jpg",
            captions_available=True
        )
        
        data = video.to_dict()
        
        assert data["video_id"] == "xyz789"
        assert data["channel_name"] == "JS Channel"
        assert data["channel_id"] == "UC123456"
        assert data["view_count"] == 50000
        assert data["like_count"] == 2500
        assert data["comment_count"] == 250
        assert data["subscriber_count"] == 100000
        assert data["captions_available"] is True
        assert data["platform"] == "youtube"
        assert data["content_type"] == "video"
    
    def test_youtube_video_deserialization(self):
        """Test YouTube video deserialization"""
        data = {
            "id": "yt-123",
            "title": "CSS Grid Tutorial",
            "url": "https://youtube.com/watch?v=grid123",
            "platform": "youtube",
            "content_type": "video",
            "description": "Learn CSS Grid",
            "duration": 1800,
            "rating": 4.7,
            "is_free": True,
            "difficulty_level": "intermediate",
            "skills_covered": ["css", "grid"],
            "video_id": "grid123",
            "channel_name": "CSS Masters",
            "channel_id": "UC789012",
            "view_count": 75000,
            "like_count": 3500,
            "comment_count": 400,
            "subscriber_count": 250000,
            "thumbnail_url": "https://img.youtube.com/vi/grid123/maxresdefault.jpg",
            "captions_available": False
        }
        
        video = YouTubeVideo.from_dict(data)
        
        assert video.id == "yt-123"
        assert video.title == "CSS Grid Tutorial"
        assert video.video_id == "grid123"
        assert video.channel_name == "CSS Masters"
        assert video.view_count == 75000
        assert video.captions_available is False
        assert video.platform == Platform.YOUTUBE
        assert video.content_type == ContentType.VIDEO


class TestCourse:
    """Test cases for Course model"""
    
    def test_valid_course_creation(self):
        """Test creating a valid course"""
        course = Course(
            title="Complete Web Development Bootcamp",
            url="https://example.com/web-bootcamp",
            platform=Platform.UDEMY,
            instructor="Angela Yu",
            institution="Udemy",
            enrollment_count=500000,
            completion_rate=0.75,
            certificate_available=True
        )
        
        assert course.title == "Complete Web Development Bootcamp"
        assert course.content_type == ContentType.COURSE
        assert course.instructor == "Angela Yu"
        assert course.institution == "Udemy"
        assert course.enrollment_count == 500000
        assert course.completion_rate == 0.75
        assert course.certificate_available is True
        assert course.modules == []
        assert course.assignments == []
    
    def test_invalid_completion_rate(self):
        """Test validation with invalid completion rate"""
        with pytest.raises(ValueError, match="Completion rate must be between 0.0 and 1.0"):
            Course(
                title="Test Course",
                url="https://example.com",
                completion_rate=1.5
            )
    
    def test_add_module(self):
        """Test adding a module to course"""
        course = Course(
            title="Python Course",
            url="https://example.com/python"
        )
        
        duration = timedelta(hours=3)
        course.add_module(
            title="Introduction to Python",
            description="Learn Python basics",
            duration=duration
        )
        
        assert len(course.modules) == 1
        module = course.modules[0]
        assert module["title"] == "Introduction to Python"
        assert module["description"] == "Learn Python basics"
        assert module["duration"] == duration.total_seconds()
        assert module["order"] == 1
    
    def test_add_assignment(self):
        """Test adding an assignment to course"""
        course = Course(
            title="Data Science Course",
            url="https://example.com/data-science"
        )
        
        course.add_assignment(
            title="Build a Data Pipeline",
            description="Create an ETL pipeline using Python",
            assignment_type="project"
        )
        
        assert len(course.assignments) == 1
        assignment = course.assignments[0]
        assert assignment["title"] == "Build a Data Pipeline"
        assert assignment["description"] == "Create an ETL pipeline using Python"
        assert assignment["type"] == "project"
        assert assignment["order"] == 1
    
    def test_invalid_module_title(self):
        """Test validation with invalid module title"""
        course = Course(
            title="Test Course",
            url="https://example.com"
        )
        
        with pytest.raises(ValueError, match="Module title cannot be empty"):
            course.add_module(title="", description="Test module")
    
    def test_calculate_course_score(self):
        """Test course score calculation"""
        course = Course(
            title="Machine Learning Course",
            url="https://example.com/ml",
            rating=4.5,
            skill_match_score=0.9,
            relevance_score=0.8,
            quality_score=0.85,
            completion_rate=0.8,
            certificate_available=True
        )
        
        # Add modules and assignments for structure bonus
        course.add_module("Module 1", "Introduction")
        course.add_assignment("Assignment 1", "Practice problems")
        
        score = course.calculate_course_score()
        
        # Base score + completion bonus + certificate bonus + structure bonus
        base_score = course.calculate_overall_score()
        expected = base_score + 0.08 + 0.05 + 0.05  # bonuses
        expected = min(expected, 1.0)
        
        assert abs(score - expected) < 0.01
    
    def test_course_serialization(self):
        """Test course serialization"""
        course = Course(
            title="React Native Development",
            url="https://example.com/react-native",
            platform=Platform.COURSERA,
            instructor="Stephen Grider",
            institution="Stanford University",
            enrollment_count=25000,
            completion_rate=0.65,
            certificate_available=True
        )
        
        course.add_module("React Native Basics", "Learn the fundamentals")
        course.add_assignment("Build a Mobile App", "Create your first app", "project")
        
        data = course.to_dict()
        
        assert data["course_id"] == ""  # Default empty
        assert data["instructor"] == "Stephen Grider"
        assert data["institution"] == "Stanford University"
        assert data["enrollment_count"] == 25000
        assert data["completion_rate"] == 0.65
        assert data["certificate_available"] is True
        assert len(data["modules"]) == 1
        assert len(data["assignments"]) == 1
        assert data["content_type"] == "course"
    
    def test_course_deserialization(self):
        """Test course deserialization"""
        data = {
            "id": "course-789",
            "title": "Advanced JavaScript",
            "url": "https://example.com/advanced-js",
            "platform": "edx",
            "content_type": "course",
            "description": "Master advanced JS concepts",
            "rating": 4.6,
            "is_free": False,
            "price": 199.99,
            "difficulty_level": "advanced",
            "skills_covered": ["closures", "promises", "async/await"],
            "course_id": "ADV-JS-101",
            "instructor": "Kyle Simpson",
            "institution": "MIT",
            "enrollment_count": 15000,
            "completion_rate": 0.72,
            "certificate_available": True,
            "modules": [
                {
                    "title": "Closures Deep Dive",
                    "description": "Understanding closures",
                    "duration": 3600,
                    "order": 1
                }
            ],
            "assignments": [
                {
                    "title": "Closure Challenge",
                    "description": "Implement complex closures",
                    "type": "coding",
                    "order": 1
                }
            ]
        }
        
        course = Course.from_dict(data)
        
        assert course.id == "course-789"
        assert course.title == "Advanced JavaScript"
        assert course.platform == Platform.EDUX
        assert course.content_type == ContentType.COURSE
        assert course.course_id == "ADV-JS-101"
        assert course.instructor == "Kyle Simpson"
        assert course.institution == "MIT"
        assert course.enrollment_count == 15000
        assert course.completion_rate == 0.72
        assert course.certificate_available is True
        assert len(course.modules) == 1
        assert len(course.assignments) == 1
        assert course.modules[0]["title"] == "Closures Deep Dive"
        assert course.assignments[0]["title"] == "Closure Challenge"


if __name__ == "__main__":
    pytest.main([__file__])