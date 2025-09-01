# YouTube Content Search Implementation

## Overview

The YouTube content search functionality enables EdAgent to discover, filter, and rank educational videos from YouTube based on user preferences and learning goals. This implementation provides intelligent content recommendation with quality scoring and skill matching.

## Features

### 🔍 Smart Search
- **Query-based search**: Find videos using natural language queries
- **Quality filtering**: Automatically filter out low-quality content
- **Engagement scoring**: Rank videos based on views, likes, and comments
- **Duration filtering**: Filter by video length preferences
- **Skill extraction**: Automatically identify skills covered in videos

### 📊 Quality Assessment
- **View count analysis**: Consider video popularity
- **Engagement metrics**: Like-to-view and comment-to-view ratios
- **Duration optimization**: Prefer educational-length content (5-30 minutes)
- **Caption availability**: Track accessibility features
- **Channel credibility**: Consider channel subscriber count

### 🎯 Personalization
- **Skill matching**: Match content to user's current skills and goals
- **Difficulty assessment**: Automatically determine content difficulty level
- **Preference filtering**: Filter by budget, platform, and content type preferences
- **Learning style adaptation**: Consider visual/auditory learning preferences

## Implementation Details

### Core Components

#### ContentRecommender Class
```python
class ContentRecommender(ContentRecommenderInterface):
    """Main service for content recommendation with YouTube integration"""
    
    async def search_youtube_content(self, query: str, filters: ContentFilters) -> List[YouTubeVideo]
    async def filter_by_preferences(self, content: List[ContentRecommendation], preferences: Dict[str, Any]) -> List[ContentRecommendation]
    async def rank_content(self, content: List[ContentRecommendation], user_context: UserContext) -> List[ContentRecommendation]
```

#### YouTubeVideo Model
```python
@dataclass
class YouTubeVideo(ContentRecommendation):
    """Specialized model for YouTube videos with engagement metrics"""
    
    video_id: str
    channel_name: str
    view_count: int
    like_count: int
    comment_count: int
    captions_available: bool
    
    def calculate_engagement_score(self) -> float
```

#### YouTubeContentFilters
```python
class YouTubeContentFilters(ContentFilters):
    """Extended filters for YouTube-specific search parameters"""
    
    max_results: int = 25
    min_view_count: int = 100
    captions_required: bool = False
    upload_date: str = None  # 'hour', 'today', 'week', 'month', 'year'
```

### Search Algorithm

1. **Query Processing**: Clean and optimize search terms
2. **API Search**: Execute YouTube Data API search with filters
3. **Metadata Retrieval**: Get detailed video information (duration, stats, etc.)
4. **Quality Scoring**: Calculate quality score based on engagement metrics
5. **Skill Extraction**: Identify technical skills from title/description
6. **Difficulty Assessment**: Determine content difficulty level
7. **Filtering**: Apply user preference filters
8. **Ranking**: Sort by relevance and quality scores

### Quality Scoring Formula

```python
quality_score = (
    view_score * 0.3 +           # Normalized view count (log scale)
    like_ratio * 100 * 0.3 +     # Like-to-view ratio
    comment_ratio * 500 * 0.2 +  # Comment-to-view ratio  
    duration_score * 0.2         # Optimal duration bonus
)
```

### Skill Extraction

The system automatically identifies technical skills from video content:

```python
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
```

## Usage Examples

### Basic Search
```python
from edagent.services.content_recommender import ContentRecommender, YouTubeContentFilters
from edagent.config.settings import Settings

# Initialize service
settings = Settings(youtube_api_key="your_api_key")
recommender = ContentRecommender(settings)

# Create filters
filters = YouTubeContentFilters(
    max_duration=1800,  # 30 minutes
    min_view_count=1000,
    max_results=10
)

# Search for content
results = await recommender.search_youtube_content("Python web development", filters)
```

### Personalized Recommendations
```python
# Create user context
user_context = UserContext(
    user_id="user123",
    current_skills={"python": SkillLevel("python", SkillLevelEnum.BEGINNER, 0.6)},
    career_goals=["become a web developer"],
    learning_preferences=UserPreferences(
        learning_style=LearningStyleEnum.VISUAL,
        budget_preference="free",
        preferred_platforms=["YouTube"]
    )
)

# Search and rank content
search_results = await recommender.search_youtube_content("Python tutorial", filters)
preferences = user_context.learning_preferences.to_dict()
filtered_results = await recommender.filter_by_preferences(search_results, preferences)
ranked_results = await recommender.rank_content(filtered_results, user_context)
```

