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
from ..models.user_context import UserContext, SkillLevel, SkillLevelEnum, LearningStyleEnum


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
        Search for courses on various platforms using web search
        
        Args:
            skill: Target skill name
            level: User's current skill level
            
        Returns:
            List of relevant courses from multiple platforms
        """
        try:
            # Build search queries for different platforms
            level_str = level.level.value if hasattr(level, 'level') else str(level)
            
            search_queries = [
                f"{skill} {level_str} course site:coursera.org",
                f"{skill} {level_str} tutorial site:udemy.com", 
                f"{skill} {level_str} course site:edx.org",
                f"{skill} {level_str} tutorial site:khanacademy.org",
                f"{skill} {level_str} course site:codecademy.com",
                f"free {skill} {level_str} course"
            ]
            
            courses = []
            
            # Search each platform (simulated for now - would use web search MCP in real implementation)
            for query in search_queries:
                platform_courses = await self._search_course_platform(query, skill, level_str)
                courses.extend(platform_courses)
            
            # Remove duplicates and rank by relevance
            unique_courses = self._deduplicate_courses(courses)
            ranked_courses = await self._rank_courses_by_relevance(unique_courses, skill, level_str)
            
            logger.info(f"Found {len(ranked_courses)} courses for skill: {skill}, level: {level_str}")
            return ranked_courses[:10]  # Return top 10 courses
            
        except Exception as e:
            logger.error(f"Error searching courses for {skill}: {e}")
            return []
    
    async def _search_course_platform(self, query: str, skill: str, level: str) -> List[Course]:
        """
        Search for courses on a specific platform (simulated implementation)
        
        In a real implementation, this would use web search MCP or platform APIs
        """
        # This is a simulated implementation - in reality would use web search MCP
        # or integrate with platform APIs
        
        platform_mapping = {
            "coursera.org": Platform.COURSERA,
            "udemy.com": Platform.UDEMY,
            "edx.org": Platform.EDUX,
            "khanacademy.org": Platform.KHAN_ACADEMY,
            "codecademy.com": Platform.CODECADEMY
        }
        
        # Determine platform from query
        platform = Platform.OTHER
        for domain, plat in platform_mapping.items():
            if domain in query:
                platform = plat
                break
        
        # Simulate course results based on skill and level
        simulated_courses = []
        
        if "python" in skill.lower():
            if level == "beginner":
                simulated_courses = [
                    {
                        "title": f"Python for Everybody - {platform.value.title()}",
                        "url": f"https://{platform.value}.com/python-beginners",
                        "description": "Complete Python course for beginners",
                        "is_free": platform in [Platform.KHAN_ACADEMY, Platform.CODECADEMY],
                        "rating": 4.5,
                        "duration": timedelta(hours=40),
                        "difficulty": DifficultyLevel.BEGINNER,
                        "skills": ["python", "programming basics", "data structures"]
                    }
                ]
            elif level == "intermediate":
                simulated_courses = [
                    {
                        "title": f"Intermediate Python Programming - {platform.value.title()}",
                        "url": f"https://{platform.value}.com/python-intermediate", 
                        "description": "Advanced Python concepts and real-world projects",
                        "is_free": platform == Platform.KHAN_ACADEMY,
                        "rating": 4.3,
                        "duration": timedelta(hours=60),
                        "difficulty": DifficultyLevel.INTERMEDIATE,
                        "skills": ["python", "oop", "web development", "apis"]
                    }
                ]
        
        # Convert to Course objects
        courses = []
        for course_data in simulated_courses:
            course = Course(
                title=course_data["title"],
                url=course_data["url"],
                platform=platform,
                description=course_data["description"],
                duration=course_data["duration"],
                rating=course_data["rating"],
                is_free=course_data["is_free"],
                difficulty_level=course_data["difficulty"],
                skills_covered=course_data["skills"],
                course_id=f"{platform.value}_{skill}_{level}",
                instructor="Expert Instructor",
                institution=platform.value.title()
            )
            courses.append(course)
        
        return courses
    
    def _deduplicate_courses(self, courses: List[Course]) -> List[Course]:
        """Remove duplicate courses based on title similarity"""
        unique_courses = []
        seen_titles = set()
        
        for course in courses:
            # Simple deduplication based on normalized title
            normalized_title = course.title.lower().strip()
            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_courses.append(course)
        
        return unique_courses
    
    async def _rank_courses_by_relevance(self, courses: List[Course], skill: str, level: str) -> List[Course]:
        """Rank courses by relevance to skill and level"""
        for course in courses:
            relevance_score = 0.0
            
            # Skill match in title and description
            skill_lower = skill.lower()
            title_lower = course.title.lower()
            desc_lower = course.description.lower()
            
            if skill_lower in title_lower:
                relevance_score += 0.4
            if skill_lower in desc_lower:
                relevance_score += 0.2
            
            # Level match
            if level.lower() in title_lower or level.lower() in desc_lower:
                relevance_score += 0.3
            
            # Rating bonus
            relevance_score += (course.rating / 5.0) * 0.1
            
            course.relevance_score = min(relevance_score, 1.0)
        
        # Sort by relevance score
        courses.sort(key=lambda c: c.relevance_score, reverse=True)
        return courses
    
    async def filter_by_preferences(
        self, 
        content: List[ContentRecommendation], 
        preferences: Dict[str, Any]
    ) -> List[ContentRecommendation]:
        """
        Advanced content filtering based on user preferences
        
        Args:
            content: List of content recommendations
            preferences: User preference dictionary
            
        Returns:
            Filtered list of content recommendations
        """
        filtered_content = []
        
        for item in content:
            if await self._matches_advanced_preferences(item, preferences):
                filtered_content.append(item)
        
        return filtered_content
    
    async def _matches_advanced_preferences(
        self, 
        content: ContentRecommendation, 
        preferences: Dict[str, Any]
    ) -> bool:
        """
        Advanced preference matching with weighted criteria
        
        Args:
            content: Content item to evaluate
            preferences: User preferences dictionary
            
        Returns:
            True if content matches user preferences
        """
        # Budget preference (strict filter)
        budget_pref = preferences.get("budget_preference", "free")
        if budget_pref == "free" and not content.is_free:
            return False
        elif budget_pref == "low_cost" and content.price and content.price > 50:
            return False
        
        # Content type preference
        preferred_types = preferences.get("content_types", [])
        if preferred_types and content.content_type.value not in preferred_types:
            return False
        
        # Platform preference
        preferred_platforms = preferences.get("preferred_platforms", [])
        if preferred_platforms:
            platform_match = any(
                platform.lower() == content.platform.value.lower() or
                platform.lower() in content.platform.value.lower()
                for platform in preferred_platforms
            )
            if not platform_match:
                return False
        
        # Learning style preference
        learning_style = preferences.get("learning_style", "")
        if learning_style:
            if learning_style == "visual" and content.content_type not in [ContentType.VIDEO, ContentType.INTERACTIVE]:
                # Reduce preference but don't exclude
                pass
            elif learning_style == "auditory" and content.content_type not in [ContentType.VIDEO, ContentType.PODCAST]:
                pass
            elif learning_style == "reading" and content.content_type not in [ContentType.ARTICLE, ContentType.BOOK]:
                pass
        
        # Time commitment filter
        time_commitment = preferences.get("time_commitment", "")
        if time_commitment and content.duration:
            # Parse time commitment (e.g., "2-3 hours/week")
            max_session_time = self._parse_time_commitment(time_commitment)
            if max_session_time and content.duration.total_seconds() > max_session_time * 3600:
                # Allow longer content but reduce score later
                pass
        
        # Difficulty preference
        difficulty_pref = preferences.get("difficulty_preference", "gradual")
        if difficulty_pref == "gradual" and content.difficulty_level == DifficultyLevel.EXPERT:
            return False
        elif difficulty_pref == "challenging" and content.difficulty_level == DifficultyLevel.BEGINNER:
            # Reduce preference but don't exclude completely
            pass
        
        # Quality threshold
        min_quality = preferences.get("min_quality_score", 0.3)
        if content.quality_score < min_quality:
            return False
        
        return True
    
    def _parse_time_commitment(self, time_commitment: str) -> Optional[float]:
        """
        Parse time commitment string to extract maximum session hours
        
        Args:
            time_commitment: String like "2-3 hours/week" or "30 minutes/day"
            
        Returns:
            Maximum hours per session, or None if cannot parse
        """
        try:
            import re
            
            # Extract numbers and time units
            pattern = r'(\d+(?:\.\d+)?)\s*(?:-\s*(\d+(?:\.\d+)?))?\s*(hours?|minutes?|mins?)'
            match = re.search(pattern, time_commitment.lower())
            
            if match:
                min_time = float(match.group(1))
                max_time = float(match.group(2)) if match.group(2) else min_time
                unit = match.group(3)
                
                # Convert to hours
                if 'min' in unit:
                    max_time = max_time / 60
                
                # Assume 2-3 sessions per week, so divide by 2
                return max_time / 2
            
            return None
        except Exception:
            return None
    
    async def rank_content(
        self, 
        content: List[ContentRecommendation], 
        user_context: UserContext
    ) -> List[ContentRecommendation]:
        """
        Advanced content ranking based on user context and multiple factors
        
        Args:
            content: List of content recommendations
            user_context: Current user context with skills, goals, and preferences
            
        Returns:
            Ranked list of content recommendations
        """
        # Calculate comprehensive scores for each content item
        for item in content:
            # 1. Skill relevance score
            item.skill_match_score = await self._calculate_skill_relevance(item, user_context)
            
            # 2. Career goal alignment score
            item.relevance_score = await self._calculate_goal_alignment(item, user_context)
            
            # 3. Learning progression score
            progression_score = await self._calculate_learning_progression(item, user_context)
            
            # 4. Preference alignment score
            preference_score = await self._calculate_preference_alignment(item, user_context)
            
            # 5. Content freshness score
            freshness_score = self._calculate_freshness_score(item)
            
            # 6. Difficulty appropriateness score
            difficulty_score = await self._calculate_difficulty_appropriateness(item, user_context)
            
            # Store additional scores in metadata for debugging
            item.metadata.update({
                "progression_score": progression_score,
                "preference_score": preference_score,
                "freshness_score": freshness_score,
                "difficulty_score": difficulty_score
            })
        
        # Sort by comprehensive weighted score
        content.sort(key=lambda x: self._calculate_comprehensive_score(x), reverse=True)
        
        return content
    
    async def _calculate_skill_relevance(
        self, 
        content: ContentRecommendation, 
        user_context: UserContext
    ) -> float:
        """Calculate how relevant content is to user's current skills"""
        if not content.skills_covered:
            return 0.3  # Base score for content without explicit skills
        
        user_skills = set(skill.lower() for skill in user_context.current_skills.keys())
        content_skills = set(skill.lower() for skill in content.skills_covered)
        
        if not user_skills:
            return 0.5  # Neutral score for new users
        
        # Calculate skill overlap
        overlap = user_skills.intersection(content_skills)
        overlap_ratio = len(overlap) / len(content_skills) if content_skills else 0
        
        # Calculate new skills being taught
        new_skills = content_skills - user_skills
        new_skill_ratio = len(new_skills) / len(content_skills) if content_skills else 0
        
        # Weighted combination: some overlap is good, but new skills are valuable
        skill_score = (overlap_ratio * 0.4) + (new_skill_ratio * 0.6)
        
        # Bonus for building on existing skills
        if overlap and new_skills:
            skill_score += 0.2
        
        return min(skill_score, 1.0)
    
    async def _calculate_goal_alignment(
        self, 
        content: ContentRecommendation, 
        user_context: UserContext
    ) -> float:
        """Calculate alignment with user's career goals"""
        if not user_context.career_goals:
            return 0.5  # Neutral score if no goals specified
        
        title_lower = content.title.lower()
        desc_lower = content.description.lower()
        content_text = f"{title_lower} {desc_lower}"
        
        max_alignment = 0.0
        
        for goal in user_context.career_goals:
            goal_lower = goal.lower()
            goal_words = goal_lower.split()
            
            # Direct goal mention
            if goal_lower in content_text:
                max_alignment = max(max_alignment, 0.9)
                continue
            
            # Partial word matches
            word_matches = sum(1 for word in goal_words if word in content_text)
            word_score = word_matches / len(goal_words) if goal_words else 0
            max_alignment = max(max_alignment, word_score * 0.7)
            
            # Semantic matching for common career goals
            semantic_score = self._calculate_semantic_goal_match(goal_lower, content_text)
            max_alignment = max(max_alignment, semantic_score)
        
        return min(max_alignment, 1.0)
    
    def _calculate_semantic_goal_match(self, goal: str, content_text: str) -> float:
        """Calculate semantic matching for career goals"""
        # Define semantic mappings for common career goals
        goal_mappings = {
            "software developer": ["programming", "coding", "development", "software", "web dev", "app dev"],
            "data scientist": ["data", "analytics", "machine learning", "statistics", "python", "r"],
            "web developer": ["html", "css", "javascript", "react", "vue", "angular", "web"],
            "mobile developer": ["android", "ios", "swift", "kotlin", "react native", "flutter"],
            "devops engineer": ["docker", "kubernetes", "ci/cd", "aws", "azure", "deployment"],
            "ai engineer": ["artificial intelligence", "machine learning", "deep learning", "neural networks"]
        }
        
        related_terms = goal_mappings.get(goal, [])
        if not related_terms:
            return 0.0
        
        matches = sum(1 for term in related_terms if term in content_text)
        return (matches / len(related_terms)) * 0.6  # Max 0.6 for semantic matches
    
    async def _calculate_learning_progression(
        self, 
        content: ContentRecommendation, 
        user_context: UserContext
    ) -> float:
        """Calculate how well content fits user's learning progression"""
        if not content.skills_covered:
            return 0.5
        
        progression_score = 0.0
        skill_count = 0
        
        for skill in content.skills_covered:
            skill_lower = skill.lower()
            user_skill = user_context.current_skills.get(skill_lower)
            
            if user_skill:
                # Content should be slightly above current level
                user_level = user_skill.level
                content_level = content.difficulty_level
                
                if user_level == SkillLevelEnum.BEGINNER:
                    if content_level in [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE]:
                        progression_score += 0.8
                    else:
                        progression_score += 0.3
                elif user_level == SkillLevelEnum.INTERMEDIATE:
                    if content_level in [DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED]:
                        progression_score += 0.8
                    elif content_level == DifficultyLevel.BEGINNER:
                        progression_score += 0.4  # Review content
                    else:
                        progression_score += 0.3
                elif user_level == SkillLevelEnum.ADVANCED:
                    if content_level in [DifficultyLevel.ADVANCED, DifficultyLevel.EXPERT]:
                        progression_score += 0.8
                    else:
                        progression_score += 0.2
                
                skill_count += 1
            else:
                # New skill - prefer beginner content
                if content.difficulty_level == DifficultyLevel.BEGINNER:
                    progression_score += 0.9
                elif content.difficulty_level == DifficultyLevel.INTERMEDIATE:
                    progression_score += 0.6
                else:
                    progression_score += 0.2
                
                skill_count += 1
        
        return progression_score / skill_count if skill_count > 0 else 0.5
    
    async def _calculate_preference_alignment(
        self, 
        content: ContentRecommendation, 
        user_context: UserContext
    ) -> float:
        """Calculate alignment with user's learning preferences"""
        if not user_context.learning_preferences:
            return 0.5
        
        prefs = user_context.learning_preferences
        alignment_score = 0.0
        
        # Learning style alignment
        if prefs.learning_style == LearningStyleEnum.VISUAL:
            if content.content_type in [ContentType.VIDEO, ContentType.INTERACTIVE]:
                alignment_score += 0.3
        elif prefs.learning_style == LearningStyleEnum.AUDITORY:
            if content.content_type in [ContentType.VIDEO, ContentType.PODCAST]:
                alignment_score += 0.3
        elif prefs.learning_style == LearningStyleEnum.READING:
            if content.content_type in [ContentType.ARTICLE, ContentType.BOOK, ContentType.DOCUMENTATION]:
                alignment_score += 0.3
        
        # Platform preference
        if prefs.preferred_platforms:
            platform_matches = any(
                p.lower() == content.platform.value.lower() or
                p.lower() in content.platform.value.lower()
                for p in prefs.preferred_platforms
            )
            if platform_matches:
                alignment_score += 0.2
        
        # Content type preference
        if content.content_type.value in prefs.content_types:
            alignment_score += 0.2
        
        # Budget alignment
        if prefs.budget_preference == "free" and content.is_free:
            alignment_score += 0.2
        elif prefs.budget_preference == "low_cost" and (content.is_free or (content.price and content.price <= 50)):
            alignment_score += 0.2
        elif prefs.budget_preference == "any":
            alignment_score += 0.1
        
        # Time commitment alignment
        if content.duration:
            max_session_time = self._parse_time_commitment(prefs.time_commitment)
            if max_session_time:
                duration_hours = content.duration.total_seconds() / 3600
                if duration_hours <= max_session_time:
                    alignment_score += 0.1
                elif duration_hours <= max_session_time * 2:
                    alignment_score += 0.05  # Slightly longer is okay
        
        return min(alignment_score, 1.0)
    
    def _calculate_freshness_score(self, content: ContentRecommendation) -> float:
        """Calculate content freshness score based on publication date"""
        if not content.published_date:
            return 0.5  # Neutral score for unknown dates
        
        now = datetime.now()
        # Handle timezone-aware vs naive datetime comparison
        if content.published_date.tzinfo is not None and now.tzinfo is None:
            # Convert naive datetime to UTC for comparison
            from datetime import timezone
            now = now.replace(tzinfo=timezone.utc)
        elif content.published_date.tzinfo is None and now.tzinfo is not None:
            # Make published_date timezone-aware
            from datetime import timezone
            content.published_date = content.published_date.replace(tzinfo=timezone.utc)
        
        age = now - content.published_date
        
        # Fresher content gets higher scores
        if age.days <= 30:  # Very fresh
            return 1.0
        elif age.days <= 180:  # Recent
            return 0.8
        elif age.days <= 365:  # Within a year
            return 0.6
        elif age.days <= 730:  # Within two years
            return 0.4
        else:  # Older content
            return 0.2
    
    async def _calculate_difficulty_appropriateness(
        self, 
        content: ContentRecommendation, 
        user_context: UserContext
    ) -> float:
        """Calculate how appropriate the content difficulty is for the user"""
        if not content.skills_covered:
            return 0.5
        
        # Get user's average skill level for relevant skills
        relevant_skills = []
        for skill in content.skills_covered:
            skill_lower = skill.lower()
            if skill_lower in user_context.current_skills:
                relevant_skills.append(user_context.current_skills[skill_lower])
        
        if not relevant_skills:
            # New skills - prefer beginner content
            if content.difficulty_level == DifficultyLevel.BEGINNER:
                return 0.9
            elif content.difficulty_level == DifficultyLevel.INTERMEDIATE:
                return 0.5
            else:
                return 0.2
        
        # Calculate average skill level
        avg_confidence = sum(skill.confidence_score for skill in relevant_skills) / len(relevant_skills)
        
        # Map confidence to difficulty appropriateness
        if avg_confidence < 0.4:  # Low confidence - prefer easier content
            difficulty_scores = {
                DifficultyLevel.BEGINNER: 0.9,
                DifficultyLevel.INTERMEDIATE: 0.6,
                DifficultyLevel.ADVANCED: 0.3,
                DifficultyLevel.EXPERT: 0.1
            }
        elif avg_confidence < 0.7:  # Medium confidence
            difficulty_scores = {
                DifficultyLevel.BEGINNER: 0.6,
                DifficultyLevel.INTERMEDIATE: 0.9,
                DifficultyLevel.ADVANCED: 0.7,
                DifficultyLevel.EXPERT: 0.3
            }
        else:  # High confidence - can handle advanced content
            difficulty_scores = {
                DifficultyLevel.BEGINNER: 0.3,
                DifficultyLevel.INTERMEDIATE: 0.6,
                DifficultyLevel.ADVANCED: 0.9,
                DifficultyLevel.EXPERT: 0.8
            }
        
        return difficulty_scores.get(content.difficulty_level, 0.5)
    
    def _calculate_comprehensive_score(self, content: ContentRecommendation) -> float:
        """Calculate final comprehensive score with weighted factors"""
        # Define weights for different factors
        weights = {
            "skill_match": 0.25,
            "relevance": 0.20,
            "quality": 0.15,
            "progression": 0.15,
            "preference": 0.10,
            "difficulty": 0.10,
            "freshness": 0.05
        }
        
        # Get scores from metadata
        progression_score = content.metadata.get("progression_score", 0.5)
        preference_score = content.metadata.get("preference_score", 0.5)
        freshness_score = content.metadata.get("freshness_score", 0.5)
        difficulty_score = content.metadata.get("difficulty_score", 0.5)
        
        # Calculate weighted score
        comprehensive_score = (
            weights["skill_match"] * content.skill_match_score +
            weights["relevance"] * content.relevance_score +
            weights["quality"] * content.quality_score +
            weights["progression"] * progression_score +
            weights["preference"] * preference_score +
            weights["difficulty"] * difficulty_score +
            weights["freshness"] * freshness_score
        )
        
        return min(max(comprehensive_score, 0.0), 1.0)
    
    async def search_multi_source_content(
        self,
        query: str,
        user_context: UserContext,
        filters: Optional[ContentFilters] = None,
        max_results: int = 20
    ) -> List[ContentRecommendation]:
        """
        Search for content across multiple sources (YouTube, courses, etc.)
        
        Args:
            query: Search query string
            user_context: User context for personalization
            filters: Content filtering criteria
            max_results: Maximum number of results to return
            
        Returns:
            Ranked list of content recommendations from all sources
        """
        if filters is None:
            filters = ContentFilters()
        
        all_content = []
        
        try:
            # Search YouTube content
            youtube_filters = YouTubeContentFilters(
                max_duration=filters.max_duration,
                is_free=filters.is_free,
                min_rating=filters.min_rating,
                content_types=filters.content_types,
                difficulty_level=filters.difficulty_level,
                max_results=max_results // 2  # Split results between sources
            )
            
            youtube_content = await self.search_youtube_content(query, youtube_filters)
            all_content.extend(youtube_content)
            
            # Search courses for each skill mentioned in query or user context
            skills_to_search = self._extract_skills_from_query(query, user_context)
            
            for skill in skills_to_search[:3]:  # Limit to top 3 skills to avoid too many API calls
                # Determine appropriate skill level for search
                user_skill = user_context.current_skills.get(skill.lower())
                if user_skill:
                    skill_level = user_skill
                else:
                    # Default to beginner for new skills
                    skill_level = SkillLevel(skill, SkillLevelEnum.BEGINNER, 0.0, datetime.now())
                
                course_content = await self.search_courses(skill, skill_level)
                all_content.extend(course_content)
            
            # Remove duplicates based on URL
            unique_content = self._deduplicate_content(all_content)
            
            # Apply preference filtering
            if user_context.learning_preferences:
                preferences = user_context.learning_preferences.to_dict()
                filtered_content = await self.filter_by_preferences(unique_content, preferences)
            else:
                filtered_content = unique_content
            
            # Rank all content together
            ranked_content = await self.rank_content(filtered_content, user_context)
            
            # Return top results
            final_results = ranked_content[:max_results]
            
            logger.info(f"Multi-source search for '{query}' returned {len(final_results)} results")
            return final_results
            
        except Exception as e:
            logger.error(f"Error in multi-source content search: {e}")
            return []
    
    def _extract_skills_from_query(self, query: str, user_context: UserContext) -> List[str]:
        """Extract relevant skills from search query and user context"""
        query_lower = query.lower()
        
        # Common programming and technical skills
        all_skills = [
            'python', 'javascript', 'java', 'c++', 'c#', 'go', 'rust', 'swift',
            'html', 'css', 'react', 'vue', 'angular', 'node.js', 'express',
            'django', 'flask', 'spring', 'laravel', 'rails',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes',
            'git', 'github', 'ci/cd', 'devops', 'linux',
            'machine learning', 'ai', 'data science', 'analytics',
            'web development', 'mobile development', 'backend', 'frontend'
        ]
        
        # Find skills mentioned in query
        query_skills = [skill for skill in all_skills if skill in query_lower]
        
        # Add user's current skills if relevant to query
        user_skills = list(user_context.current_skills.keys())
        
        # Combine and prioritize
        combined_skills = list(set(query_skills + user_skills))
        
        # If no specific skills found, infer from career goals
        if not combined_skills and user_context.career_goals:
            for goal in user_context.career_goals:
                goal_lower = goal.lower()
                if 'developer' in goal_lower or 'programming' in goal_lower:
                    combined_skills.extend(['python', 'javascript', 'web development'])
                elif 'data' in goal_lower:
                    combined_skills.extend(['python', 'sql', 'data science'])
                elif 'devops' in goal_lower:
                    combined_skills.extend(['docker', 'kubernetes', 'aws'])
        
        # Return unique skills, prioritizing query skills
        result = []
        for skill in query_skills:
            if skill not in result:
                result.append(skill)
        for skill in combined_skills:
            if skill not in result:
                result.append(skill)
        
        return result[:5]  # Limit to top 5 skills
    
    def _deduplicate_content(self, content: List[ContentRecommendation]) -> List[ContentRecommendation]:
        """Remove duplicate content based on URL and title similarity"""
        unique_content = []
        seen_urls = set()
        seen_titles = set()
        
        for item in content:
            # Check URL duplication
            if item.url in seen_urls:
                continue
            
            # Check title similarity (simple approach)
            normalized_title = item.title.lower().strip()
            title_words = set(normalized_title.split())
            
            is_duplicate = False
            for seen_title in seen_titles:
                seen_words = set(seen_title.split())
                # If 80% of words overlap, consider it a duplicate
                if len(title_words.intersection(seen_words)) / len(title_words.union(seen_words)) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_urls.add(item.url)
                seen_titles.add(normalized_title)
                unique_content.append(item)
        
        return unique_content


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