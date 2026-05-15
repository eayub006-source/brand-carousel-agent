# Brand Carousel Agent

Generate cohesive branded carousel decks for LinkedIn and Instagram using a single prompt.

Brand Carousel Agent is a Flask-based web app that creates visually consistent carousel slides with a unified typography system, spacing structure, editorial layout style, and branded color palette.

The app can generate complete multi-slide carousel decks locally, export PNG slides, and package the full deck as a ZIP download.

---

## Features

- Generate branded carousel slides from a single prompt
- Consistent visual identity across every slide
- 1080×1080 optimized slide format
- Editorial-inspired typography and layout system
- Export individual PNG slides
- Download complete carousel decks as ZIP files
- Optional Ollama integration for local AI-generated copy
- Offline fallback generation without API keys

---

## How It Works

Provide:

- Company name
- Platform
- Theme
- Topic or prompt
- Message
- Tone
- Audience
- Keywords
- Slide count

The app generates a cohesive carousel deck while maintaining:

- Consistent typography
- Unified spacing and composition
- Shared color palette
- Structured grid layouts
- Matching editorial tone across slides

---

## Project Structure

```bash
.
├── app.py              # Flask app and carousel generator
├── README.md           # Project documentation
├── QUICKSTART.md       # Quick Windows setup guide
├── requirements.txt    # Python dependencies
├── Procfile            # Deployment entrypoint
├── START.bat           # Windows launcher
└── START.ps1           # PowerShell launcher
Run Locally
1. Clone the repository
git clone <your-repo-url>
cd brand-carousel-agent
2. Install dependencies
python -m pip install -r requirements.txt
3. Start the app
python app.py

Open:

http://localhost:8000
Optional Ollama Support

If Ollama is installed locally, you can enable AI-generated carousel planning and copy.

Example
$env:OLLAMA_MODEL = "llama3.1"
python app.py

The app will connect to:

http://127.0.0.1:11434

when available.

Output

Each generated carousel includes:

Slide previews
Individual PNG downloads
Full ZIP export of the carousel deck
Deployment

The app is ready for deployment on Python hosting platforms such as:

Render
Railway
Fly.io
Heroku-compatible platforms
Start Command
gunicorn app:app

The hosting platform should provide the PORT environment variable automatically.

Stack
Python
Flask
Pillow
HTML/CSS
Ollama (optional)
Future Improvements
Custom brand themes
Additional slide layout presets
Animated carousel exports
AI-assisted design variations
Social platform export presets
License

MIT License
