"""
Improved Content Generator with AI Integration and Trend Analysis
"""

import json
import random
import requests
import openai
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
from abc import ABC, abstractmethod

@dataclass
class VideoContent:
    title: str
    description: str
    tags: List[str]
    thumbnail_path: str
    script: str
    hook: str
    cta: str
    category: str
    estimated_duration: int
    trending_score: float = 0.0

@dataclass
class TrendingTopic:
    keyword: str
    volume: int
    competition: float
    relevance_score: float
    category: str

class ContentStrategy(ABC):
    """Abstract base class for content strategies"""
    
    @abstractmethod
    def generate_content(self) -> VideoContent:
        pass
    
    @abstractmethod
    def get_trending_topics(self) -> List[TrendingTopic]:
        pass

class TrendAnalyzer:
    """Analyze trends from multiple sources"""
    
    def __init__(self, youtube_api_key: str, openai_api_key: str):
        self.youtube_api_key = youtube_api_key
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.logger = logging.getLogger(__name__)
        
        # Category ID mapping
        self.category_mapping = {
            'gaming': '20',
            'anime': '1',  # Film & Animation
            'entertainment': '24',
            'music': '10'
        }
    
    def get_trending_topics(self, category: str, region: str = 'US') -> List[TrendingTopic]:
        """Get trending topics from YouTube API"""
        try:
            category_id = self.category_mapping.get(category, '20')
            
            # Get trending videos
            url = "https://www.googleapis.com/youtube/v3/videos"
            params = {
                'part': 'snippet,statistics',
                'chart': 'mostPopular',
                'regionCode': region,
                'videoCategoryId': category_id,
                'maxResults': 50,
                'key': self.youtube_api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            videos = response.json().get('items', [])
            
            # Extract titles and analyze with AI
            titles = [video['snippet']['title'] for video in videos]
            statistics = [video['statistics'] for video in videos]
            
            return self._analyze_trends_with_ai(titles, statistics, category)
            
        except Exception as e:
            self.logger.error(f"Trend analysis failed: {e}")
            return self._get_fallback_trends(category)
    
    def _analyze_trends_with_ai(self, titles: List[str], statistics: List[Dict], category: str) -> List[TrendingTopic]:
        """Use AI to extract trending keywords and topics"""
        try:
            prompt = f"""
            Analyze these trending {category} video titles and extract viral keywords:
            
            Titles: {json.dumps(titles[:20])}
            
            Extract the top 15 trending keywords that would work for YouTube Shorts.
            For each keyword, provide:
            1. The keyword/phrase
            2. Estimated search volume (1-100)
            3. Competition level (0.1-1.0)
            4. Relevance to {category} (0.1-1.0)
            
            Return as JSON array: [{"keyword": "text", "volume": 85, "competition": 0.6, "relevance": 0.9}]
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.3
            )
            
            keywords_data = json.loads(response.choices[0].message.content)
            
            trending_topics = []
            for item in keywords_data:
                topic = TrendingTopic(
                    keyword=item['keyword'],
                    volume=item['volume'],
                    competition=item['competition'],
                    relevance_score=item['relevance'],
                    category=category
                )
                trending_topics.append(topic)
            
            return sorted(trending_topics, key=lambda x: x.volume * x.relevance_score, reverse=True)
            
        except Exception as e:
            self.logger.error(f"AI trend analysis failed: {e}")
            return self._get_fallback_trends(category)
    
    def _get_fallback_trends(self, category: str) -> List[TrendingTopic]:
        """Fallback trending topics when API fails"""
        fallback_data = {
            'gaming': [
                TrendingTopic("epic gaming moments", 90, 0.7, 0.9, category),
                TrendingTopic("gaming shorts", 85, 0.8, 0.95, category),
                TrendingTopic("pro gamer tips", 80, 0.6, 0.8, category),
                TrendingTopic("gaming fails", 75, 0.5, 0.85, category),
                TrendingTopic("speedrun highlights", 70, 0.4, 0.7, category)
            ],
            'anime': [
                TrendingTopic("anime moments", 95, 0.8, 0.95, category),
                TrendingTopic("anime reactions", 90, 0.7, 0.9, category),
                TrendingTopic("anime theories", 85, 0.6, 0.8, category),
                TrendingTopic("anime shorts", 80, 0.9, 0.95, category),
                TrendingTopic("anime fights", 75, 0.5, 0.85, category)
            ]
        }
        
        return fallback_data.get(category, fallback_data['gaming'])

class AIContentGenerator:
    """Generate content using AI with viral optimization"""
    
    def __init__(self, openai_api_key: str, trend_analyzer: TrendAnalyzer):
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.trend_analyzer = trend_analyzer
        self.logger = logging.getLogger(__name__)
        
        # Viral content templates
        self.viral_patterns = {
            'hook_templates': [
                "You won't believe what happens when...",
                "This {category} moment broke the internet...",
                "Nobody talks about this {category} secret...",
                "This will change how you see {category}...",
                "Wait until you see what happens at 0:{timestamp}...",
                "POV: You discover the most {adjective} {category} moment...",
                "This {category} theory will blow your mind...",
                "The {category} community is losing it over this..."
            ],
            'cta_templates': [
                "Drop a 🔥 if this gave you chills! What's your favorite {category} moment?",
                "Comment your top 3 {category} picks and I'll rate them 1-10!",
                "Hit subscribe if you want more {category} content like this!",
                "Like if you agree, comment if you disagree! Let's debate!",
                "Save this video and thank me later! What should we cover next?",
                "Share this with someone who needs to see it! Tag them below!",
                "If this reaches 1000 likes, I'll make part 2! What topic should I cover?",
                "Comment YES if you want a full breakdown of this!"
            ]
        }
    
    def generate_viral_content(self, category: str, trending_topics: List[TrendingTopic]) -> VideoContent:
        """Generate viral content using AI and trending topics"""
        try:
            # Select top trending topics
            top_topics = trending_topics[:5]
            topic_keywords = [t.keyword for t in top_topics]
            
            # Generate content with AI
            content_prompt = self._create_content_prompt(category, topic_keywords)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": content_prompt}],
                max_tokens=1200,
                temperature=0.7
            )
            
            content_data = json.loads(response.choices[0].message.content)
            
            # Enhance with viral elements
            enhanced_content = self._enhance_with_viral_elements(content_data, category, trending_topics)
            
            return enhanced_content
            
        except Exception as e:
            self.logger.error(f"AI content generation failed: {e}")
            return self._generate_fallback_content(category, trending_topics)
    
    def _create_content_prompt(self, category: str, trending_keywords: List[str]) -> str:
        """Create optimized prompt for content generation"""
        return f"""
        Create a viral YouTube Shorts script for {category} content using trending keywords: {', '.join(trending_keywords)}
        
        Requirements:
        - 45-60 seconds duration
        - Hook within first 3 seconds
        - Fast-paced, engaging script
        - Include trending keywords naturally
        - Vertical video format (9:16)
        - Strong emotional trigger
        - Clear call-to-action
        - Optimized for YouTube algorithm
        
        Return JSON with:
        {{
            "title": "Catchy title with trending keywords (max 60 chars)",
            "script": "Complete 60-second script with timestamps",
            "hook": "First 3 seconds hook",
            "main_content": "Main content sections",
            "cta": "Call-to-action",
            "tags": ["list", "of", "relevant", "tags"],
            "target_emotion": "primary emotion to trigger",
            "visual_cues": ["key", "visual", "elements"]
        }}
        
        Focus on creating content that will get maximum engagement and shares.
        """
    
    def _enhance_with_viral_elements(self, content_data: Dict, category: str, trending_topics: List[TrendingTopic]) -> VideoContent:
        """Enhance AI-generated content with viral optimization"""
        
        # Calculate trending score
        trending_score = sum(t.volume * t.relevance_score for t in trending_topics[:3]) / 3
        
        # Enhance title with viral elements
        title = content_data['title']
        if trending_score > 80:
            title = f"🔥 {title}"
        elif trending_score > 60:
            title = f"⚡ {title}"
        
        # Enhance tags with trending keywords
        base_tags = content_data.get('tags', [])
        trending_tags = [t.keyword.replace(' ', '') for t in trending_topics[:5]]
        viral_tags = ['shorts', 'viral', 'trending', 'fyp', 'foryou']
        all_tags = list(set(base_tags + trending_tags + viral_tags))
        
        # Generate SEO-optimized description
        description = self._generate_seo_description(content_data, category, trending_topics)
        
        return VideoContent(
            title=title[:100],  # YouTube title limit
            description=description,
            tags=all_tags[:30],  # Reasonable tag limit
            thumbnail_path="",  # To be generated separately
            script=content_data['script'],
            hook=content_data['hook'],
            cta=content_data['cta'],
            category=category,
            estimated_duration=60,
            trending_score=trending_score
        )
    
    def _generate_seo_description(self, content_data: Dict, category: str, trending_topics: List[TrendingTopic]) -> str:
        """Generate SEO-optimized description"""
        top_keywords = [t.keyword for t in trending_topics[:5]]
        
        description = f"""🔥 {content_data['title']} 🔥

{content_data.get('hook', '')}

⚡ What's in this video:
✅ {category.title()} highlights and epic moments
✅ Trending {category} content you can't miss
✅ Community favorites and viral clips
✅ {', '.join(top_keywords[:3])}

🎯 Daily {category} content at 9AM, 12PM, 4PM & 8PM!

💬 Engage with us:
👆 LIKE for more {category} content
🔔 SUBSCRIBE for daily uploads
💬 COMMENT your thoughts
🔄 SHARE with friends

🏷️ Tags: {' '.join([f'#{tag}' for tag in content_data.get('tags', [])[:10]])}

#Shorts #Viral #Trending #FYP #{category.title()}"""
        
        return description[:5000]  # YouTube description limit
    
    def _generate_fallback_content(self, category: str, trending_topics: List[TrendingTopic]) -> VideoContent:
        """Generate fallback content when AI fails"""
        fallback_templates = {
            'gaming': {
                'title': "Epic Gaming Moments That Broke The Internet",
                'hook': "You won't believe what happens in this gaming clip...",
                'script': """[0-3s] Hook with epic moment preview
[3-10s] "Gamers, you NEED to see this!"
[10-40s] Showcase epic gaming moments with quick cuts
[40-55s] "This is why gaming is amazing!"
[55-60s] "Drop your best gaming moment below!"
""",
                'cta': "Comment your best gaming moment! Like if this was epic! 🔥"
            },
            'anime': {
                'title': "Anime Moments That Made Everyone Cry",
                'hook': "This anime moment hits different...",
                'script': """[0-3s] Hook with emotional moment preview
[3-10s] "Anime fans, prepare your tissues!"
[10-40s] Showcase emotional anime scenes
[40-55s] "This is why anime is pure art!"
[55-60s] "What's your most emotional anime moment?"
""",
                'cta': "Share your favorite emotional anime moment! Like if you cried! 😭"
            }
        }
        
        template = fallback_templates.get(category, fallback_templates['gaming'])
        trending_score = sum(t.volume for t in trending_topics[:3]) / 3 if trending_topics else 50
        
        return VideoContent(
            title=template['title'],
            description=f"{template['hook']}\n\nMore amazing {category} content coming daily!",
            tags=[category, 'shorts', 'viral', 'trending'],
            thumbnail_path="",
            script=template['script'],
            hook=template['hook'],
            cta=template['cta'],
            category=category,
            estimated_duration=60,
            trending_score=trending_score
        )

class AdvancedContentStrategy(ContentStrategy):
    """Advanced content strategy with AI and trend analysis"""
    
    def __init__(self, youtube_api_key: str, openai_api_key: str, category: str = 'gaming'):
        self.category = category
        self.trend_analyzer = TrendAnalyzer(youtube_api_key, openai_api_key)
        self.content_generator = AIContentGenerator(openai_api_key, self.trend_analyzer)
        self.logger = logging.getLogger(__name__)
    
    def generate_content(self) -> VideoContent:
        """Generate content using advanced AI and trend analysis"""
        try:
            # Get trending topics
            trending_topics = self.get_trending_topics()
            
            # Generate viral content
            content = self.content_generator.generate_viral_content(self.category, trending_topics)
            
            self.logger.info(f"Generated content: {content.title} (Score: {content.trending_score:.1f})")
            return content
            
        except Exception as e:
            self.logger.error(f"Content generation failed: {e}")
            # Return fallback content
            return self.content_generator._generate_fallback_content(self.category, [])
    
    def get_trending_topics(self) -> List[TrendingTopic]:
        """Get current trending topics"""
        return self.trend_analyzer.get_trending_topics(self.category)
    
    def analyze_content_performance(self, content: VideoContent, views: int, engagement_rate: float) -> Dict:
        """Analyze content performance for future optimization"""
        performance_score = (views / 1000) * engagement_rate * content.trending_score
        
        analysis = {
            'content_id': content.title,
            'performance_score': performance_score,
            'trending_score': content.trending_score,
            'views': views,
            'engagement_rate': engagement_rate,
            'recommendations': []
        }
        
        # Add recommendations based on performance
        if performance_score < 50:
            analysis['recommendations'].extend([
                "Consider using more trending keywords",
                "Improve hook effectiveness",
                "Test different thumbnail styles"
            ])
        
        if content.trending_score < 60:
            analysis['recommendations'].append("Focus on more viral topics")
        
        return analysis

# Example usage
if __name__ == "__main__":
    import os
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize with API keys (use environment variables in production)
    youtube_api_key = os.getenv('YOUTUBE_API_KEY', 'your_key_here')
    openai_api_key = os.getenv('OPENAI_API_KEY', 'your_key_here')
    
    # Create content strategy
    strategy = AdvancedContentStrategy(youtube_api_key, openai_api_key, 'gaming')
    
    # Generate content
    content = strategy.generate_content()
    
    print(f"Generated content: {content.title}")
    print(f"Trending score: {content.trending_score:.1f}")
    print(f"Script preview: {content.script[:100]}...")