## Configuration

### Environment Variables
```bash
# Required
YOUTUBE_API_KEY=your_youtube_data_api_key

# Optional
YOUTUBE_MAX_RESULTS=10
CONTENT_CACHE_TTL=3600
```

### API Key Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable YouTube Data API v3
4. Create credentials (API Key)
5. Restrict the key to YouTube Data API v3
6. Set the key in your environment variables

## Testing

### Unit Tests
```bash
# Run content recommender tests
python -m pytest tests/test_content_recommender.py -v

# Run integration tests
python -m pytest tests/test_youtube_integration.py -v
```

### Demo Script
```bash
# Run the demo (works with or without API key)
PYTHONPATH=. python examples/youtube_search_demo.py
```

## Performance Considerations

### Rate Limiting
- YouTube Data API has quota limits (10,000 units/day by default)
- Each search costs ~100 units, video details cost ~1 unit per video
- Implement caching to reduce API calls
- Use exponential backoff for rate limit handling

### Optimization Tips
1. **Cache Results**: Store search results for popular queries
2. **Batch Requests**: Get multiple video details in single API call
3. **Smart Filtering**: Apply filters before API calls when possible
4. **Result Limiting**: Don't request more results than needed

### Error Handling
- **API Quota Exceeded**: Graceful degradation with cached results
- **Network Issues**: Retry with exponential backoff
- **Invalid Videos**: Skip malformed or unavailable videos
- **Authentication Errors**: Clear error messages for API key issues

## Future Enhancements

### Planned Features
1. **Content Caching**: Redis-based caching for popular searches
2. **Playlist Support**: Search and recommend YouTube playlists
3. **Channel Analysis**: Evaluate channel quality and consistency
4. **Transcript Analysis**: Use video transcripts for better skill extraction
5. **User Feedback**: Learn from user ratings and preferences
6. **Multi-language Support**: Search content in different languages

### Integration Points
- **AI Service**: Use Gemini to analyze video descriptions
- **User Context**: Track viewing history and preferences
- **Learning Paths**: Integrate video recommendations into learning paths
- **Progress Tracking**: Monitor video completion and comprehension

## Troubleshooting

### Common Issues

#### "YouTube service not available"
- Check if `YOUTUBE_API_KEY` is set correctly
- Verify API key has YouTube Data API v3 enabled
- Check API key restrictions and quotas

#### "No results found"
- Try broader search terms
- Check if filters are too restrictive
- Verify API quota hasn't been exceeded

#### "Quality score always 0"
- Check if video statistics are available
- Some videos may have disabled statistics
- Ensure video is not private or restricted

### Debug Mode
```python
import logging
logging.getLogger('edagent.services.content_recommender').setLevel(logging.DEBUG)
```

## Requirements Mapping

This implementation addresses the following requirements:

- **Requirement 4.1**: Free educational resource recommendations ✅
- **Requirement 4.2**: Clear cost indication (all YouTube content is free) ✅  
- **Requirement 6.1**: Learning preference-based filtering ✅
- **Requirement 6.2**: Content format information (video metadata) ✅

## API Reference

### ContentRecommender Methods

#### `search_youtube_content(query: str, filters: ContentFilters) -> List[YouTubeVideo]`
Search YouTube for educational content matching the query and filters.

**Parameters:**
- `query`: Search query string
- `filters`: ContentFilters or YouTubeContentFilters object

**Returns:** List of YouTubeVideo objects ranked by quality

#### `filter_by_preferences(content: List[ContentRecommendation], preferences: Dict[str, Any]) -> List[ContentRecommendation]`
Filter content based on user preferences.

**Parameters:**
- `content`: List of content recommendations
- `preferences`: User preference dictionary

**Returns:** Filtered list of content recommendations

#### `rank_content(content: List[ContentRecommendation], user_context: UserContext) -> List[ContentRecommendation]`
Rank content based on user context and skill matching.

**Parameters:**
- `content`: List of content recommendations  
- `user_context`: User context with skills and goals

**Returns:** Ranked list of content recommendations