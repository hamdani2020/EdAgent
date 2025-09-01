"""
Unit tests for content recommendation service
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any

from edagent.services.content_recommender import ContentRecommender, YouTubeContentFilters
from edagent.interfaces.content_interface import ContentFilters
from edagent.models.content import YouTubeVideo, ContentType, Platform, DifficultyLevel
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
            platform=Platform.YOUTUBE
        )
        
        video2 = YouTubeVideo(
            title="Paid Python Course",
            url="https://youtube.com/watch?v=test2", 
            video_id="test2",
            is_free=False,
            price=29.99,
            content_type=ContentType.VIDEO,
            platform=Platform.YOUTUBE
        )
        
        content = [video1, video2]
        
        # Test free content preference
        preferences = {
            "budget_preference": "free",
            "content_types": ["video"],
            "preferred_platforms": ["YouTube"]
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
        assert ranked[0].title == "Python Web Development"
        assert ranked[0].skill_match_score > ranked[1].skill_match_score


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
                preferred_platforms=["YouTube"],
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