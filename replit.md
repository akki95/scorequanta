# SAT Math Diagnostic Web App

## Overview
A production-style lightweight SAT Math diagnostic tool that predicts SAT Math scores using behavioral and performance analytics. It measures not just correctness but timing, confidence calibration, decision volatility, and cognitive patterns across a 15-minute, 12-question diagnostic test.

## Tech Stack
- **Backend**: Python FastAPI with async endpoints
- **Database**: PostgreSQL (Replit built-in)
- **Frontend**: Jinja2 templates, vanilla JavaScript, minimal CSS
- **AI**: Gemini (via Replit AI Integrations) for diagnostic report generation

## Project Structure
```
app/
  __init__.py
  main.py           - FastAPI app, routes, API endpoints
  models.py          - SQLAlchemy ORM models
  database.py        - Async database engine/session setup
  metrics_engine.py  - Behavioral analytics computation
  ai_report.py       - Gemini-powered diagnostic report generation
  templates/
    landing.html     - Landing page with CTA
    test.html        - Test engine with timer and tracking
    add_question.html - Admin question form
  static/
    style.css        - Professional minimal styling
```

## Key Features
- Zero-login 15-minute diagnostic test
- 12 randomly selected questions per attempt
- Global countdown timer with auto-submit
- Per-question behavioral tracking (start delay, time taken, confidence, answer changes)
- Computed intelligence metrics (carelessness, decision volatility, momentum curve, endurance, etc.)
- AI-generated diagnostic report via Gemini
- Email gate before report reveal
- Admin route at /add-question for adding questions

## Database Schema
- **questions**: Question bank with difficulty, concept, trap types
- **users**: Email-based user storage
- **test_attempts**: Test session records with scores and AI reports
- **responses**: Per-question response data with behavioral metrics
- **derived_metrics**: Computed analytics per attempt

## Running
```
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

## Environment Variables
- DATABASE_URL: PostgreSQL connection string (auto-set)
- AI_INTEGRATIONS_GEMINI_API_KEY: Gemini API key (auto-set via Replit AI Integrations)
- AI_INTEGRATIONS_GEMINI_BASE_URL: Gemini base URL (auto-set)
- SESSION_SECRET: Session secret key

## Recent Changes
- 2026-02-08: Initial build with full diagnostic flow, metrics engine, Gemini AI reports, 15 seeded SAT questions
