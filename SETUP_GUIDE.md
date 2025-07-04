# YouTube Agent Setup Guide - Version 1.0 & 1.2
*Step-by-step instructions explained simply*

## 🛠️ What You Need Before Starting

### 1. Install Python
- Go to [python.org](https://python.org) and download Python 3.8 or newer
- During installation, **check the box** that says "Add Python to PATH"
- To test: Open terminal/command prompt and type `python --version`

### 2. Get API Keys (Required for both versions)

#### YouTube API Key:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable "YouTube Data API v3"
4. Create credentials → API Key
5. Copy and save this key

#### OpenAI API Key (for AI content):
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up/login
3. Go to API Keys section
4. Create new secret key
5. Copy and save this key

---

## 📦 Version 1.0 Setup (Command Line Version)

### Step 1: Download the Files
```bash
# Create a folder for your project
mkdir youtube-agent
cd youtube-agent

# You should have these files:
# - improved_youtube_agent.py
# - improved_content_generator.py
# - video_generator.py
# - secure_config.py
# - requirements.txt
```

### Step 2: Install Required Packages
```bash
pip install -r requirements.txt
```

### Step 3: Set Up Configuration
```bash
python secure_config.py
```

**What happens:** A setup wizard will ask you for:
- Your YouTube API key
- Your OpenAI API key  
- Video upload settings
- Content preferences

**Just follow the prompts and paste your API keys when asked.**

### Step 4: Run the Agent
```bash
python improved_youtube_agent.py
```

**What it does:**
- Creates videos automatically
- Uploads them to YouTube
- Sends you email notifications
- Runs on a schedule you set

### Step 5: Stop the Agent
- Press `Ctrl+C` to stop the program

---

## 🌐 Version 1.2 Setup (Web Interface Version)

### Step 1: Download All Files
```bash
# Create a folder for version 1.2
mkdir youtube-agent-v1.2
cd youtube-agent-v1.2

# You should have these files:
# Backend files:
# - web_interface.py
# - improved_youtube_agent.py
# - improved_content_generator.py
# - video_generator.py
# - secure_config.py
# - run_dashboard.py
# - requirements.txt

# Templates folder with:
# - templates/base.html
# - templates/dashboard.html
# - templates/schedule.html
# - templates/history.html
# - templates/settings.html
```

### Step 2: Install Web Requirements
```bash
pip install -r requirements.txt
```

### Step 3: Set Up Configuration (First Time Only)
```bash
python secure_config.py
```

**Same setup wizard as Version 1.0 - enter your API keys.**

### Step 4: Start the Web Interface
```bash
python run_dashboard.py
```

**What you'll see:**
```
✅ Starting YouTube Agent Dashboard...
✅ All requirements satisfied
🌐 Dashboard running at: http://localhost:8000
📱 Mobile friendly interface available
```

### Step 5: Open Your Browser
1. Open any web browser
2. Go to: `http://localhost:8000`
3. You'll see a beautiful dashboard!

### Step 6: Using the Web Interface

#### Dashboard Page:
- See your video statistics
- Quick buttons to create videos
- View recent uploads

#### Schedule Page:
- Set when videos should be created
- Choose themes (Gaming, Anime, Educational)
- Use templates: Beginner (2/day), Growth (4/day), Pro (6/day)

#### History Page:
- See all your videos with thumbnails
- Download videos to your computer
- Delete unwanted videos
- Search and filter videos

#### Settings Page:
- Update your API keys
- Test connections
- Export/import your settings

---

## 🚀 Quick Start Guides

### Version 1.0 (5 minutes):
1. Download files → Install requirements → Run setup → Start agent
2. It runs in the background automatically
3. Check your email for upload notifications

### Version 1.2 (5 minutes):
1. Download files → Install requirements → Run setup → Start dashboard
2. Open browser to `localhost:8000`
3. Click "Generate AI Video" for your first video!

---

## 🔧 Common Issues & Solutions

### "Python not found"
- **Solution:** Reinstall Python and check "Add to PATH"

### "pip not found"  
- **Solution:** Use `python -m pip install -r requirements.txt`

### "API key invalid"
- **Solution:** Double-check your keys in the settings page (v1.2) or re-run `secure_config.py` (v1.0)

### "Port already in use" (Version 1.2)
- **Solution:** Close other programs or change port in `run_dashboard.py`

### "No videos being created"
- **Solution:** Check your schedule settings and ensure API keys are working

### "Videos have no audio"
- **Solution:** Check if `edge-tts` is installed: `pip install edge-tts`

---

## 📱 Using Version 1.2 Features

### Creating Your First Video:
1. Go to Dashboard
2. Click "Generate AI Video"
3. Choose theme (Gaming/Anime/Educational)
4. Select category (Epic Moments, Tutorials, etc.)
5. Click "Create Video"
6. Watch the progress bar!

### Setting Up Auto-Upload:
1. Go to Schedule page
2. Pick times you want videos uploaded
3. Choose "Auto-upload after creation"
4. Select days of the week
5. Click "Save Schedule"

### Managing Videos:
1. Go to History page
2. See all videos with thumbnails
3. Click video to preview
4. Use buttons to upload/download/delete

---

## 🎯 Pro Tips

### For Best Results:
- Use high-quality API keys (not free trial)
- Set realistic upload schedules (don't spam)
- Mix different content themes
- Check your videos before auto-uploading

### Version Choice:
- **Use 1.0 if:** You want set-and-forget automation
- **Use 1.2 if:** You want control and visual interface

### Storage:
- Videos are saved in `output/` folder
- Thumbnails in `thumbnails/` folder  
- Database file: `youtube_agent.db` (v1.2 only)

---

## 🆘 Getting Help

### If Something Breaks:
1. Check the terminal/command prompt for error messages
2. Restart the program
3. Re-run the setup if needed
4. Check your internet connection
5. Verify API keys are still valid

### File Structure Check:
```
youtube-agent/
├── improved_youtube_agent.py
├── improved_content_generator.py
├── video_generator.py
├── secure_config.py
├── requirements.txt
└── (for v1.2 add:)
    ├── web_interface.py
    ├── run_dashboard.py
    └── templates/
        ├── base.html
        ├── dashboard.html
        ├── schedule.html
        ├── history.html
        └── settings.html
```

**🎉 That's it! You're ready to create amazing YouTube content automatically!**