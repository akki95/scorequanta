# ScoreQuanta - SAT Math Diagnostic Web App

## Overview
ScoreQuanta is a production-style lightweight SAT Math diagnostic tool that predicts SAT Math scores using behavioral and performance analytics. It measures not just correctness but timing, confidence calibration, decision volatility, and cognitive patterns across a 15-minute, 12-question diagnostic test.

## Tech Stack
- **Backend**: Python FastAPI with async endpoints
- **Database**: PostgreSQL (Replit built-in)
- **Frontend**: Jinja2 templates, vanilla JavaScript, TailwindCSS (CDN), Chart.js
- **AI**: Gemini (via Replit AI Integrations) for structured diagnostic report generation
- **Font**: Inter (Google Fonts)

## Project Structure
```
app/
  __init__.py
  main.py           - FastAPI app, routes, API endpoints
  models.py          - SQLAlchemy ORM models
  database.py        - Async database engine/session setup
  metrics_engine.py  - Behavioral analytics computation
  ai_report.py       - Gemini-powered diagnostic report (structured JSON -> dashboard HTML)
  templates/
    landing.html     - High-authority landing page with hero, CTA, feature cards
    test.html        - Test engine with progress bar, timer, orientation card, email gate, report display
    admin.html       - Admin dashboard with question management and stats
    admin_login.html - Admin login page
    add_question.html - Admin question form
    edit_question.html - Admin question edit form
  static/
    logo.png         - ScoreQuanta brand logo (transparent background)
    style.css        - Legacy styles (mostly overridden by Tailwind in templates)
```

## Key Features
- Zero-login 15-minute diagnostic test
- 12 randomly selected questions per attempt
- Visual progress bar with % completion
- Orientation header with tips (No tricks, Skip if stuck, Accuracy > speed)
- Timer with recommended pace display (~75 sec/question)
- Momentum messages at Q3, Q6, Q9
- Per-question behavioral tracking (start delay, time taken, confidence, answer changes)
- Confidence selector with no default selection and microcopy
- Computed intelligence metrics (carelessness, decision volatility, momentum curve, endurance, etc.)
- AI-generated structured diagnostic report via Gemini (JSON -> dashboard)
- Performance dashboard with Chart.js radar chart, metrics grid, severity cards, benchmark comparisons
- Email gate with value stack card before report reveal
- Background report generation
- Admin dashboard with password authentication, question CRUD, usage stats

## Database Schema
- **questions**: Question bank with difficulty, concept, trap types
- **users**: Email-based user storage
- **test_attempts**: Test session records with scores and AI reports
- **responses**: Per-question response data with behavioral metrics
- **derived_metrics**: Computed analytics per attempt

## AI Report Format
The AI prompt requests structured JSON from Gemini with fields:
- predicted_score, score_ceiling, primary_constraint, secondary_risk, monitor_zone
- score_friction (0-10), friction_description
- metric_interpretations (6 metrics with scores, benchmarks, interpretations)
- radar_scores (6 values for Chart.js radar)
- top_suppressors (severity, title, data, impact, directive)
- fastest_path (action commands)
- benchmarks (you vs 700+ scorers)
Includes fallback rendering if JSON parsing fails.

## Running
```
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

## Environment Variables
- SUPABASE_DATABASE_URL: Supabase PostgreSQL connection string (secret - full URL or just password)
- SUPABASE_HOST: Supabase pooler hostname (env var)
- SUPABASE_PORT: Supabase pooler port (env var, default 6543)
- SUPABASE_USER: Supabase database user (env var)
- SUPABASE_DB: Supabase database name (env var, default postgres)
- AI_INTEGRATIONS_GEMINI_API_KEY: Gemini API key (auto-set via Replit AI Integrations)
- AI_INTEGRATIONS_GEMINI_BASE_URL: Gemini base URL (auto-set)
- SESSION_SECRET: Session secret key
- ADMIN_PASSWORD: Admin dashboard password

## Branding
- Brand name: ScoreQuanta
- Contact email: akash@scorequanta.com
- Logo: app/static/logo.png (blue icon + text, transparent background)
- Design: Premium, calm, analytical - no gamification, no gradients, no bright colors

## Recent Changes
- 2026-02-11: Report page conversion upgrade - Sticky CTA bar (appears after 25% scroll with predicted/ceiling/unlockable scores), rebuilt expert section (single dominant CTA path, callout card with review bullets, credibility + scarcity microcopy), performance labels on metrics (Elite/Above Average/Developing/Needs Immediate Attention), outcome modeling text, renamed plan to "Score Acceleration Protocol"
- 2026-02-11: KaTeX LaTeX math rendering - Added KaTeX CDN to all templates (test, landing, admin, add/edit question). Live preview in admin question forms. Monospace textarea with LaTeX helper text. Auto-render on dynamic content. `| safe` filter for trusted admin content.
- 2026-02-10: ScoreQuanta branding - navbar with logo + Contact mailto button, positioning tagline, updated CTA ("Start Free Diagnostic"), expert interpretation card below report with mailto + email capture, page titles updated
- 2026-02-10: Fixed report generation crash - decision_volatility (string) was used in arithmetic, fallback report now handles all metric types correctly, simplified async report generation
- 2026-02-09: Complete UI overhaul - landing page (Stripe-inspired hero, CTA, feature cards), test page (progress bar, orientation card, timer reframe, momentum messages, confidence microcopy, Continue button), email capture (value stack card, curiosity headline), report (structured JSON from Gemini, performance dashboard with Chart.js radar, metrics grid, severity chips, benchmark bars, fallback rendering)
- 2026-02-08: Initial build with full diagnostic flow, metrics engine, Gemini AI reports, 15 seeded SAT questions
