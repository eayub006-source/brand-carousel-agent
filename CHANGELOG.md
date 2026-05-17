# Changelog

All notable changes to Brand Carousel Agent are documented in this file.

## [2.0.0] - 2026-05-18

### ✨ Major Features Added

#### PPTX Theme Extraction & Smart Design System
- Extract colors, fonts, and typography directly from custom PPTX presentations
- Intelligent carousel structure with auto-generated layout zones:
  - Headers with section labels and page counts (e.g., "THE PROBLEM — 03 / 06")
  - Hook lines (italic) for reader engagement
  - Numbered bullet points (max 3-4 per slide)
  - Call-to-action sections aligned with brand tone
  - Footer with brand name and page indicators
- Smart swipe-to-next cues on first slide for better UX
- Premium editorial design system with:
  - Serif typography (Georgia, Calibri) for headlines
  - Strategic whitespace and grid-based composition
  - Warm cream, sage green, and deep olive color palette
  - Professional, trustworthy aesthetic

#### Multi-LLM Provider Support
- **OpenAI Integration**
  - Support for GPT-4o, GPT-4o-mini, GPT-4-turbo models
  - Full chat completion API integration with streaming support
  - Configurable via `OPENAI_API_KEY` and `OPENAI_MODEL` environment variables

- **Anthropic Claude Integration**
  - Support for Claude 3.5 Sonnet and other Claude models
  - Messages API integration
  - Configurable via `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` environment variables

- **Ollama Local Model Support**
  - Run models locally without API costs
  - Support for Llama3.1, Mistral, Neural Chat, and other models
  - Offline-first approach for privacy
  - Configurable via `OLLAMA_MODEL` environment variable

- **Automatic Provider Detection**
  - Intelligently selects available LLM in priority order:
    1. OpenAI (if API key present)
    2. Anthropic Claude (if API key present)
    3. Ollama (if model configured)
    4. Offline generation (always available as fallback)
  - Single `LLM_PROVIDER` override option for force-selection

- **Graceful Offline Fallback**
  - Works completely offline without any API keys
  - Intelligent default carousel structures
  - No connectivity issues affecting user experience

#### Enhanced User Interface
- **Slide Outline Field**
  - Custom carousel structure specification
  - Example: "Cover → Problem → Solution → Vision → Follow-up"
  - Allows precise control over slide sequencing
  - Works with or without AI providers

- **Website/Handle Field**
  - Brand identity in footer
  - Custom domain or social media handle
  - Personalizes every generated carousel

- **Theme Selector**
  - Preset themes matching PPTX designs
  - Multiple color palette options
  - Editorial and premium aesthetic choices

- **Smart Form Validation**
  - Helpful error messages
  - Required field indicators
  - Real-time feedback

- **Live Carousel Preview**
  - See slides as they're generated
  - Download individual PNG files
  - Export complete ZIP deck

#### Deployment Improvements
- **Vercel Python Runtime Support**
  - Zero-configuration deployment
  - api/index.py WSGI entrypoint
  - Automatic bundle optimization
  - Environment variable support for API keys

- **Windows Startup Scripts**
  - START.bat: Basic launcher
  - START.ps1: PowerShell launcher with color output
  - RUN_LOCAL.bat: Dedicated local runner
  - OPEN_LOCAL.bat: Auto-open browser

- **Test Utility**
  - test_app.py for quick verification
  - Validates imports and runtime
  - Useful for debugging environment issues

### 📝 Documentation Updates
- Comprehensive README.md with all v2.0 features
- Updated QUICKSTART.md with correct folder references
- Added LLM provider setup instructions
- Added design system documentation
- Project structure clearly documented
- Deployment guide updated with Vercel instructions

### 🔧 Technical Changes

#### app.py (2300+ lines)
- **Restructured BRAND and THEMES dictionary**
  - Line 35-49: THEMES dict with SEREAI palette
  - PPTX-extracted colors with hex codes
  - Support for multiple preset themes

- **Redesigned SlidePlan dataclass** (lines 74-95)
  - New fields: header, hook, bullets, cta, footer_line, footer_left, footer_right, swipe_text, theme_key
  - Intelligent structure for editorial carousel design
  - Support for custom outline specifications

- **Added LLM Integration Functions**
  - try_openai(): OpenAI API integration (lines 153-180)
  - try_anthropic(): Anthropic Claude API integration (lines 182-209)
  - try_ollama(): Ollama local model support (lines 211-238)
  - select_llm_provider(): Auto-detection with priority order
  - All functions include timeout handling and graceful fallback

- **Enhanced Helper Functions**
  - normalize_bullets(): Parse various bullet formats
  - resolve_theme_key(): Safe theme lookup with fallback
  - prompt_for_ai(): Comprehensive carousel design instructions

- **Rebuilt Drawing System**
  - draw_frame(): Uses new THEMES system
  - draw_right_text(): Right-aligned footer text
  - draw_bullets(): Numbered bullet points with formatting
  - generate_carousel_slide(): Complete redesign with new layout (lines 591-650)
  - Added proper header formatting with section label + pagination
  - Added swipe-to-next cues on first slide
  - Footer system with left (brand) and right (page/CTA) text

- **Updated Form Handling**
  - normalize_payload(): Includes theme_preset, website, slide_outline
  - Updated HTML form with new fields (lines 1080-1240)
  - Smart validation and error handling

#### Supporting Files
- **vercel.json**: Verified and optimized for Vercel Python runtime
- **api/index.py**: Confirmed WSGI entrypoint compatibility
- **requirements.txt**: All dependencies documented
- **Procfile**: Deployment configuration validated

### 🎨 Design System
- **Typography**
  - Headlines: Serif (Georgia, Calibri) at 52-72pt
  - Body: Sans-serif at 28-32pt
  - Accents: Italicized hooks and CTAs

- **Layout Structure**
  - Header: Section label + page count
  - Headline: Large serif text
  - Hook: Italic supporting text
  - Bullets: Numbered list (3-4 max)
  - CTA: Brand-aligned action
  - Footer: Brand name + page/swipe indicator

- **Color Palette**
  - Cream: #ECEEE6
  - Sage Green: #7A9060
  - Deep Olive: #2F3028
  - Additional supporting colors extracted from PPTX

### 🐛 Bug Fixes
- Fixed Flask debug mode restart issues
- Improved error handling for invalid theme presets
- Enhanced timeout handling for LLM API calls
- Better fallback behavior when providers unavailable

### 🚀 Performance
- Optimized bundle size for Vercel deployment
- Efficient PPTX theme extraction
- Streamlined LLM provider detection
- Faster startup time with improved imports

## [1.0.0] - Earlier

- Initial brand carousel agent release
- Basic carousel generation
- PNG export functionality
- ZIP deck downloads
- Ollama integration
- Vercel deployment support
