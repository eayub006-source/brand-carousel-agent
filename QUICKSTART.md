# Quick Start Guide

## 🚀 Run Locally (Easiest Way)

**Option 1: Double-click (Windows)**
1. Go to the `brand-carousel-agent` folder.
2. Double-click `START.bat`
3. Your browser will open automatically.
4. Done!

**Option 2: PowerShell**
1. Open PowerShell in the folder.
2. Run:
```powershell
.\START.ps1
```

**Option 3: Manual (if scripts don't work)**
1. Open PowerShell and navigate to the folder:
```powershell
cd "c:\Users\DELL PRECision 7550\Documents\brand-carousel-agent"
```

2. Start the app:
```powershell
& "c:\Users\DELL PRECision 7550\Documents\.venv\Scripts\python.exe" app.py
```

3. Open your browser to:
```
http://localhost:8000
```

## What the app does

- **No personal API needed** — it uses a built-in brand-aware generator.
- **Respects your theme** — warm cream (#ECEEE6), sage green (#7A9060), deep olive (#2F3028).
- **Two platforms, one click** — toggle between LinkedIn and Instagram; both get unique formatting.
- **Optional OpenAI / Anthropic / Ollama support** — set API keys or an Ollama model and the app will use it for richer text generation.

## Advanced: Use AI Providers

**OpenAI**
```powershell
$env:OPENAI_API_KEY = "your-key"
$env:OPENAI_MODEL = "gpt-4o-mini"
& ".\..\..\.venv\Scripts\python.exe" app.py
```

**Anthropic**
```powershell
$env:ANTHROPIC_API_KEY = "your-key"
$env:ANTHROPIC_MODEL = "claude-3-5-sonnet-latest"
& ".\..\..\.venv\Scripts\python.exe" app.py
```

**Ollama**

1. Download a model (e.g., `ollama pull llama3.1`).
2. Start Ollama in a separate terminal.
3. Before launching the app, set the model:
```powershell
$env:OLLAMA_MODEL = "llama3.1"
& ".\..\..\.venv\Scripts\python.exe" app.py
```

The app will now send requests to `http://127.0.0.1:11434` and generate posts using your local model if it's available, otherwise it falls back gracefully to the built-in generator.

## Deploy to the Cloud

This app is ready for **Railway**, **Render**, **Heroku**, or any Python host that supports `Procfile`.

### Render.com example:

1. Push this folder to a GitHub repo.
2. Create a new Web Service on Render.
3. Connect the GitHub repo.
4. Render will automatically detect `Procfile` and use:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn app:app`
5. Deploy. Your agent is now live at `https://your-app-name.onrender.com`.

### Add a custom domain:
- Go to Render dashboard → your service → Settings → Custom Domain.
- Point your domain there.

## File Structure

```
brand-carousel-agent/
  ├── app.py           # The Flask app (all-in-one)
  ├── requirements.txt # Dependencies
  ├── Procfile         # Deployment config
  ├── README.md        # Full documentation
  └── QUICKSTART.md    # This file
```

## Customization Tips

**Want to change the brand colors?**  
Edit `DEFAULT_THEME` in `app.py` lines 18–24.

**Want different platform guidelines?**  
Edit `PLATFORM_GUIDES` in `app.py` lines 27–35.

**Want to add more platforms (TikTok, Twitter)?**  
Add a new entry to `PLATFORM_GUIDES` and create a `generate_tiktok()` function.

## Troubleshooting

**App won't start?**  
Make sure you're using the right Python path:
```powershell
& ".\..\..\.venv\Scripts\python.exe" --version
```
Should show `Python 3.14.2.final.0` or similar.

**Posts aren't generating?**  
Check that Flask is installed:
```powershell
& ".\..\..\.venv\Scripts\pip.exe" list | Select-String Flask
```

**Want to share this with others?**  
Deploy it. Once live, teammates can visit the URL and generate posts without needing any setup.

---

**Ready to generate?** Just run the start command and open localhost:8000.
