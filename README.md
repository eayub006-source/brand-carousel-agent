# Brand Carousel Agent

Generate cohesive branded carousel decks for LinkedIn and Instagram from a single prompt.

Brand Carousel Agent is a Flask-based web app that creates visually consistent carousel slides with a unified typography system, spacing structure, editorial layout style, and branded color palette.

The app generates complete multi-slide carousel decks locally, exports PNG slides, and packages the full deck as a ZIP download.

## ✨ What's New (v2.0)

### PPTX Theme Extraction & Smart Design
- **Intelligent carousel structure** with auto-generated headers, hooks, bullet points, CTAs, and footers
- **Page numbering system** (e.g., "THE PROBLEM — 03 / 06") on every slide
- **Swipe-to-next cues** on first slide for better UX
- **Smart layout zones**: Header, headline, hook line, numbered bullets, CTA, footer message, and brand footer
- **PPTX-aligned theme**: Extracts colors, fonts, and design system from custom PPTX presentations
- **Premium editorial design**: Serif typography (Georgia, Calibri), strategic whitespace, grid-based composition

### Multi-LLM Support
- **OpenAI integration** (GPT-4o, GPT-4o-mini) for advanced carousel copy planning
- **Anthropic Claude** (Claude 3.5 Sonnet) for high-quality AI generation
- **Ollama support** for local/offline models (Llama3.1, etc.)
- **Automatic provider detection** with graceful fallback to offline generation
- **Zero API key required** mode - works completely offline with intelligent defaults

### Enhanced User Interface
- **Slide outline field** for custom carousel structure (e.g., "Cover → Problem → Solution → Vision → CTA")
- **Website/handle field** for brand identity in footer
- **Theme selector** matching your PPTX design
- **Smart form validation** with helpful error messages
- **Real-time preview** of generated carousels

## Features

- ✅ Generate branded carousel slides from one prompt
- ✅ Keep a consistent visual identity across every slide
- ✅ Use 1080×1080 optimized slide formatting
- ✅ Apply an editorial-inspired typography and layout system
- ✅ Export individual PNG slides
- ✅ Download complete carousel decks as ZIP files
- ✅ Use optional OpenAI, Anthropic, or Ollama integration for AI-generated copy
- ✅ Fall back to offline generation without API keys
- ✅ Extract and apply custom PPTX themes
- ✅ Generate intelligent slide structures with headers, hooks, and pagination
- ✅ Auto-detect best available LLM provider (OpenAI → Anthropic → Ollama → Offline)
- ✅ Support custom slide outlines for precise carousel planning
- ✅ Deploy to Vercel with zero configuration

## How It Works

Provide:

- Company name
- Platform
- Theme (auto-detects PPTX-based themes)
- Topic or prompt
- Message
- Tone
- Audience
- Keywords
- Website / handle (optional)
- Slide outline (optional - e.g., "Cover → Problem → Solution → Vision → Follow-up")
- Slide count

The app then generates a cohesive carousel deck while maintaining:

- Consistent typography (serif headlines, italic accents)
- Unified spacing and composition (grid-based layout)
- Shared color palette (PPTX-extracted or preset themes)
- Structured editorial design (headers, hooks, bullets, CTAs, footers)
- Intelligent pagination (page numbers on every slide)
- Smart slide structure (auto-generated or custom-defined)

## Project Structure

- [app.py](app.py) - Flask app, carousel generator, multi-LLM integration, and download endpoints
- [README.md](README.md) - Project documentation
- [QUICKSTART.md](QUICKSTART.md) - Quick Windows setup guide
- [requirements.txt](requirements.txt) - Python dependencies
- [Procfile](Procfile) - Deployment entrypoint for Python hosts
- [START.bat](START.bat) - Windows launcher with auto-restart
- [START.ps1](START.ps1) - PowerShell launcher with color output
- [RUN_LOCAL.bat](RUN_LOCAL.bat) - Dedicated Windows local runner
- [OPEN_LOCAL.bat](OPEN_LOCAL.bat) - Browser auto-opener utility
- [test_app.py](test_app.py) - Quick verification script for imports and runtime
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

The agent can plan carousel copy with OpenAI, Anthropic, or a local Ollama model. If no API keys are present, it automatically falls back to the offline planner.

**Auto-Detection Priority:**
The app automatically detects and uses the first available provider in this order:
1. OpenAI (if `OPENAI_API_KEY` is set)
2. Anthropic Claude (if `ANTHROPIC_API_KEY` is set)
3. Ollama (if `OLLAMA_MODEL` is set)
4. Offline generation (always available, no keys needed)

**OpenAI Setup**
```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:OPENAI_MODEL = "gpt-4o-mini"  # or gpt-4o, gpt-4-turbo, etc.
python app.py
```

**Anthropic Claude Setup**
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
$env:ANTHROPIC_MODEL = "claude-3-5-sonnet-latest"  # or claude-3-opus, etc.
python app.py
```

**Ollama Setup (Local)**
```powershell
# First, install Ollama from https://ollama.ai
# Then pull a model: ollama pull llama3.1
$env:OLLAMA_MODEL = "llama3.1"  # or mistral, neural-chat, etc.
python app.py
```

**Force a Specific Provider (Optional)**
```powershell
$env:LLM_PROVIDER = "openai"  # or "anthropic", "ollama", "offline"
python app.py
```

## Output

Each generated carousel includes:

- **Slide previews** in the web interface
- **Individual PNG downloads** for each slide
- **Full ZIP export** of the complete carousel deck (ready for upload to LinkedIn, Instagram, etc.)
- **Slide metadata** (page numbers, section labels, brand info)

## Design System

### Typography
- **Headlines**: Serif font (Georgia, Calibri) at 52-72pt for impact
- **Body text**: Clean sans-serif at 28-32pt for readability
- **Accents**: Italicized hook lines and CTAs for emphasis

### Layout Structure
Each slide includes intelligent zones:
- **Header**: Section label + page count (e.g., "THE INSIGHT — 04 / 06")
- **Headline**: Large serif text for primary message
- **Hook**: Italic supporting text to draw reader in
- **Bullets**: Numbered list items (max 3-4 per slide)
- **CTA**: Call-to-action aligned with brand tone
- **Footer**: Brand name (left) + page indicator or swipe cue (right)

### Color Palette
The app includes preset themes and supports custom PPTX-extracted themes:
- **Warm cream, sage green, olive**: Premium editorial palette
- **Deep neutrals**: Professional, trustworthy aesthetic
- **Custom themes**: Extract from your own PPTX presentations

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
