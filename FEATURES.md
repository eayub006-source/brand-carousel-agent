# Brand Carousel Agent - Feature Guide

## 🎯 Quick Feature Overview

### 1. PPTX-Aligned Design System
Generate carousels that **perfectly match your brand's PPTX presentations**.

**What it does:**
- Automatically extracts colors from your PPTX file
- Applies your brand's typography (Calibri, Georgia, etc.)
- Generates slides with consistent editorial aesthetic
- Maintains your brand's visual identity across all 6-20 slides

**How to use:**
1. Upload or reference your PPTX file in the theme selector
2. The agent extracts: colors, fonts, layout preferences
3. All generated carousels will follow your brand's design system

**Example:**
- Your PPTX uses: Cream (#ECEEE6), Sage Green (#7A9060), Deep Olive (#2F3028)
- Generated carousels use: Exact same colors automatically
- No manual color picking needed!

---

### 2. Intelligent Carousel Structure
The agent **knows where to place elements** without you needing to specify every detail.

**Smart Layout System:**
- **Header**: Section label + page count (e.g., "THE PROBLEM — 03 / 06")
- **Hook**: Italic line that draws readers in
- **Headlines**: Large serif text for impact
- **Bullets**: Numbered points (auto-formatted)
- **CTA**: Call-to-action aligned with your tone
- **Footer**: Brand name + page indicator or swipe cue

**Smart Slide Structure:**
The agent understands carousel flow:
1. **Cover Slide** — Hook, headline, brand intro
2. **Problem Slides** — Issue + context
3. **Insight Slides** — Aha moments & solutions
4. **Action Slides** — What to do next
5. **Closing** — Brand message + follow-up link

---

### 3. Multi-LLM Provider Support
Choose your **AI brainpower**—or go offline.

#### 🤖 OpenAI (GPT-4o, GPT-4o-mini)
- Best for creative, nuanced copy
- Fastest generation (2-5 seconds per carousel)
- Most reliable for complex requests
- Cost-effective with mini models

**Setup:**
```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:OPENAI_MODEL = "gpt-4o-mini"
python app.py
```

#### 🧠 Anthropic Claude (Claude 3.5 Sonnet)
- Excellent for thoughtful, brand-aligned messaging
- Great at understanding complex briefs
- Strong at maintaining tone consistency
- Privacy-conscious option

**Setup:**
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
$env:ANTHROPIC_MODEL = "claude-3-5-sonnet-latest"
python app.py
```

#### 🖥️ Ollama (Local Models)
- Run completely offline
- No API costs
- No rate limits
- Use Llama3.1, Mistral, etc.

**Setup:**
```powershell
# Install from https://ollama.ai
# Pull a model: ollama pull llama3.1
$env:OLLAMA_MODEL = "llama3.1"
python app.py
```

#### 📴 Offline Mode (Always Available)
- No API keys? No problem!
- Works completely offline
- Uses intelligent defaults
- Generates professional carousels anyway

**Setup:**
```powershell
python app.py  # Just run it—no env vars needed
```

#### 🎯 How Auto-Detection Works
The app checks in this order and uses the **first available**:
1. ✅ OpenAI API key present? Use GPT-4o-mini
2. ✅ Anthropic API key present? Use Claude 3.5 Sonnet
3. ✅ Ollama model configured? Use local model
4. ✅ None available? Use offline generation

**Force a specific provider:**
```powershell
$env:LLM_PROVIDER = "anthropic"  # Ignore others, use only Claude
python app.py
```

---

### 4. Custom Slide Outline Control
Tell the agent **exactly what structure you want**.

**What it does:**
- Override auto-generated slide structure
- Create custom carousel flows
- Mix and match slide types

**Example outline:**
```
Cover → Problem → Solution → Vision → CTA → Follow-up
```

**How to use:**
1. In the form, fill "Slide outline" field
2. List slide types separated by arrows or commas
3. Agent generates exactly that sequence

**Valid slide types:**
- Cover
- Problem
- Insight
- Solution
- Vision
- Follow-up
- CTA
- Scenario
- Root cause
- Approach

---

### 5. Brand Identity Fields
Make every carousel **uniquely yours**.

#### Website/Handle
- Your brand name or domain
- Social media handle
- Appears in footer of every slide
- Example: "www.sereai.com" or "@yourbrand"

#### Company Name
- Your official brand name
- Used in cover slide
- Maintains consistency across carousels

#### Theme
- Select your PPTX-based theme
- Choose preset themes
- Apply specific color palettes
- Example: "Warm cream, sage green, deep olive"

---

### 6. Carousel Customization Fields

#### Topic/Prompt
- Main subject of your carousel
- Example: "How continuous memory transforms clinical insights"
- Sets overall message direction

#### Message
- Core takeaway
- Example: "Clinical insight through continuous memory"
- Distilled into 1-2 sentences

#### Tone
- How your message is delivered
- Example: "calm, premium, and editorial"
- Options: professional, casual, urgent, warm, technical, etc.

#### Audience
- Who sees this carousel
- Example: "customers, prospects, and community followers"
- Shapes language and depth

#### Keywords
- Topics to emphasize
- Example: "clarity, trust, calm, editorial"
- Ensures message consistency

---

### 7. Export & Download Options

#### Individual PNG Slides
- Download each slide separately
- Perfect for testing/editing
- Ready for social media

#### Complete ZIP Deck
- All slides in one download
- Organized folder structure
- Ready to upload to LinkedIn, Instagram, etc.

#### Slide Preview
- See results in browser
- Review before download
- Make adjustments and regenerate

---

### 8. Deployment Options

#### 🖥️ Local Development
- Windows: Run `START.bat` or `START.ps1`
- Flask dev server at http://localhost:8000
- Access: 127.0.0.1:8000 (local only) or 192.168.1.6:8000 (network)

#### ☁️ Vercel Deployment
- One-click deploy to free cloud hosting
- Live URL in 2-5 minutes
- Access from anywhere
- Share with team members

**Steps:**
1. Push to GitHub
2. Go to https://vercel.com
3. Import the repo
4. Click "Deploy"
5. Get live URL instantly

#### 🚀 Other Platforms
- Render.com (free tier available)
- Railway.app
- Fly.io
- Any Python host with Gunicorn support

---

### 9. Real-World Use Cases

#### 📱 LinkedIn Post Series
```
Prompt: "How AI transforms customer support"
Outline: Problem → Solution → Benefits → CTA
Theme: Professional, trustworthy
Result: 6-slide deck for LinkedIn carousel
```

#### 🎯 Product Launch
```
Prompt: "Announcing new feature X"
Message: "What customers have been asking for"
Tone: Exciting, accessible
Result: 8-slide teaser campaign
```

#### 💡 Thought Leadership
```
Topic: "Industry trends we're seeing"
Audience: Enterprise leaders
Tone: Editorial, insightful
Result: Authoritative, premium carousel
```

#### 🤝 Community Engagement
```
Prompt: "Behind the scenes of our research"
Tone: Warm, human, accessible
Audience: Community followers
Result: Engaging, relatable carousel series
```

---

### 10. Advanced Tips

#### 🎨 Maximize Visual Impact
- Use specific, vivid imagery descriptions
- Include colors that match your theme
- Mention premium or editorial tone
- Reference specific metrics or insights

#### 📊 Better AI Output
- Be specific about audience
- Provide context (industry, pain point)
- Mention brand values in tone
- Specify desired outcome in CTA

#### ⚡ Faster Generation
- Use GPT-4o-mini (faster than full GPT-4o)
- Keep prompts focused (2-3 sentences)
- Use slide outline (less LLM thinking needed)
- Reuse themes and tones

#### 🔄 Iteration Workflow
1. Generate first version
2. Download and review
3. Adjust prompt (tone, structure, keywords)
4. Regenerate
5. Compare both versions
6. Pick the best

---

## 🎓 Getting Started

### Minimal Setup (5 minutes)
1. Clone the repo
2. `python -m pip install -r requirements.txt`
3. `python app.py`
4. Open http://localhost:8000
5. Fill the form and generate your first carousel!

### Advanced Setup (10 minutes)
1. Get OpenAI or Anthropic API key (optional)
2. Set environment variables
3. Run app
4. Generate with AI power!

### Deploy to Vercel (2 minutes)
1. Push to GitHub
2. Import on Vercel
3. Click Deploy
4. Share live URL

---

## 📞 Questions?

- **Local not working?** Run `test_app.py` to diagnose
- **LLM not activating?** Check env vars with `echo $env:OPENAI_API_KEY`
- **Carousel looks off?** Try different theme or slide outline
- **Deployment errors?** Check Vercel logs for Python errors
