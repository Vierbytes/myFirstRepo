"""
YouTube Agent Web Interface v1.2
Modern web dashboard for managing YouTube automation
"""

import asyncio
import json
import os
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, Request, Form, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import uvicorn

# Import our modules
from secure_config import SecureConfigManager
from improved_content_generator import AdvancedContentStrategy, VideoContent
from video_generator import AdvancedVideoGenerator
from improved_youtube_agent import ImprovedYouTubeAgent

# Database models
Base = declarative_base()

class VideoHistory(Base):
    __tablename__ = "video_history"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text)
    category = Column(String)
    theme = Column(String)
    youtube_id = Column(String, unique=True, index=True)
    thumbnail_path = Column(String)
    video_path = Column(String)
    script = Column(Text)
    trending_score = Column(Float)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    upload_status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    uploaded_at = Column(DateTime)

class ScheduleEntry(Base):
    __tablename__ = "schedule_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    time_slot = Column(String)  # HH:MM format
    category = Column(String)
    theme = Column(String)
    enabled = Column(Boolean, default=True)
    days_of_week = Column(String)  # JSON array of day names
    created_at = Column(DateTime, default=datetime.utcnow)

# Pydantic models for API
class ScheduleCreate(BaseModel):
    time_slot: str
    category: str
    theme: str
    days_of_week: List[str]
    enabled: bool = True

class ThemeConfig(BaseModel):
    name: str
    primary_color: str
    secondary_color: str
    font_style: str
    animation_style: str
    background_type: str

class AgentConfig(BaseModel):
    youtube_api_key: str
    youtube_client_id: str
    youtube_client_secret: str
    openai_api_key: str
    email_username: str
    email_password: str
    notification_email: str

# Initialize FastAPI app
app = FastAPI(title="YouTube Agent Dashboard", version="1.2.0")

# Setup static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Database setup
DATABASE_URL = "sqlite:///./youtube_agent.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# Global agent instance
agent: Optional[ImprovedYouTubeAgent] = None
config_manager = SecureConfigManager()

# Video themes and categories
VIDEO_THEMES = {
    "gaming": {
        "Epic Moments": {"description": "Epic gaming moments and highlights", "tags": ["epic", "gaming", "highlights"]},
        "Pro Tips": {"description": "Professional gaming tips and tricks", "tags": ["tips", "tutorial", "pro"]},
        "Funny Fails": {"description": "Hilarious gaming fails and bloopers", "tags": ["funny", "fails", "comedy"]},
        "Speedruns": {"description": "Amazing speedrun highlights", "tags": ["speedrun", "fast", "record"]},
        "Reviews": {"description": "Quick game reviews and impressions", "tags": ["review", "gameplay", "opinion"]}
    },
    "anime": {
        "Epic Fights": {"description": "Best anime fight scenes", "tags": ["anime", "fights", "action"]},
        "Emotional Moments": {"description": "Heart-touching anime scenes", "tags": ["emotional", "feels", "sad"]},
        "Character Analysis": {"description": "Deep character breakdowns", "tags": ["analysis", "character", "psychology"]},
        "Top Lists": {"description": "Top anime rankings and lists", "tags": ["top", "best", "ranking"]},
        "Theories": {"description": "Anime theories and speculation", "tags": ["theory", "analysis", "speculation"]}
    },
    "educational": {
        "Quick Facts": {"description": "Interesting facts in 60 seconds", "tags": ["facts", "education", "learning"]},
        "How To": {"description": "Quick tutorials and guides", "tags": ["tutorial", "howto", "guide"]},
        "Science": {"description": "Cool science concepts explained", "tags": ["science", "physics", "chemistry"]},
        "History": {"description": "Historical events and stories", "tags": ["history", "events", "story"]},
        "Technology": {"description": "Latest tech trends and news", "tags": ["tech", "innovation", "future"]}
    }
}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_startup
async def startup_event():
    """Initialize the agent on startup"""
    global agent
    try:
        agent = ImprovedYouTubeAgent()
        print("🚀 YouTube Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")

# Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    db = next(get_db())
    
    # Get recent videos
    recent_videos = db.query(VideoHistory).order_by(VideoHistory.created_at.desc()).limit(6).all()
    
    # Get scheduled uploads
    scheduled_uploads = db.query(ScheduleEntry).filter(ScheduleEntry.enabled == True).all()
    
    # Calculate statistics
    total_videos = db.query(VideoHistory).count()
    successful_uploads = db.query(VideoHistory).filter(VideoHistory.upload_status == "success").count()
    total_views = db.query(VideoHistory).with_entities(VideoHistory.views).all()
    total_views_sum = sum([v[0] or 0 for v in total_views])
    
    stats = {
        "total_videos": total_videos,
        "successful_uploads": successful_uploads,
        "total_views": total_views_sum,
        "success_rate": (successful_uploads / total_videos * 100) if total_videos > 0 else 0
    }
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "recent_videos": recent_videos,
        "scheduled_uploads": scheduled_uploads,
        "stats": stats,
        "video_themes": VIDEO_THEMES
    })

