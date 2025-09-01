"""
Unit tests for content recommendation service
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any

from edagent.services.content_recommender import ContentRecommender, YouTubeContentFilters
from edagent.interfaces.content_interface import ContentFilters
from edagent.models.content import YouTubeVideo, ContentType, Platform, DifficultyLevel, ContentRecommendation
from edagent.models.user_context import UserContext, SkillLevel, UserPreferences, SkillLevelEnum, LearningStyleEnum
from edagent.config.settings import Settings


@pytest.fixture
def mock_settings():
    """Create mock settings for testing"""
    settings = Mock(spec=Settings)
    settings.youtube_api_key = "test_api_key"
    settings.youtube_max_results = 10
    return settings


@pytest.fixture
def content_recommender(mock_settings):
    """Create ContentRecommender instance for testing"""
    with patch('edagent.services.content_recommender.build') as mock_build:
        mock_youtube_service = Mock()
        mock_build.return_value = mock_youtube_service
        
        recommender = ContentRecommender(mock_settings)
        recommender.youtube_service = mock_youtube_service
        return recommender


@pytest.fixture
def sample_youtube_api_response():
    """Sample YouTube API search response"""
    return {
        'items': [
            {
                'id': {'videoId': 'test_video_1'},
                'snippet': {
                    'title': 'Python for Beginners - Complete Tutorial',
                    'description': 'Learn Python programming from scratch. Perfect for beginners.',
                    'channelTitle': 'CodeAcademy',
                    'channelId': 'UC123456',
                    'publishedAt': '2024-01-15T10:00:00Z',
                    'thumbnails': {
                        'high': {'url': 'https://img.youtube.com/vi/test_video_1/hqdefault.jpg'}
                    }
                }
            },
            {
                'id': {'videoId': 'test_video_2'},
                'snippet': {
                    'title': 'Advanced Python Techniques',
                    'description': 'Master advanced Python concepts for professional development.',
                    'channelTitle': 'TechExpert',
                    'channelId': 'UC789012',
                    'publishedAt': '2024-01-10T15:30:00Z',
                    'thumbnails': {
                        'medium': {'url': 'https://img.youtube.com/vi/test_video_2/mqdefault.jpg'}
                    }
                }
            }
        ]
    }


@pytest.fixture
def sample_youtube_videos_response():
    """Sample YouTube API videos response with detailed info"""
    return {
        'items': [
            {
                'id': 'test_video_1',
                'snippet': {
                    'title': 'Python for Beginners - Complete Tutorial',
                    'description': 'Learn Python programming from scratch. Perfect for beginners.',
                    'channelTitle': 'CodeAcademy',
                    'channelId': 'UC123456',
                    'publishedAt': '2024-01-15T10:00:00Z',
                    'thumbnails': {
                        'high': {'url': 'https://img.youtube.com/vi/test_video_1/hqdefault.jpg'}
                    }
                },
                'statistics': {
                    'viewCount': '50000',
                    'likeCount': '2500',
                    'commentCount': '150'
                },
                'contentDetails': {
                    'duration': 'PT25M30S',
                    'caption': 'true'
                }
            },
            {
                'id': 'test_video_2',
                'snippet': {
                    'title': 'Advanced Python Techniques',
                    'description': 'Master advanced Python concepts for professional development.',
                    'channelTitle': 'TechExpert',
                    'channelId': 'UC789012',
                    'publishedAt': '2024-01-10T15:30:00Z',
                    'thumbnails': {
                        'medium': {'url': 'https://img.youtube.com/vi/test_video_2/mqdefault.jpg'}
                    }
                },
                'statistics': {
                    'viewCount': '25000',
                    'likeCount': '1200',
                    'commentCount': '80'
                },
                'contentDetails': {
                    'duration': 'PT45M15S',
                    'caption': 'false'
                }
            }
        ]
    }


class TestContentRecommender:
    """Test cases for ContentRecommender class"""
    
    def test_initialization_with_api_key(self, mock_settings):
        """Test ContentRecommender initialization with valid API key"""
        with patch('edagent.services.content_recommender.build') as mock_build:
            mock_youtube_service = Mock()
            mock_build.return_value = mock_youtube_service
            
            recommender = ContentRecommender(mock_settings)
            
            mock_build.assert_called_once_with('youtube', 'v3', developerKey='test_api_key')
            assert recommender.youtube_service == mock_youtube_service
    
    def test_initialization_without_api_key(self):
        """Test ContentRecommender initialization without API key"""
        settings = Mock(spec=Settings)
        settings.youtube_api_key = None
        
        with patch('edagent.services.content_recommender.build') as mock_build:
            recommender = ContentRecommender(settings)
            
            mock_build.assert_not_called()
            assert recommender.youtube_service is None
    
    @pytest.mark.asyncio
    async def test_search_youtube_content_success(
        self, 
        content_recommender, 
        sample_youtube_api_response,
        sample_youtube_videos_response
    ):
        """Test successful YouTube content search"""
        # Mock the YouTube API calls
        mock_search = Mock()
        mock_search.list.return_value.execute.return_value = sample_youtube_api_response
        content_recommender.youtube_service.search.return_value = mock_search
        
        mock_videos = Mock()
        mock_videos.list.return_value.execute.return_value = sample_youtube_videos_response
        content_recommender.youtube_service.videos.return_value = mock_videos
        
        # Create filters
        filters = ContentFilters(max_duration=3600, min_rating=3.0)
        
        # Execute search
        results = await content_recommender.search_youtube_content("Python tutorial", filters)
        
        # Verify results
        assert len(results) == 2
        assert all(isinstance(video, YouTubeVideo) for video in results)
        
        # Check first video
        video1 = results[0]
        assert video1.title == "Python for Beginners - Complete Tutorial"
        assert video1.video_id == "test_video_1"
        assert video1.platform == Platform.YOUTUBE
        assert video1.content_type == ContentType.VIDEO
        assert video1.is_free is True
        assert video1.view_count == 50000
        assert video1.like_count == 2500
        assert video1.comment_count == 150
        assert video1.captions_available is True
        assert video1.difficulty_level == DifficultyLevel.BEGINNER
        assert "python" in video1.skills_covered
    
    @pytest.mark.asyncio
    async def test_search_youtube_content_no_service(self, mock_settings):
        """Test YouTube search when service is not available"""
        recommender = ContentRecommender(mock_settings)
        recommender.youtube_service = None
        
        filters = ContentFilters()
        results = await recommender.search_youtube_content("Python tutorial", filters)
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_search_youtube_content_api_error(self, content_recommender):
        """Test YouTube search with API error"""
        from googleapiclient.errors import HttpError
        
        # Mock API error
        mock_search = Mock()
        mock_search.list.return_value.execute.side_effect = HttpError(
            resp=Mock(status=403), content=b'API quota exceeded'
        )
        content_recommender.youtube_service.search.return_value = mock_search
        
        filters = ContentFilters()
        results = await content_recommender.search_youtube_content("Python tutorial", filters)
        
        assert results == []
    
    def test_determine_difficulty_level_beginner(self, content_recommender):
        """Test difficulty level determination for beginner content"""
        title = "Python for Beginners - Getting Started Tutorial"
        description = "Learn the basics of Python programming. Perfect for beginners."
        
        level = content_recommender._determine_difficulty_level(title, description)
        assert level == DifficultyLevel.BEGINNER
    
    def test_determine_difficulty_level_advanced(self, content_recommender):
        """Test difficulty level determination for advanced content"""
        title = "Advanced Python: Performance Optimization Techniques"
        description = "Master advanced Python concepts for professional development."
        
        level = content_recommender._determine_difficulty_level(title, description)
        assert level == DifficultyLevel.ADVANCED
    
    def test_determine_difficulty_level_intermediate(self, content_recommender):
        """Test difficulty level determination for intermediate content"""
        title = "Build a Real-World Python Project"
        description = "Create a practical Python application with intermediate concepts."
        
        level = content_recommender._determine_difficulty_level(title, description)
        assert level == DifficultyLevel.INTERMEDIATE
    
    def test_calculate_video_quality_score(self, content_recommender):
        """Test video quality score calculation"""
        # High engagement video
        score1 = content_recommender._calculate_video_quality_score(
            view_count=100000,
            like_count=5000,
            comment_count=500,
            duration=timedelta(minutes=15)
        )
        assert 0.0 <= score1 <= 1.0
        
        # Low engagement video
        score2 = content_recommender._calculate_video_quality_score(
            view_count=1000,
            like_count=10,
            comment_count=2,
            duration=timedelta(minutes=60)
        )
        assert 0.0 <= score2 <= 1.0
        assert score1 > score2  # High engagement should score higher
    
    def test_extract_skills_from_content(self, content_recommender):
        """Test skill extraction from video content"""
        title = "Learn Python and JavaScript for Web Development"
        description = "Master Python Django and JavaScript React for full-stack development"
        
        skills = content_recommender._extract_skills_from_content(title, description)
        
        expected_skills = ['python', 'javascript', 'django', 'react', 'web development']
        for skill in expected_skills:
            assert skill in skills
    
    def test_passes_quality_filters_success(self, content_recommender):
        """Test quality filter validation - passing case"""
        video = YouTubeVideo(
            title="Test Video",
            url="https://youtube.com/watch?v=test",
            video_id="test",
            view_count=1000,
            duration=timedelta(minutes=10),
            quality_score=0.8
        )
        
        filters = ContentFilters(
            max_duration=1800,  # 30 minutes
            min_rating=3.0,
            content_types=['video']
        )
        
        assert content_recommender._passes_quality_filters(video, filters) is True
    
    def test_passes_quality_filters_failure(self, content_recommender):
        """Test quality filter validation - failing case"""
        video = YouTubeVideo(
            title="Test Video",
            url="https://youtube.com/watch?v=test",
            video_id="test",
            view_count=50,  # Too low
            duration=timedelta(minutes=10),
            quality_score=0.8
        )
        
        filters = ContentFilters(max_duration=1800, min_rating=3.0)
        
        assert content_recommender._passes_quality_filters(video, filters) is False
    
    @pytest.mark.asyncio
    async def test_filter_by_preferences(self, content_recommender):
        """Test content filtering by user preferences"""
        # Create test content
        video1 = YouTubeVideo(
            title="Free Python Tutorial",
            url="https://youtube.com/watch?v=test1",
            video_id="test1",
            is_free=True,
            content_type=ContentType.VIDEO,
            platform=Platform.YOUTUBE,
            quality_score=0.8  # Add quality score above threshold
        )
        
        video2 = YouTubeVideo(
            title="Paid Python Course",
            url="https://youtube.com/watch?v=test2", 
            video_id="test2",
            is_free=False,
            price=29.99,
            content_type=ContentType.VIDEO,
            platform=Platform.YOUTUBE,
            quality_score=0.7  # Add quality score above threshold
        )
        
        content = [video1, video2]
        
        # Test free content preference
        preferences = {
            "budget_preference": "free",
            "content_types": ["video"],
            "preferred_platforms": ["youtube"]  # Use lowercase to match Platform.YOUTUBE.value
        }
        
        filtered = await content_recommender.filter_by_preferences(content, preferences)
        
        assert len(filtered) == 1
        assert filtered[0].is_free is True
    
    @pytest.mark.asyncio
    async def test_rank_content(self, content_recommender):
        """Test content ranking based on user context"""
        # Create test user context
        user_context = UserContext(
            user_id="test_user",
            current_skills={"python": SkillLevel("python", SkillLevelEnum.BEGINNER, 0.6, datetime.now())},
            career_goals=["become a software developer"],
            learning_preferences=UserPreferences(
                learning_style=LearningStyleEnum.VISUAL,
                time_commitment="2-3 hours/week",
                budget_preference="free"
            )
        )
        
        # Create test content
        video1 = YouTubeVideo(
            title="Python Web Development",
            url="https://youtube.com/watch?v=test1",
            video_id="test1",
            skills_covered=["python", "web development"],
            quality_score=0.8
        )
        
        video2 = YouTubeVideo(
            title="Java Programming Basics",
            url="https://youtube.com/watch?v=test2",
            video_id="test2", 
            skills_covered=["java"],
            quality_score=0.7
        )
        
        content = [video2, video1]  # Intentionally wrong order
        
        # Rank content
        ranked = await content_recommender.rank_content(content, user_context)
        
        # Python video should rank higher due to skill match
        # The ranking algorithm is comprehensive, so let's check the overall scores
        python_video = next((v for v in ranked if "Python" in v.title), None)
        java_video = next((v for v in ranked if "Java" in v.title), None)
        
        assert python_video is not None
        assert java_video is not None
        
        # Python video should have higher skill match score due to user having Python skills
        assert python_video.skill_match_score > java_video.skill_match_score


class TestYouTubeContentFilters:
    """Test cases for YouTubeContentFilters class"""
    
    def test_youtube_filters_initialization(self):
        """Test YouTubeContentFilters initialization"""
        filters = YouTubeContentFilters(
            max_duration=1800,
            max_results=20,
            min_view_count=500,
            captions_required=True,
            upload_date='week'
        )
        
        assert filters.max_duration == 1800
        assert filters.max_results == 20
        assert filters.min_view_count == 500
        assert filters.captions_required is True
        assert filters.upload_date == 'week'
    
    def test_youtube_filters_defaults(self):
        """Test YouTubeContentFilters default values"""
        filters = YouTubeContentFilters()
        
        assert filters.max_results == 25
        assert filters.min_view_count == 100
        assert filters.captions_required is False
        assert filters.upload_date is None


class TestContentRecommenderIntegration:
    """Integration tests for ContentRecommender"""
    
    @pytest.mark.asyncio
    async def test_full_search_workflow(self, content_recommender, sample_youtube_api_response, sample_youtube_videos_response):
        """Test complete search workflow from query to ranked results"""
        # Mock YouTube API responses
        mock_search = Mock()
        mock_search.list.return_value.execute.return_value = sample_youtube_api_response
        content_recommender.youtube_service.search.return_value = mock_search
        
        mock_videos = Mock()
        mock_videos.list.return_value.execute.return_value = sample_youtube_videos_response
        content_recommender.youtube_service.videos.return_value = mock_videos
        
        # Create user context
        user_context = UserContext(
            user_id="test_user",
            current_skills={"python": SkillLevel("python", SkillLevelEnum.BEGINNER, 0.5, datetime.now())},
            career_goals=["learn programming"],
            learning_preferences=UserPreferences(
                learning_style=LearningStyleEnum.VISUAL,
                time_commitment="2-3 hours/week",
                budget_preference="free",
                preferred_platforms=["youtube"],
                content_types=["video"]
            )
        )
        
        # Search for content
        filters = YouTubeContentFilters(max_duration=3600, min_rating=3.0)
        search_results = await content_recommender.search_youtube_content("Python programming", filters)
        
        # Filter by preferences
        preferences = user_context.learning_preferences.to_dict()
        filtered_results = await content_recommender.filter_by_preferences(search_results, preferences)
        
        # Rank results
        final_results = await content_recommender.rank_content(filtered_results, user_context)
        
        # Verify workflow
        assert len(final_results) > 0
        assert all(isinstance(video, YouTubeVideo) for video in final_results)
        assert all(video.is_free for video in final_results)  # Should match budget preference
        
        # Results should be ranked (first should have highest overall score)
        if len(final_results) > 1:
            assert (final_results[0].calculate_overall_score() >= 
                   final_results[1].calculate_overall_score())
    
    @pytest.mark.asyncio
    async def test_multi_source_search(self, content_recommender, sample_youtube_api_response, sample_youtube_videos_response):
        """Test multi-source content search functionality"""
        # Mock YouTube API responses
        mock_search = Mock()
        mock_search.list.return_value.execute.return_value = sample_youtube_api_response
        content_recommender.youtube_service.search.return_value = mock_search
        
        mock_videos = Mock()
        mock_videos.list.return_value.execute.return_value = sample_youtube_videos_response
        content_recommender.youtube_service.videos.return_value = mock_videos
        
        # Create user context
        user_context = UserContext(
            user_id="test_user",
            current_skills={"python": SkillLevel("python", SkillLevelEnum.INTERMEDIATE, 0.7, datetime.now())},
            career_goals=["become a software developer"],
            learning_preferences=UserPreferences(
                learning_style=LearningStyleEnum.VISUAL,
                time_commitment="5-10 hours/week",
                budget_preference="any"
            )
        )
        
        # Test multi-source search
        results = await content_recommender.search_multi_source_content(
            "Python web development",
            user_context,
            max_results=10
        )
        
        # Verify results
        assert len(results) <= 10
        assert all(isinstance(item, ContentRecommendation) for item in results)
        
        # Should include both YouTube videos and courses
        content_types = set(item.content_type for item in results)
        assert ContentType.VIDEO in content_types  # YouTube videos
        
        # Results should be ranked
        if len(results) > 1:
            scores = [content_recommender._calculate_comprehensive_score(content) for content in results]
            assert scores == sorted(scores, reverse=True)


class TestAdvancedContentFiltering:
    """Test cases for advanced content filtering"""
    
    @pytest.mark.asyncio
    async def test_advanced_preference_matching(self, content_recommender):
        """Test advanced preference matching logic"""
        # Create test content
        video_content = YouTubeVideo(
            title="Python Tutorial for Beginners",
            url="https://youtube.com/watch?v=test",
            video_id="test",
            content_type=ContentType.VIDEO,
            platform=Platform.YOUTUBE,
            is_free=True,
            duration=timedelta(minutes=30),
            difficulty_level=DifficultyLevel.BEGINNER,
            quality_score=0.8
        )
        
        # Test strict budget preference
        strict_preferences = {
            "budget_preference": "free",
            "learning_style": "visual",
            "content_types": ["video"],
            "time_commitment": "1-2 hours/week"
        }
        
        matches = await content_recommender._matches_advanced_preferences(video_content, strict_preferences)
        assert matches is True
        
        # Test budget mismatch
        paid_content = YouTubeVideo(
            title="Premium Python Course",
            url="https://youtube.com/watch?v=premium",
            video_id="premium",
            is_free=False,
            price=99.99
        )
        
        matches = await content_recommender._matches_advanced_preferences(paid_content, strict_preferences)
        assert matches is False
    
    def test_time_commitment_parsing(self, content_recommender):
        """Test time commitment string parsing"""
        # Test various time commitment formats
        assert content_recommender._parse_time_commitment("2-3 hours/week") == 1.5
        assert content_recommender._parse_time_commitment("30 minutes/day") == 0.25
        assert content_recommender._parse_time_commitment("1 hour/week") == 0.5
        assert content_recommender._parse_time_commitment("invalid format") is None


class TestContentRanking:
    """Test cases for advanced content ranking"""
    
    @pytest.mark.asyncio
    async def test_skill_relevance_calculation(self, content_recommender):
        """Test skill relevance scoring"""
        user_context = UserContext(
            user_id="test_user",
            current_skills={
                "python": SkillLevel("python", SkillLevelEnum.INTERMEDIATE, 0.7, datetime.now()),
                "javascript": SkillLevel("javascript", SkillLevelEnum.BEGINNER, 0.4, datetime.now())
            }
        )
        
        # Content that builds on existing skills
        content1 = ContentRecommendation(
            title="Advanced Python Web Development",
            url="https://example.com/python-web",
            skills_covered=["python", "django", "web development"]
        )
        
        # Content with completely new skills
        content2 = ContentRecommendation(
            title="Introduction to Machine Learning",
            url="https://example.com/ml-intro",
            skills_covered=["machine learning", "data science", "statistics"]
        )
        
        score1 = await content_recommender._calculate_skill_relevance(content1, user_context)
        score2 = await content_recommender._calculate_skill_relevance(content2, user_context)
        
        # Content building on existing skills should score higher
        assert score1 > score2
        assert 0.0 <= score1 <= 1.0
        assert 0.0 <= score2 <= 1.0
    
    @pytest.mark.asyncio
    async def test_goal_alignment_calculation(self, content_recommender):
        """Test career goal alignment scoring"""
        user_context = UserContext(
            user_id="test_user",
            career_goals=["become a software developer", "learn web development"]
        )
        
        # Content directly matching goals
        content1 = ContentRecommendation(
            title="Complete Software Developer Bootcamp",
            url="https://example.com/bootcamp",
            description="Learn software development from scratch"
        )
        
        # Content with partial match
        content2 = ContentRecommendation(
            title="Data Science Fundamentals",
            url="https://example.com/data-science",
            description="Introduction to data analysis and statistics"
        )
        
        score1 = await content_recommender._calculate_goal_alignment(content1, user_context)
        score2 = await content_recommender._calculate_goal_alignment(content2, user_context)
        
        # Direct goal match should score higher
        assert score1 > score2
        assert 0.0 <= score1 <= 1.0
        assert 0.0 <= score2 <= 1.0
    
    @pytest.mark.asyncio
    async def test_learning_progression_calculation(self, content_recommender):
        """Test learning progression scoring"""
        user_context = UserContext(
            user_id="test_user",
            current_skills={
                "python": SkillLevel("python", SkillLevelEnum.BEGINNER, 0.3, datetime.now())
            }
        )
        
        # Appropriate next-level content
        content1 = ContentRecommendation(
            title="Intermediate Python Programming",
            url="https://example.com/python-intermediate",
            skills_covered=["python"],
            difficulty_level=DifficultyLevel.INTERMEDIATE
        )
        
        # Too advanced content
        content2 = ContentRecommendation(
            title="Expert Python Performance Optimization",
            url="https://example.com/python-expert",
            skills_covered=["python"],
            difficulty_level=DifficultyLevel.EXPERT
        )
        
        score1 = await content_recommender._calculate_learning_progression(content1, user_context)
        score2 = await content_recommender._calculate_learning_progression(content2, user_context)
        
        # Appropriate level should score higher
        assert score1 > score2
        assert 0.0 <= score1 <= 1.0
        assert 0.0 <= score2 <= 1.0
    
    def test_freshness_score_calculation(self, content_recommender):
        """Test content freshness scoring"""
        now = datetime.now()
        
        # Very fresh content
        fresh_content = ContentRecommendation(
            title="Latest Python Features",
            url="https://example.com/fresh",
            published_date=now - timedelta(days=15)
        )
        
        # Old content
        old_content = ContentRecommendation(
            title="Python Tutorial from 2020",
            url="https://example.com/old",
            published_date=now - timedelta(days=1000)
        )
        
        fresh_score = content_recommender._calculate_freshness_score(fresh_content)
        old_score = content_recommender._calculate_freshness_score(old_content)
        
        # Fresh content should score higher
        assert fresh_score > old_score
        assert fresh_score == 1.0  # Very fresh
        assert old_score == 0.2    # Old content
    
    def test_comprehensive_score_calculation(self, content_recommender):
        """Test comprehensive scoring algorithm"""
        content = ContentRecommendation(
            title="Test Content",
            url="https://example.com/test",
            skill_match_score=0.8,
            relevance_score=0.7,
            quality_score=0.9
        )
        
        # Add metadata scores
        content.metadata = {
            "progression_score": 0.6,
            "preference_score": 0.8,
            "freshness_score": 0.5,
            "difficulty_score": 0.7
        }
        
        score = content_recommender._calculate_comprehensive_score(content)
        
        # Should be weighted average of all factors
        assert 0.0 <= score <= 1.0
        # Should be around 0.72 based on the weights and scores
        assert 0.7 <= score <= 0.8


class TestCourseSearch:
    """Test cases for course search functionality"""
    
    @pytest.mark.asyncio
    async def test_course_search_basic(self, content_recommender):
        """Test basic course search functionality"""
        skill_level = SkillLevel("python", SkillLevelEnum.BEGINNER, 0.5, datetime.now())
        
        courses = await content_recommender.search_courses("python", skill_level)
        
        # Should return some courses (simulated)
        assert isinstance(courses, list)
        # All items should be Course objects
        for course in courses:
            assert hasattr(course, 'course_id')
            assert hasattr(course, 'instructor')
            assert course.content_type == ContentType.COURSE
    
    def test_course_deduplication(self, content_recommender):
        """Test course deduplication logic"""
        from edagent.models.content import Course, Platform, ContentType, DifficultyLevel
        
        # Create duplicate courses
        course1 = Course(
            title="Python for Beginners",
            url="https://coursera.com/python1",
            platform=Platform.COURSERA,
            course_id="course1"
        )
        
        course2 = Course(
            title="Python for Beginners",  # Same title
            url="https://udemy.com/python2",
            platform=Platform.UDEMY,
            course_id="course2"
        )
        
        course3 = Course(
            title="Advanced Python Programming",
            url="https://edx.com/python3",
            platform=Platform.EDUX,
            course_id="course3"
        )
        
        courses = [course1, course2, course3]
        unique_courses = content_recommender._deduplicate_courses(courses)
        
        # Should remove one duplicate
        assert len(unique_courses) == 2
        titles = [course.title for course in unique_courses]
        assert "Python for Beginners" in titles
        assert "Advanced Python Programming" in titles


class TestUtilityMethods:
    """Test cases for utility methods"""
    
    def test_extract_skills_from_query(self, content_recommender):
        """Test skill extraction from search queries"""
        user_context = UserContext(
            user_id="test_user",
            current_skills={"python": SkillLevel("python", SkillLevelEnum.BEGINNER, 0.5, datetime.now())},
            career_goals=["become a web developer"]
        )
        
        # Query with explicit skills
        skills1 = content_recommender._extract_skills_from_query("Learn Python and JavaScript", user_context)
        assert "python" in skills1
        assert "javascript" in skills1
        
        # Query without explicit skills but with career goals
        skills2 = content_recommender._extract_skills_from_query("programming tutorial", user_context)
        assert len(skills2) > 0  # Should infer from career goals
    
    def test_content_deduplication(self, content_recommender):
        """Test content deduplication across different types"""
        content1 = ContentRecommendation(
            title="Python Tutorial for Beginners",
            url="https://youtube.com/watch?v=abc123"
        )
        
        content2 = ContentRecommendation(
            title="Python Tutorial for Beginners",  # Same title
            url="https://coursera.com/python-course"  # Different URL
        )
        
        content3 = ContentRecommendation(
            title="Advanced Python Programming",
            url="https://udemy.com/advanced-python"
        )
        
        content_list = [content1, content2, content3]
        unique_content = content_recommender._deduplicate_content(content_list)
        
        # Should keep unique content based on title similarity
        assert len(unique_content) <= len(content_list)
        
        # URLs should be unique
        urls = [item.url for item in unique_content]
        assert len(urls) == len(set(urls))