"""
Advanced Video Generator for YouTube Shorts
Creates actual video files with TTS, visuals, and effects
"""

import asyncio
import os
import random
import tempfile
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging
from dataclasses import dataclass
from pathlib import Path

# Video processing libraries
from moviepy.editor import *
from moviepy.video.fx import resize
import edge_tts
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

# For downloading stock footage/images
import unsplash
from pixabay import Image as PixabayImage, Video as PixabayVideo

@dataclass
class VideoScene:
    start_time: float
    end_time: float
    text: str
    visual_type: str  # 'image', 'video', 'text', 'transition'
    visual_source: str  # path to media or text content
    effects: List[str] = None
    audio_emphasis: bool = False

@dataclass
class VideoStyle:
    primary_color: str
    secondary_color: str
    font_family: str
    animation_style: str  # 'zoom', 'slide', 'fade', 'bounce'
    background_type: str  # 'gradient', 'image', 'video', 'solid'
    energy_level: str  # 'high', 'medium', 'low'

class AdvancedVideoGenerator:
    """Generate professional YouTube Shorts videos"""
    
    def __init__(self, unsplash_api_key: str = None, pixabay_api_key: str = None):
        self.unsplash_client = unsplash.Api(unsplash_api_key) if unsplash_api_key else None
        self.pixabay_client = PixabayImage(pixabay_api_key) if pixabay_api_key else None
        self.logger = logging.getLogger(__name__)
        
        # Video settings
        self.video_width = 1080
        self.video_height = 1920  # 9:16 aspect ratio
        self.fps = 30
        self.duration = 60  # seconds
        
        # Style presets
        self.style_presets = {
            'gaming': VideoStyle(
                primary_color='#FF6B35',
                secondary_color='#004E7C',
                font_family='arial-bold',
                animation_style='zoom',
                background_type='gradient',
                energy_level='high'
            ),
            'anime': VideoStyle(
                primary_color='#FF69B4',
                secondary_color='#8A2BE2',
                font_family='arial-bold',
                animation_style='bounce',
                background_type='gradient',
                energy_level='high'
            ),
            'educational': VideoStyle(
                primary_color='#2E86AB',
                secondary_color='#A23B72',
                font_family='arial',
                animation_style='slide',
                background_type='solid',
                energy_level='medium'
            )
        }
        
        # Audio settings
        self.voice_settings = {
            'gaming': 'en-US-GuyNeural',  # Energetic male voice
            'anime': 'en-US-AriaNeural',  # Expressive female voice
            'educational': 'en-US-DavisNeural',  # Clear male voice
            'default': 'en-US-JennyNeural'  # Default female voice
        }
    
    async def create_video(self, script: str, category: str, title: str, output_path: str = None) -> str:
        """Create a complete video from script"""
        try:
            self.logger.info(f"Starting video generation for: {title}")
            
            # Parse script into scenes
            scenes = self._parse_script_to_scenes(script)
            
            # Get video style
            style = self.style_presets.get(category, self.style_presets['gaming'])
            
            # Generate TTS audio
            audio_path = await self._generate_tts(script, category)
            
            # Create visual scenes
            video_clips = []
            for scene in scenes:
                clip = await self._create_scene_clip(scene, style, category)
                video_clips.append(clip)
            
            # Combine all clips
            final_video = self._combine_clips(video_clips, audio_path, style)
            
            # Add effects and transitions
            final_video = self._add_effects(final_video, style)
            
            # Generate output path
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"youtube_short_{category}_{timestamp}.mp4"
            
            # Export video
            final_video.write_videofile(
                output_path,
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            self.logger.info(f"Video created successfully: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Video generation failed: {e}")
            raise
    
    def _parse_script_to_scenes(self, script: str) -> List[VideoScene]:
        """Parse script into timed scenes"""
        scenes = []
        lines = script.split('\n')
        
        current_time = 0.0
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Extract timestamp if present [0-5s]
            if '[' in line and ']' in line:
                timestamp_part = line[line.find('['):line.find(']')+1]
                content = line.replace(timestamp_part, '').strip()
                
                # Parse timestamp
                if '-' in timestamp_part:
                    start_str, end_str = timestamp_part[1:-1].split('-')
                    start_time = float(start_str.replace('s', ''))
                    end_time = float(end_str.replace('s', ''))
                else:
                    start_time = current_time
                    end_time = current_time + 5.0  # Default 5 seconds
            else:
                content = line
                start_time = current_time
                end_time = current_time + 5.0
            
            # Determine visual type based on content
            visual_type = self._determine_visual_type(content)
            
            scene = VideoScene(
                start_time=start_time,
                end_time=end_time,
                text=content,
                visual_type=visual_type,
                visual_source=content,
                effects=['fade_in', 'fade_out'] if visual_type == 'text' else ['zoom', 'fade']
            )
            
            scenes.append(scene)
            current_time = end_time
        
        return scenes
    
    def _determine_visual_type(self, content: str) -> str:
        """Determine what type of visual to use for content"""
        content_lower = content.lower()
        
        if any(word in content_lower for word in ['epic', 'amazing', 'incredible', 'shock']):
            return 'dynamic_text'
        elif any(word in content_lower for word in ['hook', 'intro', 'welcome']):
            return 'title_card'
        elif any(word in content_lower for word in ['moment', 'scene', 'clip']):
            return 'image_sequence'
        elif any(word in content_lower for word in ['subscribe', 'like', 'comment']):
            return 'cta_animation'
        else:
            return 'text_overlay'
    
    async def _generate_tts(self, script: str, category: str) -> str:
        """Generate text-to-speech audio"""
        try:
            # Clean script for TTS (remove timestamps and formatting)
            clean_script = self._clean_script_for_tts(script)
            
            # Select voice based on category
            voice = self.voice_settings.get(category, self.voice_settings['default'])
            
            # Generate TTS
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_path = f"tts_audio_{timestamp}.wav"
            
            communicate = edge_tts.Communicate(clean_script, voice)
            await communicate.save(audio_path)
            
            return audio_path
            
        except Exception as e:
            self.logger.error(f"TTS generation failed: {e}")
            raise
    
    def _clean_script_for_tts(self, script: str) -> str:
        """Clean script for TTS processing"""
        lines = script.split('\n')
        clean_lines = []
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Remove timestamp markers
            if '[' in line and ']' in line:
                line = line[line.find(']')+1:].strip()
            
            # Remove quotes and special formatting
            line = line.replace('"', '').replace("'", '').replace('*', '')
            
            # Add natural pauses
            if line.endswith('!') or line.endswith('?'):
                line += ' ... '
            elif line.endswith('.'):
                line += ' .. '
            
            clean_lines.append(line)
        
        return ' '.join(clean_lines)
    
    async def _create_scene_clip(self, scene: VideoScene, style: VideoStyle, category: str) -> VideoClip:
        """Create a video clip for a single scene"""
        duration = scene.end_time - scene.start_time
        
        if scene.visual_type == 'title_card':
            return self._create_title_card(scene.text, duration, style)
        elif scene.visual_type == 'dynamic_text':
            return self._create_dynamic_text(scene.text, duration, style)
        elif scene.visual_type == 'image_sequence':
            return await self._create_image_sequence(scene.text, duration, style, category)
        elif scene.visual_type == 'cta_animation':
            return self._create_cta_animation(scene.text, duration, style)
        else:
            return self._create_text_overlay(scene.text, duration, style)
    
    def _create_title_card(self, text: str, duration: float, style: VideoStyle) -> VideoClip:
        """Create an animated title card"""
        # Create background
        bg_clip = self._create_background(duration, style)
        
        # Create text clip
        text_clip = TextClip(
            text,
            fontsize=80,
            color='white',
            font='Arial-Bold',
            stroke_color=style.primary_color,
            stroke_width=3
        ).set_duration(duration).set_position('center')
        
        # Add animation based on style
        if style.animation_style == 'zoom':
            text_clip = text_clip.resize(lambda t: 1 + 0.1 * np.sin(2 * np.pi * t))
        elif style.animation_style == 'bounce':
            text_clip = text_clip.set_position(lambda t: ('center', 'center' if t < 0.5 else 'center'))
        
        return CompositeVideoClip([bg_clip, text_clip])
    
    def _create_dynamic_text(self, text: str, duration: float, style: VideoStyle) -> VideoClip:
        """Create dynamic animated text"""
        bg_clip = self._create_background(duration, style)
        
        # Split text into words for word-by-word animation
        words = text.split()
        word_clips = []
        
        word_duration = duration / len(words)
        
        for i, word in enumerate(words):
            start_time = i * word_duration
            
            word_clip = TextClip(
                word,
                fontsize=60 + random.randint(-10, 20),  # Varying sizes
                color='white',
                font='Arial-Bold',
                stroke_color=style.primary_color,
                stroke_width=2
            ).set_duration(word_duration * 1.5).set_start(start_time)
            
            # Random position for dynamic effect
            x_pos = random.randint(100, self.video_width - 200)
            y_pos = random.randint(200, self.video_height - 200)
            word_clip = word_clip.set_position((x_pos, y_pos))
            
            # Add fade effect
            word_clip = word_clip.fadeout(0.2)
            
            word_clips.append(word_clip)
        
        return CompositeVideoClip([bg_clip] + word_clips)
    
    async def _create_image_sequence(self, text: str, duration: float, style: VideoStyle, category: str) -> VideoClip:
        """Create a sequence of relevant images"""
        try:
            # Search for relevant images
            search_terms = self._extract_keywords_for_images(text, category)
            images = await self._download_stock_images(search_terms)
            
            if not images:
                # Fallback to generated images
                images = self._generate_placeholder_images(search_terms, style)
            
            # Create image sequence
            image_clips = []
            images_per_clip = min(len(images), 3)  # Max 3 images per scene
            image_duration = duration / images_per_clip
            
            for i, image_path in enumerate(images[:images_per_clip]):
                start_time = i * image_duration
                
                img_clip = ImageClip(image_path, duration=image_duration).set_start(start_time)
                
                # Resize to fit video dimensions
                img_clip = img_clip.resize(height=self.video_height).set_position('center')
                
                # Add zoom effect
                if style.animation_style == 'zoom':
                    img_clip = img_clip.resize(lambda t: 1 + 0.1 * t / image_duration)
                
                image_clips.append(img_clip)
            
            # Create background
            bg_clip = self._create_background(duration, style)
            
            return CompositeVideoClip([bg_clip] + image_clips)
            
        except Exception as e:
            self.logger.warning(f"Image sequence creation failed: {e}")
            return self._create_text_overlay(text, duration, style)
    
    def _create_cta_animation(self, text: str, duration: float, style: VideoStyle) -> VideoClip:
        """Create call-to-action animation"""
        bg_clip = self._create_background(duration, style)
        
        # Create main CTA text
        cta_text = TextClip(
            text,
            fontsize=50,
            color='white',
            font='Arial-Bold',
            stroke_color=style.primary_color,
            stroke_width=3
        ).set_duration(duration).set_position('center')
        
        # Add pulsing effect
        cta_text = cta_text.resize(lambda t: 1 + 0.1 * np.sin(4 * np.pi * t))
        
        # Add subscribe button animation
        button_text = TextClip(
            "👆 SUBSCRIBE 👆",
            fontsize=40,
            color=style.primary_color,
            font='Arial-Bold'
        ).set_duration(duration).set_position(('center', 100))
        
        return CompositeVideoClip([bg_clip, cta_text, button_text])
    
    def _create_text_overlay(self, text: str, duration: float, style: VideoStyle) -> VideoClip:
        """Create simple text overlay"""
        bg_clip = self._create_background(duration, style)
        
        text_clip = TextClip(
            text,
            fontsize=45,
            color='white',
            font='Arial',
            stroke_color='black',
            stroke_width=2
        ).set_duration(duration).set_position('center')
        
        return CompositeVideoClip([bg_clip, text_clip])
    
    def _create_background(self, duration: float, style: VideoStyle) -> VideoClip:
        """Create background based on style"""
        if style.background_type == 'gradient':
            return self._create_gradient_background(duration, style)
        elif style.background_type == 'solid':
            return ColorClip(size=(self.video_width, self.video_height), 
                           color=style.primary_color, duration=duration)
        else:
            return self._create_gradient_background(duration, style)
    
    def _create_gradient_background(self, duration: float, style: VideoStyle) -> VideoClip:
        """Create animated gradient background"""
        # Create gradient image
        img = Image.new('RGB', (self.video_width, self.video_height))
        draw = ImageDraw.Draw(img)
        
        # Parse colors
        color1 = self._hex_to_rgb(style.primary_color)
        color2 = self._hex_to_rgb(style.secondary_color)
        
        # Create gradient
        for y in range(self.video_height):
            ratio = y / self.video_height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            
            draw.line([(0, y), (self.video_width, y)], fill=(r, g, b))
        
        # Save and create clip
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bg_path = f"gradient_bg_{timestamp}.png"
        img.save(bg_path)
        
        bg_clip = ImageClip(bg_path, duration=duration)
        
        # Add subtle animation
        if style.energy_level == 'high':
            bg_clip = bg_clip.resize(lambda t: 1 + 0.05 * np.sin(2 * np.pi * t))
        
        return bg_clip
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _extract_keywords_for_images(self, text: str, category: str) -> List[str]:
        """Extract keywords for image search"""
        keywords = []
        
        # Category-specific keywords
        if category == 'gaming':
            keywords.extend(['gaming', 'esports', 'controller', 'computer'])
        elif category == 'anime':
            keywords.extend(['anime', 'manga', 'character', 'japanese'])
        
        # Extract keywords from text
        important_words = [word.lower() for word in text.split() 
                          if len(word) > 3 and word.lower() not in ['this', 'that', 'with', 'from']]
        keywords.extend(important_words[:3])
        
        return keywords[:5]
    
    async def _download_stock_images(self, search_terms: List[str]) -> List[str]:
        """Download stock images for video"""
        images = []
        
        if not self.unsplash_client:
            return images
        
        try:
            for term in search_terms[:2]:  # Limit API calls
                photos = self.unsplash_client.search.photos(term, per_page=2)
                
                for photo in photos:
                    # Download image
                    response = requests.get(photo.urls.regular)
                    if response.status_code == 200:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"stock_image_{term}_{timestamp}.jpg"
                        
                        with open(filename, 'wb') as f:
                            f.write(response.content)
                        
                        images.append(filename)
            
            return images
            
        except Exception as e:
            self.logger.warning(f"Stock image download failed: {e}")
            return []
    
    def _generate_placeholder_images(self, search_terms: List[str], style: VideoStyle) -> List[str]:
        """Generate placeholder images when stock images aren't available"""
        images = []
        
        for term in search_terms[:3]:
            img = Image.new('RGB', (self.video_width, self.video_height), 
                          color=self._hex_to_rgb(style.primary_color))
            draw = ImageDraw.Draw(img)
            
            # Add text
            try:
                font = ImageFont.truetype("arial.ttf", 100)
            except:
                font = ImageFont.load_default()
            
            draw.text((self.video_width//2, self.video_height//2), term.upper(), 
                     fill='white', font=font, anchor='mm')
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"placeholder_{term}_{timestamp}.png"
            img.save(filename)
            images.append(filename)
        
        return images
    
    def _combine_clips(self, video_clips: List[VideoClip], audio_path: str, style: VideoStyle) -> VideoClip:
        """Combine all video clips with audio"""
        # Concatenate video clips
        final_video = concatenate_videoclips(video_clips, method="compose")
        
        # Load and set audio
        audio = AudioFileClip(audio_path)
        final_video = final_video.set_audio(audio)
        
        # Adjust video duration to match audio
        if final_video.duration != audio.duration:
            final_video = final_video.subclip(0, min(final_video.duration, audio.duration))
        
        return final_video
    
    def _add_effects(self, video: VideoClip, style: VideoStyle) -> VideoClip:
        """Add final effects and enhancements"""
        # Add fade in/out
        video = video.fadein(0.5).fadeout(0.5)
        
        # Add subtle zoom for energy
        if style.energy_level == 'high':
            video = video.resize(lambda t: 1 + 0.02 * np.sin(2 * np.pi * t / 10))
        
        return video
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        temp_extensions = ['.wav', '.png', '.jpg', '.mp4']
        current_dir = Path.cwd()
        
        for file_path in current_dir.glob('*'):
            if (file_path.suffix in temp_extensions and 
                any(prefix in file_path.name for prefix in ['tts_', 'gradient_', 'stock_', 'placeholder_'])):
                try:
                    file_path.unlink()
                    self.logger.info(f"Cleaned up: {file_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to clean up {file_path}: {e}")

# Example usage
async def main():
    """Example usage of the video generator"""
    generator = AdvancedVideoGenerator()
    
    script = """
    [0-3s] You won't believe what happens next...
    [3-10s] Welcome gamers! Today we're showing you the most epic gaming moments!
    [10-30s] Check out this incredible speedrun that broke records!
    [30-50s] This player's skills are absolutely insane!
    [50-60s] Subscribe for more epic gaming content! Drop your best gaming moment below!
    """
    
    video_path = await generator.create_video(
        script=script,
        category='gaming',
        title='Epic Gaming Moments',
        output_path='epic_gaming_short.mp4'
    )
    
    print(f"Video created: {video_path}")
    
    # Cleanup temporary files
    generator.cleanup_temp_files()

if __name__ == "__main__":
    asyncio.run(main())