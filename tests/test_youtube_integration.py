"""
Integration tests for YouTube API functionality
"""

import pytest
from unittest.mock import Mock, patch
import os
from datetime import datetime, timedelta

from edagent.services.content_recommender import ContentRecommender, YouTubeContentFilters
from edagent.config.settings import Settings


class TestYouTubeIntegration:
    """Integration tests for YouTube API functionality"""
    
    @pytest.mark.skipif(
        not os.getenv("YOUTUBE_API_KEY"), 
        reason="YouTube API key not available"
    )
    @pytest.mark.asyncio
    async def test_real_youtube_search(self):
        """Test actual YouTube API search (requires API key)"""
        # Create settings with real API key
        settings = Settings(
            youtube_api_key=os.getenv("YOUTUBE_API_KEY"),
            gemini_api_key="dummy",  # Not needed for this test
            secret_key="dummy"
        )
        
        # Create content recommender
        recommender = ContentRecommender(settings)
        
        # Skip if YouTube service couldn't be initialized
        if not recommender.youtube_service:
            pytest.skip("YouTube service not available")
        
        # Search for Python tutorials
        filters = YouTubeContentFilters(
            max_duration=3600,  # 1 hour
            min_view_count=1000,
            max_results=5
        )
        
        results = await recommender.search_youtube_content("Python programming tutorial", filters)
        
        # Verify results
        assert len(results) > 0
        assert len(results) <= 5
        
        for video in results:
            assert video.title
            assert video.url.startswith("https://www.youtube.com/watch?v=")
            assert video.video_id
            assert video.view_count >= 1000
            assert video.is_free is True
            assert "python" in video.skills_covered
    
    @pytest.mark.asyncio
    async def test_youtube_search_with_mocked_api(self):
        """Test YouTube search with mocked API responses"""
        # Mock settings
        settings = Mock(spec=Settings)
        settings.youtube_api_key = "test_key"
        
        with patch('edagent.services.content_recommender.build') as mock_build:
            # Create mock YouTube service
            mock_service = Mock()
            mock_build.return_value = mock_service
            
            # Mock search response
            mock_search_response = {
                'items': [
                    {
                        'id': {'videoId': 'abc123'},
                        'snippet': {
                            'title': 'Python Tutorial for Beginners',
                            'description': 'Learn Python programming basics',
                            'channelTitle': 'Programming Channel',
                            'channelId': 'UC123',
                            'publishedAt': '2024-01-01T10:00:00Z',
                            'thumbnails': {
                                'high': {'url': 'https://img.youtube.com/vi/abc123/hqdefault.jpg'}
                            }
                        }
                    }
                ]
            }
            
            # Mock videos response
            mock_videos_response = {
                'items': [
                    {
                        'id': 'abc123',
                        'snippet': {
                            'title': 'Python Tutorial for Beginners',
                            'description': 'Learn Python programming basics',
                            'channelTitle': 'Programming Channel',
                            'channelId': 'UC123',
                            'publishedAt': '2024-01-01T10:00:00Z',
                            'thumbnails': {
                                'high': {'url': 'https://img.youtube.com/vi/abc123/hqdefault.jpg'}
                            }
                        },
                        'statistics': {
                            'viewCount': '10000',
                            'likeCount': '500',
                            'commentCount': '50'
                        },
                        'contentDetails': {
                            'duration': 'PT15M30S',
                            'caption': 'true'
                        }
                    }
                ]
            }
            
            # Configure mocks
            mock_search = Mock()
            mock_search.list.return_value.execute.return_value = mock_search_response
            mock_service.search.return_value = mock_search
            
            mock_videos = Mock()
            mock_videos.list.return_value.execute.return_value = mock_videos_response
            mock_service.videos.return_value = mock_videos
            
            # Create recommender and test
            recommender = ContentRecommender(settings)
            filters = YouTubeContentFilters(max_results=10)
            
            results = await recommender.search_youtube_content("Python tutorial", filters)
            
            # Verify results
            assert len(results) == 1
            video = results[0]
            assert video.title == "Python Tutorial for Beginners"
            assert video.video_id == "abc123"
            assert video.view_count == 10000
            assert video.like_count == 500
            assert video.comment_count == 50
            assert video.captions_available is True
            assert video.duration == timedelta(minutes=15, seconds=30)
            assert "python" in video.skills_covered
    
    @pytest.mark.asyncio
    async def test_youtube_search_error_handling(self):
        """Test error handling in YouTube search"""
        from googleapiclient.errors import HttpError
        
        settings = Mock(spec=Settings)
        settings.youtube_api_key = "test_key"
        
        with patch('edagent.services.content_recommender.build') as mock_build:
            mock_service = Mock()
            mock_build.return_value = mock_service
            
            # Mock API error
            mock_search = Mock()
            mock_search.list.return_value.execute.side_effect = HttpError(
                resp=Mock(status=403), 
                content=b'{"error": {"code": 403, "message": "Quota exceeded"}}'
            )
            mock_service.search.return_value = mock_search
            
            recommender = ContentRecommender(settings)
            filters = YouTubeContentFilters()
            
            # Should handle error gracefully
            results = await recommender.search_youtube_content("Python tutorial", filters)
            assert results == []
    
    def test_youtube_filters_validation(self):
        """Test YouTube content filters validation"""
        # Test valid filters
        filters = YouTubeContentFilters(
            max_duration=1800,
            max_results=15,
            min_view_count=500,
            captions_required=True,
            upload_date='month'
        )
        
        assert filters.max_duration == 1800
        assert filters.max_results == 15
        assert filters.min_view_count == 500
        assert filters.captions_required is True
        assert filters.upload_date == 'month'
    
    @pytest.mark.asyncio
    async def test_content_quality_scoring(self):
        """Test content quality scoring algorithm"""
        settings = Mock(spec=Settings)
        settings.youtube_api_key = "test_key"
        
        with patch('edagent.services.content_recommender.build'):
            recommender = ContentRecommender(settings)
            
            # Test high quality video
            high_quality_score = recommender._calculate_video_quality_score(
                view_count=1000000,  # 1M views
                like_count=50000,    # 5% like ratio
                comment_count=5000,  # 0.5% comment ratio
                duration=timedelta(minutes=20)  # Optimal duration
            )
            
            # Test low quality video
            low_quality_score = recommender._calculate_video_quality_score(
                view_count=100,      # Low views
                like_count=1,        # Low engagement
                comment_count=0,     # No comments
                duration=timedelta(minutes=2)  # Too short
            )
            
            assert 0.0 <= high_quality_score <= 1.0
            assert 0.0 <= low_quality_score <= 1.0
            assert high_quality_score > low_quality_score
    
    def test_skill_extraction_accuracy(self):
        """Test accuracy of skill extraction from content"""
        settings = Mock(spec=Settings)
        settings.youtube_api_key = "test_key"
        
        with patch('edagent.services.content_recommender.build'):
            recommender = ContentRecommender(settings)
            
            # Test comprehensive skill extraction
            title = "Full Stack Web Development: Python Django + React + PostgreSQL"
            description = """
            Learn full-stack web development with Python Django backend, 
            React frontend, PostgreSQL database, and deploy to AWS.
            Includes Docker, Git, and CI/CD best practices.
            """
            
            skills = recommender._extract_skills_from_content(title, description)
            
            expected_skills = [
                'python', 'django', 'react', 'postgresql', 
                'aws', 'docker', 'git', 'web development'
            ]
            
            for skill in expected_skills:
                assert skill in skills, f"Expected skill '{skill}' not found in {skills}"