@app.get("/schedule", response_class=HTMLResponse)
async def schedule_page(request: Request):
    """Schedule management page"""
    db = next(get_db())
    schedules = db.query(ScheduleEntry).order_by(ScheduleEntry.time_slot).all()
    
    return templates.TemplateResponse("schedule.html", {
        "request": request,
        "schedules": schedules,
        "video_themes": VIDEO_THEMES
    })

@app.post("/schedule/add")
async def add_schedule(request: Request, schedule_data: ScheduleCreate):
    """Add new schedule entry"""
    db = next(get_db())
    
    new_schedule = ScheduleEntry(
        time_slot=schedule_data.time_slot,
        category=schedule_data.category,
        theme=schedule_data.theme,
        days_of_week=json.dumps(schedule_data.days_of_week),
        enabled=schedule_data.enabled
    )
    
    db.add(new_schedule)
    db.commit()
    db.refresh(new_schedule)
    
    return {"status": "success", "message": "Schedule added successfully"}

@app.delete("/schedule/{schedule_id}")
async def delete_schedule(schedule_id: int):
    """Delete schedule entry"""
    db = next(get_db())
    schedule = db.query(ScheduleEntry).filter(ScheduleEntry.id == schedule_id).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    db.delete(schedule)
    db.commit()
    
    return {"status": "success", "message": "Schedule deleted successfully"}

@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    """Video history page"""
    db = next(get_db())
    
    # Get all videos with pagination
    page = int(request.query_params.get("page", 1))
    per_page = 12
    offset = (page - 1) * per_page
    
    videos = db.query(VideoHistory).order_by(VideoHistory.created_at.desc()).offset(offset).limit(per_page).all()
    total_videos = db.query(VideoHistory).count()
    total_pages = (total_videos + per_page - 1) // per_page
    
    return templates.TemplateResponse("history.html", {
        "request": request,
        "videos": videos,
        "current_page": page,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages
    })

@app.get("/video/{video_id}")
async def video_details(video_id: int, request: Request):
    """Video details modal"""
    db = next(get_db())
    video = db.query(VideoHistory).filter(VideoHistory.id == video_id).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return templates.TemplateResponse("video_details.html", {
        "request": request,
        "video": video
    })

@app.get("/thumbnail/{video_id}")
async def get_thumbnail(video_id: int):
    """Serve video thumbnail"""
    db = next(get_db())
    video = db.query(VideoHistory).filter(VideoHistory.id == video_id).first()
    
    if not video or not video.thumbnail_path or not os.path.exists(video.thumbnail_path):
        # Return default thumbnail
        return FileResponse("static/images/default_thumbnail.png")
    
    return FileResponse(video.thumbnail_path)

@app.get("/download/{video_id}")
async def download_video(video_id: int):
    """Download video file"""
    db = next(get_db())
    video = db.query(VideoHistory).filter(VideoHistory.id == video_id).first()
    
    if not video or not video.video_path or not os.path.exists(video.video_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        video.video_path,
        media_type='video/mp4',
        filename=f"{video.title}.mp4"
    )

@app.get("/create", response_class=HTMLResponse)
async def create_page(request: Request):
    """Content creation page"""
    return templates.TemplateResponse("create.html", {
        "request": request,
        "video_themes": VIDEO_THEMES
    })

@app.post("/create/video")
async def create_video(
    background_tasks: BackgroundTasks,
    category: str = Form(...),
    theme: str = Form(...),
    custom_script: Optional[str] = Form(None)
):
    """Create a new video"""
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    # Add to background tasks
    background_tasks.add_task(create_video_task, category, theme, custom_script)
    
    return {"status": "success", "message": "Video creation started"}

