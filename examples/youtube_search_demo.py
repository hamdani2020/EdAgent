#!/usr/bin/env python3
"""
Demo script for YouTube content search functionality
"""

import asyncio
import os
from datetime import datetime
from edagent.services.content_recommender import ContentRecommender, YouTubeContentFilters
from edagent.models.user_context import UserContext, SkillLevel, UserPreferences, SkillLevelEnum, LearningStyleEnum
from edagent.config.settings import Settings


async def demo_youtube_search():
    """Demonstrate YouTube content search functionality"""
    
    # Check if API key is available
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        print("⚠️  YouTube API key not found in environment variables")
        print("   Set YOUTUBE_API_KEY to test with real YouTube API")
        print("   Continuing with mock demonstration...\n")
        
        # Use mock settings for demo
        settings = Settings(
            youtube_api_key="demo_key",
            gemini_api_key="demo_key", 
            secret_key="demo_key"
        )
    else:
        settings = Settings(
            youtube_api_key=api_key,
            gemini_api_key="demo_key",
            secret_key="demo_key"
        )
    
    # Create content recommender
    print("🔧 Initializing Content Recommender...")
    recommender = ContentRecommender(settings)
    
    if not recommender.youtube_service and api_key:
        print("❌ Failed to initialize YouTube service")
        return
    
    # Create sample user context
    print("👤 Creating sample user context...")
    user_context = UserContext(
        user_id="demo_user",
        current_skills={
            "python": SkillLevel("python", SkillLevelEnum.BEGINNER, 0.6, datetime.now())
        },
        career_goals=["become a software developer", "learn web development"],
        learning_preferences=UserPreferences(
            learning_style=LearningStyleEnum.VISUAL,
            time_commitment="3-5 hours/week",
            budget_preference="free",
            preferred_platforms=["YouTube"],
            content_types=["video"],
            difficulty_preference="gradual"
        )
    )
    
    # Create search filters
    print("🔍 Setting up search filters...")
    filters = YouTubeContentFilters(
        max_duration=2400,  # 40 minutes
        min_view_count=1000,
        max_results=5,
        captions_required=False
    )
    
    # Search for Python content
    search_queries = [
        "Python programming for beginners",
        "Web development with Python",
        "Python data structures tutorial"
    ]
    
    for query in search_queries:
        print(f"\n🔎 Searching for: '{query}'")
        print("-" * 50)
        
        try:
            # Search YouTube content
            if api_key and recommender.youtube_service:
                results = await recommender.search_youtube_content(query, filters)
            else:
                # Mock results for demo
                results = await create_mock_results(query)
            
            if not results:
                print("   No results found")
                continue
            
            # Filter by user preferences
            preferences = user_context.learning_preferences.to_dict()
            filtered_results = await recommender.filter_by_preferences(results, preferences)
            
            # Rank results based on user context
            ranked_results = await recommender.rank_content(filtered_results, user_context)
            
            # Display results
            print(f"   Found {len(ranked_results)} relevant videos:")
            
            for i, video in enumerate(ranked_results[:3], 1):
                print(f"\n   {i}. {video.title}")
                print(f"      📺 Channel: {video.channel_name}")
                print(f"      ⏱️  Duration: {format_duration(video.duration)}")
                print(f"      👀 Views: {video.view_count:,}")
                print(f"      👍 Likes: {video.like_count:,}")
                print(f"      📊 Quality Score: {video.quality_score:.2f}")
                print(f"      🎯 Skill Match: {video.skill_match_score:.2f}")
                print(f"      🔗 URL: {video.url}")
                
                if video.skills_covered:
                    print(f"      🛠️  Skills: {', '.join(video.skills_covered[:5])}")
        
        except Exception as e:
            print(f"   ❌ Error searching for '{query}': {e}")
    
    print("\n✅ Demo completed!")


async def create_mock_results(query):
    """Create mock YouTube results for demo purposes"""
    from edagent.models.content import YouTubeVideo, Platform, ContentType, DifficultyLevel
    from datetime import timedelta
    
    mock_videos = [
        YouTubeVideo(
            title=f"Complete {query.split()[0]} Tutorial for Beginners",
            url="https://youtube.com/watch?v=demo1",
            video_id="demo1",
            channel_name="CodeAcademy",
            channel_id="UC_demo1",
            description=f"Learn {query.split()[0]} programming from scratch",
            duration=timedelta(minutes=25),
            view_count=45000,
            like_count=2200,
            comment_count=180,
            quality_score=0.85,
            skills_covered=[query.split()[0].lower(), "programming"],
            difficulty_level=DifficultyLevel.BEGINNER,
            captions_available=True
        ),
        YouTubeVideo(
            title=f"Advanced {query.split()[0]} Concepts Explained",
            url="https://youtube.com/watch?v=demo2",
            video_id="demo2",
            channel_name="TechExpert",
            channel_id="UC_demo2",
            description=f"Master advanced {query.split()[0]} techniques",
            duration=timedelta(minutes=35),
            view_count=28000,
            like_count=1400,
            comment_count=95,
            quality_score=0.78,
            skills_covered=[query.split()[0].lower(), "advanced programming"],
            difficulty_level=DifficultyLevel.ADVANCED,
            captions_available=False
        )
    ]
    
    return mock_videos


def format_duration(duration):
    """Format duration for display"""
    if not duration:
        return "Unknown"
    
    total_seconds = int(duration.total_seconds())
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    
    if minutes >= 60:
        hours = minutes // 60
        minutes = minutes % 60
        return f"{hours}h {minutes}m {seconds}s"
    else:
        return f"{minutes}m {seconds}s"


if __name__ == "__main__":
    print("🎬 YouTube Content Search Demo")
    print("=" * 40)
    asyncio.run(demo_youtube_search())