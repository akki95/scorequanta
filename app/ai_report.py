import os
import json
from google import genai
from google.genai import types

AI_INTEGRATIONS_GEMINI_API_KEY = os.environ.get("AI_INTEGRATIONS_GEMINI_API_KEY")
AI_INTEGRATIONS_GEMINI_BASE_URL = os.environ.get("AI_INTEGRATIONS_GEMINI_BASE_URL")

client = genai.Client(
    api_key=AI_INTEGRATIONS_GEMINI_API_KEY,
    http_options={
        'api_version': '',
        'base_url': AI_INTEGRATIONS_GEMINI_BASE_URL
    }
)


async def generate_diagnostic_report(metrics: dict) -> str:
    prompt = f"""You are an elite SAT Math performance analyst with 15+ years of experience coaching students to 780+ scores.

Analyze the following student diagnostic data and produce a HIGH-AUTHORITY intelligence report.

STUDENT DATA:
{json.dumps(metrics, indent=2)}

CONTEXT:
- This was a 12-question diagnostic test (15-minute time limit)
- Total questions: 12
- Score shown is raw correct count out of 12
- accuracy_by_difficulty shows hit rate per difficulty tier
- avg_time_deviation: ratio of actual time to ideal time (1.0 = perfect pacing)
- carelessness_flag: true if student missed easy questions but got hard ones right
- decision_volatility: how answer-changing behavior affects performance
- cognitive_start_speed: average seconds before first interaction per question
- momentum_curve: accuracy across first, middle, and final thirds of test
- endurance_index: accuracy change from start to finish (negative = fatigue)
- efficiency_projection: projected seconds needed for full 44-question SAT Math section
- trap_sensitivity: which trap types the student fell for
- guess_probability: estimated rate of random guessing
- precision_ratio: average numeric distance from correct answer (if applicable)

Generate a report with these EXACT sections using HTML formatting:

<div class="report-section">
<h2>Predicted SAT Math Range</h2>
<p>Based on performance, project a realistic SAT Math score range (e.g., 620-680). Be specific and data-driven. Use the raw score out of 12, accuracy distribution, and behavioral signals.</p>
</div>

<div class="report-section">
<h2>Estimated Score Ceiling</h2>
<p>What is the maximum this student could achieve with optimized preparation? Factor in cognitive speed, precision, and behavioral patterns.</p>
</div>

<div class="report-section">
<h2>Top 3 Score Blockers</h2>
<p>Identify the 3 biggest factors preventing higher scores. Be specific — reference the actual data points.</p>
</div>

<div class="report-section">
<h2>Fastest Path to +100 Points</h2>
<p>Concrete, actionable steps to gain 100 points. Prioritize by impact.</p>
</div>

<div class="report-section">
<h2>Behavioral Analysis</h2>
<p>Analyze decision-making patterns, answer-changing behavior, and carelessness indicators.</p>
</div>

<div class="report-section">
<h2>Speed Analysis</h2>
<p>Break down pacing efficiency, time management, and cognitive start speed patterns.</p>
</div>

<div class="report-section">
<h2>Confidence Calibration</h2>
<p>How well does the student's confidence match their actual performance?</p>
</div>

<div class="report-section">
<h2>Trap Blind Spots</h2>
<p>Which question trap types does the student consistently fall for?</p>
</div>

<div class="report-section">
<h2>2-Week Tactical Plan</h2>
<p>A day-by-day focused study plan targeting the highest-impact improvements.</p>
</div>

RULES:
- Return ONLY the HTML content (the div sections). No markdown, no code blocks, no wrapper tags.
- Be data-driven — reference actual numbers from the data.
- Be concise and authoritative. No filler.
- Sound like a top-tier performance analyst, not a chatbot.
- Do NOT be generic. Every insight must connect to this student's specific data.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=8192
            )
        )
        report_html = response.text or ""
        report_html = report_html.replace("```html", "").replace("```", "").strip()
        return report_html
    except Exception as e:
        return f'<div class="report-section"><h2>Report Generation Error</h2><p>We encountered an issue generating your report. Please try again. Error: {str(e)}</p></div>'
