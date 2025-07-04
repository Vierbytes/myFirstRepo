#!/usr/bin/env python3
"""
YouTube Agent Dashboard Launcher
Launch the web interface for YouTube automation
"""

import sys
import os
import uvicorn
from pathlib import Path

def main():
    """Launch the YouTube Agent Dashboard"""
    print("🚀 Starting YouTube Agent Dashboard v1.2")
    print("=" * 50)
    
    # Check if we're in the correct directory
    if not Path("web_interface.py").exists():
        print("❌ Error: web_interface.py not found!")
        print("Please run this script from the YouTube Agent directory.")
        sys.exit(1)
    
    # Check if templates directory exists
    if not Path("templates").exists():
        print("❌ Error: templates directory not found!")
        print("Please ensure all template files are in the templates/ directory.")
        sys.exit(1)
    
    # Create required directories
    Path("static").mkdir(exist_ok=True)
    Path("static/images").mkdir(exist_ok=True)
    
    print("✅ All files found")
    print("\n📱 Dashboard Features:")
    print("   • Schedule Management - Set upload times and themes")
    print("   • Video History - View all created videos with thumbnails")
    print("   • Settings - Configure API keys and preferences")
    print("   • Real-time Creation - Create videos with custom themes")
    print("   • Bulk Operations - Upload or delete multiple videos")
    
    print("\n🌐 Starting web server...")
    print("   • Dashboard URL: http://localhost:8000")
    print("   • Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        # Start the FastAPI server
        uvicorn.run(
            "web_interface:app",
            host="127.0.0.1",
            port=8000,
            reload=True,
            access_log=False
        )
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped by user")
        print("Thanks for using YouTube Agent!")
    except Exception as e:
        print(f"\n❌ Error starting dashboard: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure all dependencies are installed: pip install -r requirements.txt")
        print("2. Check if port 8000 is available")
        print("3. Ensure you have proper permissions")

if __name__ == "__main__":
    main()