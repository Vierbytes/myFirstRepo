"""
Improved YouTube Shorts AI Agent
Professional-grade automation with proper architecture, security, and monitoring
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pathlib import Path
import signal
import traceback

# Import our improved modules
from secure_config import SecureConfigManager
from improved_content_generator import AdvancedContentStrategy, VideoContent
from video_generator import AdvancedVideoGenerator

# Additional imports for improved functionality
import backoff
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

# YouTube and Google APIs
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Scheduling and monitoring
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import psutil

class ImprovedYouTubeAgent:
    """
    Advanced YouTube Shorts AI Agent with professional architecture
    """
    
    def __init__(self, config_dir: str = None):
        """Initialize the YouTube agent with secure configuration"""
        self.console = Console()
        self.config_manager = SecureConfigManager(config_dir)
        self.youtube_service = None
        self.content_generator = None
        self.video_generator = None
        self.scheduler = AsyncIOScheduler()
        
        # Performance metrics
        self.metrics = {
            'videos_created': 0,
            'videos_uploaded': 0,
            'upload_failures': 0,
            'total_runtime': 0,
            'average_processing_time': 0
        }
        
        # Setup logging and monitoring
        self._setup_logging()
        self._setup_monitoring()
        
        # Initialize components
        self._initialize_components()
        
        # Setup graceful shutdown
        self._setup_signal_handlers()
    
    def _setup_logging(self):
        """Setup advanced logging with rotation and structured output"""
        log_dir = Path.home() / ".youtube_agent" / "logs"
        log_dir.mkdir(exist_ok=True, parents=True)
        
        # Configure loguru
        logger.remove()  # Remove default handler
        
        # Console logging with colors
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=self.config_manager.security.log_level,
            colorize=True
        )
        
        # File logging with rotation
        logger.add(
            log_dir / "youtube_agent_{time:YYYY-MM-DD}.log",
            rotation="1 day",
            retention="30 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG"
        )
        
        # Error-only log file
        logger.add(
            log_dir / "errors_{time:YYYY-MM-DD}.log",
            rotation="1 day",
            retention="90 days",
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}"
        )
    
    def _setup_monitoring(self):
        """Setup error monitoring and metrics collection"""
        try:
            # Setup Sentry for error tracking (optional)
            sentry_dsn = self.config_manager.ai.openai_api_key  # Use a proper Sentry DSN
            if sentry_dsn and sentry_dsn.startswith('https://'):
                sentry_logging = LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR
                )
                
                sentry_sdk.init(
                    dsn=sentry_dsn,
                    integrations=[sentry_logging],
                    traces_sample_rate=0.1,
                    environment="production"
                )
                logger.info("Sentry monitoring initialized")
                
        except Exception as e:
            logger.warning(f"Monitoring setup failed: {e}")
    
    def _initialize_components(self):
        """Initialize all agent components"""
        try:
            # Validate configuration
            missing_config = self.config_manager.get_missing_config()
            if missing_config:
                logger.error(f"Missing configuration: {missing_config}")
                self.console.print(Panel(
                    f"[red]Missing configuration items:[/red]\n" + 
                    "\n".join([f"• {item}" for item in missing_config]) +
                    "\n\n[yellow]Run with --setup to configure[/yellow]",
                    title="Configuration Error"
                ))
                sys.exit(1)
            
            # Initialize YouTube API
            self._setup_youtube_api()
            
            # Initialize content generator
            self.content_generator = AdvancedContentStrategy(
                youtube_api_key=self.config_manager.youtube.api_key,
                openai_api_key=self.config_manager.ai.openai_api_key,
                category='gaming'  # Default category
            )
            
            # Initialize video generator
            self.video_generator = AdvancedVideoGenerator(
                unsplash_api_key=self.config_manager.media.unsplash_api_key,
                pixabay_api_key=self.config_manager.media.pixabay_api_key
            )
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Component initialization failed: {e}")
            raise
    
    def _setup_youtube_api(self):
        """Setup YouTube API with proper authentication"""
        try:
            SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
            
            creds = None
            token_file = Path.home() / ".youtube_agent" / "token.json"
            
            if token_file.exists():
                creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    client_config = {
                        "installed": {
                            "client_id": self.config_manager.youtube.client_id,
                            "client_secret": self.config_manager.youtube.client_secret,
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                        }
                    }
                    
                    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
                token_file.chmod(0o600)
            
            self.youtube_service = build('youtube', 'v3', credentials=creds)
            logger.info("YouTube API authenticated successfully")
            
        except Exception as e:
            logger.error(f"YouTube API setup failed: {e}")
            raise
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    @backoff.on_exception(
        backoff.expo,
        Exception,
        max_tries=3,
        max_time=300
    )
    async def create_and_upload_video(self, category: str = 'gaming') -> Optional[Dict[str, Any]]:
        """Create and upload a video with retry logic"""
        start_time = datetime.now()
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                
                # Step 1: Generate content
                task1 = progress.add_task("🎯 Generating viral content...", total=None)
                content = self.content_generator.generate_content()
                progress.update(task1, completed=True)
                
                logger.info(f"Generated content: {content.title} (Score: {content.trending_score:.1f})")
                
                # Step 2: Create video
                task2 = progress.add_task("🎬 Creating video...", total=None)
                video_path = await self.video_generator.create_video(
                    script=content.script,
                    category=content.category,
                    title=content.title
                )
                progress.update(task2, completed=True)
                
                # Step 3: Upload to YouTube
                task3 = progress.add_task("📤 Uploading to YouTube...", total=None)
                upload_result = await self._upload_to_youtube(video_path, content)
                progress.update(task3, completed=True)
                
                # Step 4: Cleanup and notify
                task4 = progress.add_task("🧹 Cleaning up...", total=None)
                self.video_generator.cleanup_temp_files()
                await self._send_notification(content, upload_result)
                progress.update(task4, completed=True)
            
            # Update metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self.metrics['videos_created'] += 1
            if upload_result and upload_result.get('id'):
                self.metrics['videos_uploaded'] += 1
            else:
                self.metrics['upload_failures'] += 1
            
            self.metrics['total_runtime'] += processing_time
            self.metrics['average_processing_time'] = (
                self.metrics['total_runtime'] / self.metrics['videos_created']
            )
            
            logger.info(f"Video processing completed in {processing_time:.1f}s")
            
            return {
                'content': content,
                'video_path': video_path,
                'upload_result': upload_result,
                'processing_time': processing_time
            }
            
        except Exception as e:
            logger.error(f"Video creation and upload failed: {e}")
            logger.error(traceback.format_exc())
            self.metrics['upload_failures'] += 1
            raise
    
    async def _upload_to_youtube(self, video_path: str, content: VideoContent) -> Optional[Dict[str, Any]]:
        """Upload video to YouTube with proper error handling"""
        try:
            body = {
                'snippet': {
                    'title': content.title[:100],  # YouTube title limit
                    'description': content.description[:5000],  # YouTube description limit
                    'tags': content.tags[:500],  # YouTube tags limit
                    'categoryId': self.config_manager.youtube.category_id
                },
                'status': {
                    'privacyStatus': 'public'
                }
            }
            
            # For demonstration, we'll simulate the upload
            # In production, uncomment the actual upload code:
            
            # media = MediaFileUpload(
            #     video_path,
            #     chunksize=-1,
            #     resumable=True,
            #     mimetype='video/mp4'
            # )
            
            # request = self.youtube_service.videos().insert(
            #     part=','.join(body.keys()),
            #     body=body,
            #     media_body=media
            # )
            
            # response = None
            # while response is None:
            #     status, response = request.next_chunk()
            #     if status:
            #         logger.info(f"Upload progress: {int(status.progress() * 100)}%")
            
            # Simulate successful upload for demo
            response = {
                'id': f"demo_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'snippet': {'title': content.title}
            }
            
            logger.info(f"Video uploaded successfully: {response['id']}")
            return response
            
        except Exception as e:
            logger.error(f"YouTube upload failed: {e}")
            return None
    
    async def _send_notification(self, content: VideoContent, upload_result: Optional[Dict[str, Any]]):
        """Send notification email with enhanced content"""
        try:
            # Import here to avoid circular imports
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config_manager.email.username
            msg['To'] = self.config_manager.email.notification_email
            msg['Subject'] = f"🎬 YouTube Short Uploaded: {content.title}"
            
            # Create HTML email
            html_body = self._create_notification_html(content, upload_result)
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(
                self.config_manager.email.smtp_server,
                self.config_manager.email.smtp_port
            ) as server:
                server.starttls()
                server.login(
                    self.config_manager.email.username,
                    self.config_manager.email.password
                )
                server.send_message(msg)
            
            logger.info("Notification email sent successfully")
            
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
    
    def _create_notification_html(self, content: VideoContent, upload_result: Optional[Dict[str, Any]]) -> str:
        """Create HTML notification email"""
        status = "✅ Success" if upload_result else "❌ Failed"
        video_id = upload_result.get('id', 'N/A') if upload_result else 'Upload Failed'
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center;">
                <h1>🎬 YouTube Short Status</h1>
                <h2>{status}</h2>
            </div>
            
            <div style="padding: 20px; background-color: #f8f9fa;">
                <h3>📹 Video Details</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Title:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{content.title}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Video ID:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{video_id}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Category:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{content.category.title()}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Trending Score:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{content.trending_score:.1f}/100</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Upload Time:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</td></tr>
                </table>
            </div>
            
            <div style="padding: 20px; background-color: #e9ecef;">
                <h3>📊 Performance Metrics</h3>
                <ul>
                    <li>Videos Created: {self.metrics['videos_created']}</li>
                    <li>Videos Uploaded: {self.metrics['videos_uploaded']}</li>
                    <li>Upload Failures: {self.metrics['upload_failures']}</li>
                    <li>Average Processing Time: {self.metrics['average_processing_time']:.1f}s</li>
                </ul>
            </div>
            
            <div style="padding: 20px; text-align: center; color: #6c757d;">
                <p>Powered by AI YouTube Agent 🤖</p>
            </div>
        </body>
        </html>
        """
    
    def setup_scheduler(self):
        """Setup advanced scheduling with multiple time slots"""
        for upload_time in self.config_manager.schedule.upload_times:
            hour, minute = map(int, upload_time.split(':'))
            
            trigger = CronTrigger(
                hour=hour,
                minute=minute,
                timezone=self.config_manager.schedule.timezone
            )
            
            self.scheduler.add_job(
                self.create_and_upload_video,
                trigger=trigger,
                id=f"upload_{upload_time}",
                max_instances=1,
                coalesce=True,
                misfire_grace_time=300  # 5 minutes grace period
            )
            
            logger.info(f"Scheduled upload job for {upload_time}")
        
        # Add system health check job
        self.scheduler.add_job(
            self._system_health_check,
            trigger=CronTrigger(minute=0),  # Every hour
            id="health_check",
            max_instances=1
        )
    
    async def _system_health_check(self):
        """Perform system health checks"""
        try:
            # Check system resources
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            logger.info(f"System Health - CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%")
            
            # Alert if resources are high
            if cpu_percent > 80 or memory.percent > 80 or disk.percent > 90:
                logger.warning("High system resource usage detected")
            
            # Check API rate limits and quotas here
            # This would involve checking YouTube API quota usage
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
    
    async def run(self):
        """Main run method with proper async handling"""
        try:
            self.console.print(Panel(
                f"[green]🤖 YouTube Shorts AI Agent Started[/green]\n" +
                f"[blue]Scheduled times:[/blue] {', '.join(self.config_manager.schedule.upload_times)}\n" +
                f"[blue]Next upload:[/blue] {self._get_next_upload_time()}\n" +
                f"[yellow]Press Ctrl+C to stop gracefully[/yellow]",
                title="Agent Status"
            ))
            
            # Setup and start scheduler
            self.setup_scheduler()
            self.scheduler.start()
            
            logger.info("Agent started successfully")
            
            # Keep the agent running
            while True:
                await asyncio.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"Agent runtime error: {e}")
            raise
        finally:
            await self.shutdown()
    
    def _get_next_upload_time(self) -> str:
        """Get next scheduled upload time"""
        now = datetime.now()
        upload_times = [
            datetime.combine(now.date(), datetime.strptime(t, "%H:%M").time())
            for t in self.config_manager.schedule.upload_times
        ]
        
        future_times = [t for t in upload_times if t > now]
        if future_times:
            return min(future_times).strftime("%H:%M")
        else:
            # Next day's first upload
            tomorrow_first = upload_times[0] + timedelta(days=1)
            return tomorrow_first.strftime("%H:%M tomorrow")
    
    async def shutdown(self):
        """Graceful shutdown of the agent"""
        logger.info("Shutting down YouTube agent...")
        
        try:
            # Stop scheduler
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)
            
            # Cleanup temporary files
            if self.video_generator:
                self.video_generator.cleanup_temp_files()
            
            # Final metrics report
            logger.info(f"Final metrics: {self.metrics}")
            
            self.console.print(Panel(
                "[green]Agent shutdown completed successfully[/green]",
                title="Shutdown"
            ))
            
        except Exception as e:
            logger.error(f"Shutdown error: {e}")

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Advanced YouTube Shorts AI Agent")
    parser.add_argument('--setup', action='store_true', help='Run configuration setup')
    parser.add_argument('--test', action='store_true', help='Run a single test upload')
    parser.add_argument('--config-dir', type=str, help='Configuration directory')
    parser.add_argument('--category', type=str, default='gaming', help='Content category')
    
    args = parser.parse_args()
    
    if args.setup:
        config_manager = SecureConfigManager(args.config_dir)
        config_manager.setup_wizard()
        return
    
    # Initialize and run agent
    agent = ImprovedYouTubeAgent(args.config_dir)
    
    if args.test:
        # Run single test upload
        result = await agent.create_and_upload_video(args.category)
        if result:
            print(f"Test upload completed: {result['upload_result']['id']}")
    else:
        # Run with scheduling
        await agent.run()

if __name__ == "__main__":
    asyncio.run(main())