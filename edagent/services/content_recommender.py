"""
Content recommendation service with YouTube integration
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re
import isodate

from ..config.settings import Settings
from ..interfaces.content_interface import ContentRecommenderInterface, ContentFilters
from ..models.content import ContentRecommendation, YouTubeVideo, Course, ContentType, Platform, DifficultyLevel
from ..models.user_context import UserContext, SkillLevel


logger = logging.getLogger(__name__)


class ContentRecommender(ContentRecommenderInterface):
    """Content recommendation service with multi-platform support"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.youtube_service = None
        self._initialize_youtube_service()
    
    def _initialize_youtube_service(self):
        """Initialize YouTube Data API service"""
        try:
            if self.settings.youtube_api_key:
                self.youtube_service = build(
                    'youtube', 'v3', 
                    developerKey=self.settings.youtube_api_key
                )
                logger.info("YouTube API service initialized successfully")
            else:
                logger.warning("YouTube API key not provided, YouTube search will be disabled")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube service: {e}")
            self.youtube_service = None
    
    async def search_youtube_content(self, query: str, filters: ContentFilters) -> List[YouTubeVideo]:
        """
        Search for YouTube educational content
        
        Args:
            query: Search query string
            filters: Content filtering criteria
            
        Returns:
            List of relevant YouTube videos
        """
        if not self.youtube_service:
            logger.warning("YouTube service not available")
            return []
        
        try:
            # Build search parameters
            search_params = {
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'maxResults': min(filters.max_results if hasattr(filters, 'max_results') else 25, 50),
                'order': 'relevance',
                'videoDefinition': 'any',
                'videoEmbeddable': 'true',
                'safeSearch': 'strict'
            }
            
            # Add duration filter if specified
            if filters.max_duration:
                if filters.max_duration <= 240:  # 4 minutes
                    search_params['videoDuration'] = 'short'
                elif filters.max_duration <= 1200:  # 20 minutes
                    search_params['videoDuration'] = 'medium'
                else:
                    search_params['videoDuration'] = 'long'
            
            # Execute search
            search_response = self.youtube_service.search().list(**search_params).execute()
            
            if not search_response.get('items'):
                logger.info(f"No YouTube results found for query: {query}")
                return []
            
            # Get video IDs for detailed information
            video_ids = [item['id']['videoId'] for item in search_response['items']]
            
            # Get detailed video information
            videos_response = self.youtube_service.videos().list(
                part='snippet,statistics,contentDetails',
                id=','.join(video_ids)
            ).execute()
            
            # Process videos into YouTubeVideo objects
            youtube_videos = []
            for video_data in videos_response.get('items', []):
                try:
                    video = await self._process_youtube_video(video_data)
                    if video and self._passes_quality_filters(video, filters):
                        youtube_videos.append(video)
                except Exception as e:
                    logger.warning(f"Error processing video {video_data.get('id', 'unknown')}: {e}")
                    continue
            
            # Sort by quality score
            youtube_videos.sort(key=lambda v: v.calculate_overall_score(), reverse=True)
            
            logger.info(f"Found {len(youtube_videos)} quality YouTube videos for query: {query}")
            return youtube_videos
            
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in YouTube search: {e}")
            return []
    
    async def _process_youtube_video(self, video_data: Dict[str, Any]) -> Optional[YouTubeVideo]:
        """Process raw YouTube API data into YouTubeVideo object"""
        try:
            snippet = video_data['snippet']
            statistics = video_data.get('statistics', {})
            content_details = video_data.get('contentDetails', {})
            
            # Parse duration
            duration = None
            if content_details.get('duration'):
                try:
                    duration = isodate.parse_duration(content_details['duration'])
                except Exception as e:
                    logger.warning(f"Could not parse duration {content_details['duration']}: {e}")
            
            # Parse published date
            published_date = None
            if snippet.get('publishedAt'):
                try:
                    published_date = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
                except Exception as e:
                    logger.warning(f"Could not parse published date {snippet['publishedAt']}: {e}")
            
            # Extract metrics
            view_count = int(statistics.get('viewCount', 0))
            like_count = int(statistics.get('likeCount', 0))
            comment_count = int(statistics.get('commentCount', 0))
            
            # Determine difficulty level from title and description
            difficulty_level = self._determine_difficulty_level(
                snippet.get('title', ''), 
                snippet.get('description', '')
            )
            
            # Calculate quality scores
            quality_score = self._calculate_video_quality_score(
                view_count, like_count, comment_count, duration
            )
            
            # Extract skills from title and description
            skills_covered = self._extract_skills_from_content(
                snippet.get('title', ''), 
                snippet.get('description', '')
            )
            
            # Build video URL
            video_url = f"https://www.youtube.com/watch?v={video_data['id']}"
            
            # Get thumbnail URL
            thumbnails = snippet.get('thumbnails', {})
            thumbnail_url = (
                thumbnails.get('maxres', {}).get('url') or
                thumbnails.get('high', {}).get('url') or
                thumbnails.get('medium', {}).get('url') or
                thumbnails.get('default', {}).get('url', '')
            )
            
            return YouTubeVideo(
                title=snippet.get('title', ''),
                url=video_url,
                platform=Platform.YOUTUBE,
                content_type=ContentType.VIDEO,
                description=snippet.get('description', ''),
                duration=duration,
                rating=0.0,  # YouTube doesn't provide ratings in API
                is_free=True,
                difficulty_level=difficulty_level,
                skills_covered=skills_covered,
                author=snippet.get('channelTitle', ''),
                published_date=published_date,
                quality_score=quality_score,
                video_id=video_data['id'],
                channel_name=snippet.get('channelTitle', ''),
                channel_id=snippet.get('channelId', ''),
                view_count=view_count,
                like_count=like_count,
                comment_count=comment_count,
                thumbnail_url=thumbnail_url,
                captions_available=content_details.get('caption') == 'true'
            )
            
        except Exception as e:
            logger.error(f"Error processing YouTube video data: {e}")
            return None
    
    def _determine_difficulty_level(self, title: str, description: str) -> DifficultyLevel:
        """Determine difficulty level from video title and description"""
        content = (title + " " + description).lower()
        
        # Beginner indicators
        beginner_keywords = [
            'beginner', 'basics', 'introduction', 'getting started', 'fundamentals',
            'crash course', 'tutorial', '101', 'for beginners', 'start here',
            'first steps', 'learn', 'how to'
        ]
        
        # Advanced indicators
        advanced_keywords = [
            'advanced', 'expert', 'professional', 'master', 'deep dive',
            'optimization', 'performance', 'architecture', 'best practices',
            'production', 'enterprise', 'complex'
        ]
        
        # Intermediate indicators
        intermediate_keywords = [
            'intermediate', 'next level', 'beyond basics', 'practical',
            'real world', 'project', 'build', 'create'
        ]
        
        # Count keyword matches
        beginner_score = sum(1 for keyword in beginner_keywords if keyword in content)
        advanced_score = sum(1 for keyword in advanced_keywords if keyword in content)
        intermediate_score = sum(1 for keyword in intermediate_keywords if keyword in content)
        
        # Determine level based on highest score
        if beginner_score >= advanced_score and beginner_score >= intermediate_score:
            return DifficultyLevel.BEGINNER
        elif advanced_score >= intermediate_score:
            return DifficultyLevel.ADVANCED
        else:
            return DifficultyLevel.INTERMEDIATE
    
    def _calculate_video_quality_score(
        self, 
        view_count: int, 
        like_count: int, 
        comment_count: int, 
        duration: Optional[timedelta]
    ) -> float:
        """Calculate quality score based on engagement metrics"""
        if view_count == 0:
            return 0.0
        
        # Calculate engagement ratios
        like_ratio = like_count / view_count if view_count > 0 else 0.0
        comment_ratio = comment_count / view_count if view_count > 0 else 0.0
        
        # Normalize view count (log scale)
        import math
        view_score = min(math.log10(max(view_count, 1)) / 7.0, 1.0)  # Max at 10M views
        
        # Duration score (prefer 5-30 minute videos for educational content)
        duration_score = 0.5
        if duration:
            duration_minutes = duration.total_seconds() / 60
            if 5 <= duration_minutes <= 30:
                duration_score = 1.0
            elif 2 <= duration_minutes < 5 or 30 < duration_minutes <= 60:
                duration_score = 0.8
            elif duration_minutes > 60:
                duration_score = 0.6
        
        # Combine scores
        quality_score = (
            view_score * 0.3 +
            like_ratio * 100 * 0.3 +  # Scale up like ratio
            comment_ratio * 500 * 0.2 +  # Scale up comment ratio
            duration_score * 0.2
        )
        
        return min(max(quality_score, 0.0), 1.0)
    
    def _extract_skills_from_content(self, title: str, description: str) -> List[str]:
        """Extract programming/technical skills from video content"""
        content = (title + " " + description).lower()
        
        # Common programming languages and technologies
        tech_skills = [
            'python', 'javascript', 'java', 'c++', 'c#', 'go', 'rust', 'swift',
            'html', 'css', 'react', 'vue', 'angular', 'node.js', 'express',
            'django', 'flask', 'spring', 'laravel', 'rails',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes',
            'git', 'github', 'ci/cd', 'devops', 'linux',
            'machine learning', 'ai', 'data science', 'analytics',
            'web development', 'mobile development', 'backend', 'frontend'
        ]
        
        found_skills = []
        for skill in tech_skills:
            if skill in content:
                found_skills.append(skill)
        
        return found_skills
    
    def _passes_quality_filters(self, video: YouTubeVideo, filters: ContentFilters) -> bool:
        """Check if video passes quality and preference filters"""
        # Minimum view count filter (avoid very low quality content)
        if video.view_count < 100:
            return False
        
        # Duration filter
        if filters.max_duration and video.duration:
            if video.duration.total_seconds() > filters.max_duration:
                return False
        
        # Rating filter (use quality score as proxy)
        if filters.min_rating and video.quality_score < (filters.min_rating / 5.0):
            return False
        
        # Content type filter
        if filters.content_types and 'video' not in filters.content_types:
            return False
        
        # Difficulty level filter
        if filters.difficulty_level:
            if video.difficulty_level.value != filters.difficulty_level.lower():
                return False
        
        return True
    
    async def search_courses(self, skill: str, level: SkillLevel) -> List[Course]:
        """
        Search for courses on various platforms
        
        Note: This is a placeholder implementation. In a full implementation,
        this would integrate with course platform APIs (Coursera, Udemy, etc.)
        """
        # For now, return empty list as this task focuses on YouTube search
        logger.info(f"Course search not yet implemented for skill: {skill}, level: {level}")
        return []
    
    async def filter_by_preferences(
        self, 
        content: List[ContentRecommendation], 
        preferences: Dict[str, Any]
    ) -> List[ContentRecommendation]:
        """Filter content based on user preferences"""
        filtered_content = []
        
        for item in content:
            if item.matches_preferences(preferences):
                filtered_content.append(item)
        
        return filtered_content
    
    async def rank_content(
        self, 
        content: List[ContentRecommendation], 
        user_context: UserContext
    ) -> List[ContentRecommendation]:
        """Rank content based on user context and relevance"""
        # Calculate relevance scores based on user context
        for item in content:
            # Skill match score
            skill_match = 0.0
            if item.skills_covered:
                user_skills = set(user_context.current_skills.keys())
                content_skills = set(skill.lower() for skill in item.skills_covered)
                
                # Check for skill overlap
                overlap = user_skills.intersection(content_skills)
                if overlap:
                    skill_match = len(overlap) / len(content_skills)
                
                # Bonus for learning new skills
                new_skills = content_skills - user_skills
                if new_skills:
                    skill_match += 0.2
            
            item.skill_match_score = min(skill_match, 1.0)
            
            # Relevance score based on career goals
            relevance_score = 0.5  # Base relevance
            if user_context.career_goals:
                for goal in user_context.career_goals:
                    goal_lower = goal.lower()
                    title_lower = item.title.lower()
                    desc_lower = item.description.lower()
                    
                    if goal_lower in title_lower or goal_lower in desc_lower:
                        relevance_score += 0.3
                        break
            
            item.relevance_score = min(relevance_score, 1.0)
        
        # Sort by overall score
        content.sort(key=lambda x: x.calculate_overall_score(), reverse=True)
        
        return content


# Add ContentFilters extension for YouTube-specific filters
class YouTubeContentFilters(ContentFilters):
    """Extended filters for YouTube content search"""
    
    def __init__(
        self,
        max_duration: int = None,
        is_free: bool = None,
        min_rating: float = None,
        content_types: List[str] = None,
        difficulty_level: str = None,
        max_results: int = 25,
        min_view_count: int = 100,
        captions_required: bool = False,
        upload_date: str = None  # 'hour', 'today', 'week', 'month', 'year'
    ):
        super().__init__(max_duration, is_free, min_rating, content_types, difficulty_level)
        self.max_results = max_results
        self.min_view_count = min_view_count
        self.captions_required = captions_required
        self.upload_date = upload_date