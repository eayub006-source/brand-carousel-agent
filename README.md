# Brand Carousel Agent

A Flask app that turns one prompt into a consistent branded carousel deck for LinkedIn or Instagram.

The visual system is based on the warm cream, sage green, and deep olive palette you shared. The generator is designed to keep the same typography feel, spacing, grid structure, and overall composition across every slide so the output looks like a single cohesive carousel rather than unrelated templates.

## What I built

- A local web app with a branded editor-style interface.
- A carousel generator that creates multiple slide images from a single prompt.
- Consistent 1080×1080 slide layouts with the same type scale and grid language.
- Download buttons for each PNG slide.
- A ZIP download for the full carousel.
- Optional local Ollama support for planning the carousel copy.
- A fallback offline generator so the app still works without any API keys.

## How the carousel works

You give the app:

- company name
- platform
- theme
- prompt or topic
- message
- tone
- audience
- keywords
- slide count

Then it produces a carousel deck where each slide stays within the same visual system:

- same brand palette
- same grid background
- same serif and sans-serif styling
- same spacing and corner treatment
- same editorial tone from slide to slide

## Files

- [app.py](app.py) - the Flask app, carousel generator, and download endpoints.
- [README.md](README.md) - project overview and usage notes.
- [QUICKSTART.md](QUICKSTART.md) - short Windows launch guide.
- [requirements.txt](requirements.txt) - Python dependencies.
- [Procfile](Procfile) - deployment entrypoint for Python hosts.
- [START.bat](START.bat) - double-click launcher for Windows.
- [START.ps1](START.ps1) - PowerShell launcher for Windows.

## Run locally

1. Open a terminal in this folder.
2. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

3. Start the app:

```powershell
python app.py
```

4. Open `http://localhost:8000`.

## Optional local AI

If you have Ollama installed, set a model before starting the app:

```powershell
$env:OLLAMA_MODEL = "llama3.1"
python app.py
```

The app will call your local Ollama server at `http://127.0.0.1:11434` when available.

## Downloading output

Every generated carousel includes:

- a preview for each slide
- an individual PNG download for each slide
- a ZIP download for the full deck

## Publishing to GitHub

This project is ready to publish, but the current workspace is not connected to a GitHub remote yet. To push it, you need to:

1. Create an empty GitHub repository.
2. Add that repo as a remote.
3. Push the `brand-post-agent` folder contents.

If you want, I can help you set up the remote and push the repository once you share the GitHub repo URL.

## Deployment

The app is also ready for simple Python hosting platforms that support `Procfile`, such as Render or Railway.

Use:

- Start command: `gunicorn app:app`
- Port: the platform will provide `PORT`