async def create_video_task(category: str, theme: str, custom_script: Optional[str]):
    """Background task to create video"""
    try:
        db = next(get_db())
        
        # Generate content
        if custom_script:
            # Use custom script
            content = VideoContent(
                title=f"Custom {theme} Video",
                description=f"Custom {category} content",
                tags=[category, theme, "shorts"],
                thumbnail_path="",
                script=custom_script,
                hook="Custom content hook",
                cta="Like and subscribe!",
                category=category,
                estimated_duration=60,
                trending_score=75.0
            )
        else:
            # Generate AI content
            content = agent.content_generator.generate_viral_content(category, [])
        
        # Create video
        video_path = await agent.video_generator.create_video(
            script=content.script,
            category=category,
            title=content.title
        )
        
        # Save to history
        video_record = VideoHistory(
            title=content.title,
            description=content.description,
            category=category,
            theme=theme,
            thumbnail_path=content.thumbnail_path,
            video_path=video_path,
            script=content.script,
            trending_score=content.trending_score,
            upload_status="created"
        )
        
        db.add(video_record)
        db.commit()
        
        print(f"✅ Video created: {content.title}")
        
    except Exception as e:
        print(f"❌ Video creation failed: {e}")

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings and configuration page"""
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "config": {
            "youtube_api_key": config_manager.youtube.api_key[:10] + "..." if config_manager.youtube.api_key else "",
            "youtube_client_id": config_manager.youtube.client_id,
            "openai_api_key": config_manager.ai.openai_api_key[:10] + "..." if config_manager.ai.openai_api_key else "",
            "email_username": config_manager.email.username,
            "notification_email": config_manager.email.notification_email,
            "upload_times": config_manager.schedule.upload_times
        }
    })

@app.post("/settings/update")
async def update_settings(config_data: AgentConfig):
    """Update configuration settings"""
    try:
        # Update configuration
        if config_data.youtube_api_key and not config_data.youtube_api_key.endswith("..."):
            config_manager.youtube.api_key = config_data.youtube_api_key
        
        if config_data.youtube_client_id:
            config_manager.youtube.client_id = config_data.youtube_client_id
        
        if config_data.youtube_client_secret and not config_data.youtube_client_secret.endswith("..."):
            config_manager.youtube.client_secret = config_data.youtube_client_secret
        
        if config_data.openai_api_key and not config_data.openai_api_key.endswith("..."):
            config_manager.ai.openai_api_key = config_data.openai_api_key
        
        if config_data.email_username:
            config_manager.email.username = config_data.email_username
        
        if config_data.email_password and not config_data.email_password.endswith("..."):
            config_manager.email.password = config_data.email_password
        
        if config_data.notification_email:
            config_manager.email.notification_email = config_data.notification_email
        
        # Save configuration
        config_manager.save_config()
        
        return {"status": "success", "message": "Settings updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")

@app.get("/api/themes/{category}")
async def get_themes(category: str):
    """Get themes for a category"""
    return {"themes": VIDEO_THEMES.get(category, {})}

@app.get("/api/stats")
async def get_stats():
    """Get dashboard statistics"""
    db = next(get_db())
    
    # Video statistics
    total_videos = db.query(VideoHistory).count()
    successful_uploads = db.query(VideoHistory).filter(VideoHistory.upload_status == "success").count()
    pending_uploads = db.query(VideoHistory).filter(VideoHistory.upload_status == "created").count()
    
    # Performance over time (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_videos = db.query(VideoHistory).filter(VideoHistory.created_at >= thirty_days_ago).all()
    
    daily_stats = {}
    for video in recent_videos:
        date_key = video.created_at.strftime("%Y-%m-%d")
        if date_key not in daily_stats:
            daily_stats[date_key] = {"videos": 0, "views": 0}
        daily_stats[date_key]["videos"] += 1
        daily_stats[date_key]["views"] += video.views or 0
    
    return {
        "total_videos": total_videos,
        "successful_uploads": successful_uploads,
        "pending_uploads": pending_uploads,
        "success_rate": (successful_uploads / total_videos * 100) if total_videos > 0 else 0,
        "daily_stats": daily_stats
    }

@app.post("/api/upload/{video_id}")
async def upload_video(video_id: int, background_tasks: BackgroundTasks):
    """Upload a video to YouTube"""
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    db = next(get_db())
    video = db.query(VideoHistory).filter(VideoHistory.id == video_id).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Add to background tasks
    background_tasks.add_task(upload_video_task, video_id)
    
    return {"status": "success", "message": "Upload started"}

async def upload_video_task(video_id: int):
    """Background task to upload video"""
    try:
        db = next(get_db())
        video = db.query(VideoHistory).filter(VideoHistory.id == video_id).first()
        
        if not video:
            return
        
        # Create VideoContent object
        content = VideoContent(
            title=video.title,
            description=video.description,
            tags=[video.category, video.theme, "shorts"],
            thumbnail_path=video.thumbnail_path,
            script=video.script,
            hook="",
            cta="",
            category=video.category,
            estimated_duration=60,
            trending_score=video.trending_score
        )
        
        # Upload to YouTube
        upload_result = await agent._upload_to_youtube(video.video_path, content)
        
        if upload_result:
            video.youtube_id = upload_result.get("id")
            video.upload_status = "success"
            video.uploaded_at = datetime.utcnow()
        else:
            video.upload_status = "failed"
        
        db.commit()
        print(f"✅ Video uploaded: {video.title}")
        
    except Exception as e:
        print(f"❌ Upload failed: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)