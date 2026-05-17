# Brand Carousel Agent

Generate cohesive branded carousel decks for LinkedIn and Instagram from a single prompt.

Brand Carousel Agent is a Flask-based web app that creates visually consistent carousel slides with a unified typography system, spacing structure, editorial layout style, and branded color palette.

The app generates complete multi-slide carousel decks locally, exports PNG slides, and packages the full deck as a ZIP download.

## Features

- Generate branded carousel slides from one prompt
- Keep a consistent visual identity across every slide
- Use 1080×1080 optimized slide formatting
- Apply an editorial-inspired typography and layout system
- Export individual PNG slides
- Download complete carousel decks as ZIP files
- Use optional OpenAI, Anthropic, or Ollama integration for AI-generated copy
- Fall back to offline generation without API keys

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
- Website / handle (optional)
- Slide outline (optional)
- Slide count

The app then generates a cohesive carousel deck while maintaining:

- Consistent typography
- Unified spacing and composition
- Shared color palette
- Structured grid layouts
- Matching editorial tone across slides

## Project Structure

- [app.py](app.py) - Flask app, carousel generator, and download endpoints
- [README.md](README.md) - Project documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick Windows setup guide
- [requirements.txt](requirements.txt) - Python dependencies
- [Procfile](Procfile) - Deployment entrypoint for Python hosts
- [START.bat](START.bat) - Windows launcher
- [START.ps1](START.ps1) - PowerShell launcher
- [api/index.py](api/index.py) - Vercel Python entrypoint
- [vercel.json](vercel.json) - Vercel routing and bundle config

## Run Locally

1. Clone the repository.
2. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

3. Start the app:

```powershell
python app.py
```

4. Open `http://localhost:8000`.

## Optional AI Providers (OpenAI, Anthropic, Ollama)

The agent can plan carousel copy with OpenAI, Anthropic, or a local Ollama model. If no keys are present it falls back to the offline planner.

**OpenAI**
```powershell
$env:OPENAI_API_KEY = "your-key"
$env:OPENAI_MODEL = "gpt-4o-mini"
python app.py
```

**Anthropic**
```powershell
$env:ANTHROPIC_API_KEY = "your-key"
$env:ANTHROPIC_MODEL = "claude-3-5-sonnet-latest"
python app.py
```

**Ollama**
```powershell
$env:OLLAMA_MODEL = "llama3.1"
python app.py
```

Optional: set `LLM_PROVIDER` to `openai`, `anthropic`, or `ollama` to force a provider.

## Output

Each generated carousel includes:

- Slide previews
- Individual PNG downloads
- Full ZIP export of the carousel deck

## Deployment

The app is ready for deployment on Python hosting platforms such as Render, Railway, Fly.io, or other Procfile-compatible hosts.

Start command:

```powershell
gunicorn app:app
```

The host should provide the `PORT` environment variable automatically.

### Deploy on Vercel

This project includes a Vercel Python entrypoint in [api/index.py](api/index.py) and routing in [vercel.json](vercel.json).

1. Create a new Vercel project from your GitHub repo.
2. Set the project root to the `brand-carousel-agent` folder if Vercel asks for a root directory.
3. Let Vercel auto-detect the Python runtime.
4. Deploy.

Vercel will use the Flask app through the Python runtime. The app keeps its fallback image generator, so it does not depend on a live Ollama server in production.

If you want to reduce bundle size further, the Python runtime docs recommend excluding unnecessary files with `functions.excludeFiles` in [vercel.json](vercel.json).

## Future Improvements

- Custom brand themes
- Additional slide layout presets
- Animated carousel exports
- AI-assisted design variations
- Social platform export presets

## License

MIT License
