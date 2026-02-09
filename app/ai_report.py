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


def build_report_html(data: dict, metrics: dict) -> str:
    predicted_score = data.get("predicted_score", "N/A")
    score_ceiling = data.get("score_ceiling", "N/A")

    try:
        unlockable = int(str(score_ceiling).split("-")[0]) - int(str(predicted_score).split("-")[0])
    except Exception:
        unlockable = "N/A"

    primary_constraint = data.get("primary_constraint", "Not identified")
    secondary_risk = data.get("secondary_risk", "Not identified")
    monitor_zone = data.get("monitor_zone", "Not identified")

    metric_cards = data.get("metric_interpretations", [])
    metrics_html = ""
    for m in metric_cards:
        name = m.get("name", "")
        score = m.get("score", 0)
        benchmark = m.get("benchmark", "")
        interpretation = m.get("interpretation", "")
        metrics_html += f'''
        <div class="metric-card">
            <div class="metric-name">{name}</div>
            <div class="metric-score">{score}<span class="metric-max">/100</span></div>
            <div class="metric-bench">{benchmark}</div>
            <div class="metric-interp">{interpretation}</div>
        </div>'''

    try:
        friction = float(data.get("score_friction", 5.0))
    except (ValueError, TypeError):
        friction = 5.0
    friction = max(0, min(10, friction))
    friction_label = "Low Suppression" if friction <= 3 else ("Moderate" if friction <= 6 else "Severe")
    friction_desc = data.get("friction_description", "Behavioral patterns are constraining current scoring.")

    suppressors = data.get("top_suppressors", [])
    suppressor_html = ""
    for s in suppressors:
        severity = s.get("severity", "medium")
        sev_icon = {"extreme": "&#128308;", "high": "&#128992;", "moderate": "&#128993;"}.get(severity, "&#128993;")
        suppressor_html += f'''
        <div class="suppressor-card">
            <div class="suppressor-title">{sev_icon} {s.get("title", "")}</div>
            <div class="suppressor-data">Data: {s.get("data", "")}</div>
            <div class="suppressor-impact">Impact: {s.get("impact", "")}</div>
            <div class="suppressor-directive">Directive: {s.get("directive", "")}</div>
        </div>'''

    fastest_path = data.get("fastest_path", [])
    path_html = ""
    for step in fastest_path:
        path_html += f'<div class="path-item"><span class="path-check">&#10003;</span> {step}</div>'

    benchmarks = data.get("benchmarks", [])
    bench_html = ""
    for b in benchmarks:
        name = b.get("name", "")
        you = b.get("you", 0)
        top = b.get("top_scorers", 0)
        you_pct = min(100, max(5, int((you / max(top, 1)) * 100)))
        bench_html += f'''
        <div class="bench-row">
            <div class="bench-label">{name}</div>
            <div class="bench-bars">
                <div class="bench-bar-wrap">
                    <div class="bench-bar you-bar" style="width:{you_pct}%"></div>
                    <span class="bench-val">You: {you}</span>
                </div>
                <div class="bench-bar-wrap">
                    <div class="bench-bar top-bar" style="width:100%"></div>
                    <span class="bench-val">700+: {top}</span>
                </div>
            </div>
        </div>'''

    radar_labels = json.dumps(["Processing Speed", "Precision", "Endurance", "Trap Recognition", "Pacing Control", "Confidence Accuracy"])
    radar_data_vals = data.get("radar_scores", [50, 50, 50, 50, 50, 50])
    radar_data = json.dumps(radar_data_vals)

    return f'''
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
    .report-dash {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; color: #111827; }}
    .hero-card {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 16px; padding: 40px 32px; margin-bottom: 28px; text-align: center; box-shadow: 0 1px 6px rgba(0,0,0,0.04); }}
    .hero-scores {{ display: flex; justify-content: center; gap: 48px; margin-bottom: 24px; flex-wrap: wrap; }}
    .hero-metric {{ text-align: center; }}
    .hero-metric .val {{ font-size: 2.4rem; font-weight: 800; color: #111827; letter-spacing: -0.03em; }}
    .hero-metric .lbl {{ font-size: 0.75rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 4px; }}
    .unlockable {{ color: #059669; }}
    .severity-chips {{ display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }}
    .sev-chip {{ padding: 6px 14px; border-radius: 20px; font-size: 0.8rem; font-weight: 500; }}
    .sev-red {{ background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }}
    .sev-orange {{ background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; }}
    .sev-yellow {{ background: #fefce8; color: #a16207; border: 1px solid #fef08a; }}

    .section-title {{ font-size: 1.1rem; font-weight: 700; color: #111827; margin-bottom: 16px; letter-spacing: -0.01em; }}
    .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; margin-bottom: 32px; }}
    .metric-card {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px; }}
    .metric-name {{ font-size: 0.78rem; color: #9ca3af; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 6px; }}
    .metric-score {{ font-size: 1.8rem; font-weight: 800; color: #111827; }}
    .metric-max {{ font-size: 0.9rem; color: #d1d5db; font-weight: 500; }}
    .metric-bench {{ font-size: 0.78rem; color: #6b7280; margin-top: 4px; }}
    .metric-interp {{ font-size: 0.82rem; color: #374151; margin-top: 8px; line-height: 1.4; }}

    .friction-card {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 28px; margin-bottom: 28px; }}
    .friction-bar-track {{ width: 100%; height: 10px; background: #e5e7eb; border-radius: 5px; overflow: hidden; margin: 12px 0 8px; }}
    .friction-bar-fill {{ height: 100%; border-radius: 5px; background: linear-gradient(90deg, #d1d5db, #6b7280, #111827); }}
    .friction-val {{ font-size: 1.6rem; font-weight: 800; color: #111827; }}
    .friction-label-text {{ font-size: 0.82rem; color: #6b7280; }}
    .friction-desc {{ font-size: 0.88rem; color: #374151; margin-top: 8px; }}

    .radar-section {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 28px; margin-bottom: 28px; text-align: center; }}
    .radar-canvas {{ max-width: 400px; margin: 0 auto; }}

    .suppressor-card {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px; margin-bottom: 12px; }}
    .suppressor-title {{ font-size: 0.95rem; font-weight: 700; color: #111827; margin-bottom: 6px; }}
    .suppressor-data, .suppressor-impact, .suppressor-directive {{ font-size: 0.82rem; color: #4b5563; line-height: 1.5; }}

    .path-section {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 24px; margin-bottom: 28px; }}
    .path-item {{ display: flex; align-items: flex-start; gap: 8px; padding: 8px 0; font-size: 0.9rem; color: #374151; border-bottom: 1px solid #f3f4f6; }}
    .path-item:last-child {{ border-bottom: none; }}
    .path-check {{ color: #4b5563; font-weight: 700; flex-shrink: 0; }}

    .bench-section {{ background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 24px; margin-bottom: 28px; }}
    .bench-row {{ margin-bottom: 16px; }}
    .bench-row:last-child {{ margin-bottom: 0; }}
    .bench-label {{ font-size: 0.82rem; font-weight: 600; color: #374151; margin-bottom: 6px; }}
    .bench-bars {{ display: flex; flex-direction: column; gap: 4px; }}
    .bench-bar-wrap {{ display: flex; align-items: center; gap: 8px; }}
    .bench-bar {{ height: 8px; border-radius: 4px; }}
    .you-bar {{ background: #6b7280; }}
    .top-bar {{ background: #111827; }}
    .bench-val {{ font-size: 0.75rem; color: #9ca3af; white-space: nowrap; }}
</style>

<div class="report-dash">
    <div class="hero-card">
        <div class="hero-scores">
            <div class="hero-metric">
                <div class="val">{predicted_score}</div>
                <div class="lbl">Predicted Score</div>
            </div>
            <div class="hero-metric">
                <div class="val">{score_ceiling}</div>
                <div class="lbl">Score Ceiling</div>
            </div>
            <div class="hero-metric">
                <div class="val unlockable">+{unlockable}</div>
                <div class="lbl">Unlockable Points</div>
            </div>
        </div>
        <div class="severity-chips">
            <span class="sev-chip sev-red">Primary Constraint: {primary_constraint}</span>
            <span class="sev-chip sev-orange">Secondary Risk: {secondary_risk}</span>
            <span class="sev-chip sev-yellow">Monitor: {monitor_zone}</span>
        </div>
    </div>

    <div class="section-title">Key Metrics</div>
    <div class="metrics-grid">
        {metrics_html}
    </div>

    <div class="friction-card">
        <div class="section-title" style="margin-bottom:8px;">Score Friction Index</div>
        <div class="friction-val">{friction} <span style="font-size:0.9rem;color:#9ca3af;font-weight:400;">/ 10</span></div>
        <div class="friction-bar-track">
            <div class="friction-bar-fill" style="width:{int(float(friction)*10)}%"></div>
        </div>
        <div class="friction-label-text">{friction_label}</div>
        <div class="friction-desc">{friction_desc}</div>
    </div>

    <div class="radar-section">
        <div class="section-title">Performance Profile</div>
        <canvas id="radarChart" class="radar-canvas" width="400" height="400"></canvas>
    </div>

    <div class="section-title">Top Score Suppressors</div>
    {suppressor_html}

    <div class="section-title" style="margin-top:28px;">Fastest Path to +100</div>
    <div class="path-section">
        {path_html}
    </div>

    <div class="section-title">Benchmark Comparison: You vs 700+ Scorers</div>
    <div class="bench-section">
        {bench_html}
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script>
(function() {{
    const ctx = document.getElementById('radarChart');
    if (!ctx) return;
    new Chart(ctx, {{
        type: 'radar',
        data: {{
            labels: {radar_labels},
            datasets: [{{
                label: 'Your Performance',
                data: {radar_data},
                backgroundColor: 'rgba(17, 24, 39, 0.08)',
                borderColor: '#111827',
                borderWidth: 2,
                pointBackgroundColor: '#111827',
                pointRadius: 4,
            }}]
        }},
        options: {{
            responsive: true,
            scales: {{
                r: {{
                    beginAtZero: true,
                    max: 100,
                    ticks: {{ stepSize: 25, font: {{ size: 11 }}, color: '#9ca3af' }},
                    grid: {{ color: '#e5e7eb' }},
                    angleLines: {{ color: '#e5e7eb' }},
                    pointLabels: {{ font: {{ size: 12, weight: '500' }}, color: '#374151' }}
                }}
            }},
            plugins: {{
                legend: {{ display: false }}
            }}
        }}
    }});
}})();
</script>
'''


async def generate_diagnostic_report(metrics: dict) -> str:
    prompt = f"""You are an elite SAT Math performance analyst. Analyze the following student diagnostic data and return a STRUCTURED JSON response.

STUDENT DATA:
{json.dumps(metrics, indent=2)}

CONTEXT:
- 12-question diagnostic test, 15-minute time limit
- accuracy_by_difficulty: hit rate per difficulty tier
- avg_time_deviation: ratio of actual to ideal time (1.0 = perfect pacing)
- carelessness_flag: missed easy but got hard right
- decision_volatility: answer-changing impact
- cognitive_start_speed: avg seconds before first interaction
- momentum_curve: accuracy across first/middle/final thirds
- endurance_index: accuracy change start to finish (negative = fatigue)
- trap_sensitivity: which trap types student fell for
- guess_probability: estimated random guessing rate

Return ONLY valid JSON with this EXACT structure. No markdown, no code blocks, no explanation:

{{
  "predicted_score": "440-520",
  "score_ceiling": "680-730",
  "primary_constraint": "short phrase",
  "secondary_risk": "short phrase",
  "monitor_zone": "short phrase",
  "score_friction": 7.5,
  "friction_description": "One sentence max.",
  "metric_interpretations": [
    {{"name": "Cognitive Start Speed", "score": 65, "benchmark": "Top 25% score: 78", "interpretation": "Under 12 words."}},
    {{"name": "Execution Precision", "score": 50, "benchmark": "Top 25% score: 85", "interpretation": "Under 12 words."}},
    {{"name": "Pacing Discipline", "score": 40, "benchmark": "Top 25% score: 81", "interpretation": "Under 12 words."}},
    {{"name": "Trap Awareness", "score": 55, "benchmark": "Top 25% score: 80", "interpretation": "Under 12 words."}},
    {{"name": "Confidence Calibration", "score": 60, "benchmark": "Top 25% score: 82", "interpretation": "Under 12 words."}},
    {{"name": "Decision Stability", "score": 45, "benchmark": "Top 25% score: 88", "interpretation": "Under 12 words."}}
  ],
  "radar_scores": [65, 50, 40, 55, 60, 45],
  "top_suppressors": [
    {{"severity": "extreme", "title": "Short title", "data": "Specific data point", "impact": "One sentence.", "directive": "One command."}},
    {{"severity": "high", "title": "Short title", "data": "Specific data point", "impact": "One sentence.", "directive": "One command."}},
    {{"severity": "moderate", "title": "Short title", "data": "Specific data point", "impact": "One sentence.", "directive": "One command."}}
  ],
  "fastest_path": [
    "Action command 1",
    "Action command 2",
    "Action command 3",
    "Action command 4"
  ],
  "benchmarks": [
    {{"name": "Pacing Discipline", "you": 40, "top_scorers": 81}},
    {{"name": "Execution Precision", "you": 50, "top_scorers": 85}},
    {{"name": "Trap Awareness", "you": 55, "top_scorers": 80}},
    {{"name": "Confidence Calibration", "you": 60, "top_scorers": 82}}
  ]
}}

RULES:
- Return ONLY valid JSON. No markdown, no code fences, no prose.
- All scores are 0-100. predicted_score and score_ceiling are SAT scale (200-800).
- Be data-driven. Reference actual numbers from the student data.
- Interpretations must be under 12 words.
- Suppressors: Insight, Impact, Directive format. Max 3 lines each.
- Sound like a performance analyst, not a chatbot.
- Every insight must connect to this student's specific data.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=4096
            )
        )
        raw = response.text or ""
        raw = raw.replace("```json", "").replace("```", "").strip()

        report_data = json.loads(raw)
        return build_report_html(report_data, metrics)
    except json.JSONDecodeError as e:
        return _fallback_report(metrics, raw_text=raw)
    except Exception as e:
        return f'<div style="text-align:center;padding:40px;font-family:Inter,sans-serif;"><h2 style="font-size:1.2rem;color:#111;">Report Generation Error</h2><p style="color:#6b7280;">We encountered an issue generating your report. Please try again. Error: {str(e)}</p></div>'


def _fallback_report(metrics: dict, raw_text: str = "") -> str:
    score = metrics.get("total_score", 0)
    total = metrics.get("total_questions", 12)
    pct = (score / max(total, 1)) * 100

    if pct >= 80:
        predicted = "620-700"
        ceiling = "740-780"
    elif pct >= 60:
        predicted = "520-600"
        ceiling = "680-720"
    elif pct >= 40:
        predicted = "420-500"
        ceiling = "620-680"
    else:
        predicted = "320-420"
        ceiling = "560-640"

    fallback_data = {
        "predicted_score": predicted,
        "score_ceiling": ceiling,
        "primary_constraint": "Accuracy gaps on core concepts",
        "secondary_risk": "Pacing inconsistency",
        "monitor_zone": "Confidence calibration",
        "score_friction": round(max(1, 10 - pct / 10), 1),
        "friction_description": "Behavioral patterns are constraining current scoring potential.",
        "metric_interpretations": [
            {"name": "Cognitive Start Speed", "score": int(max(20, 100 - metrics.get("cognitive_start_speed", 3) * 15)), "benchmark": "Top 25% score: 78", "interpretation": "Processing delay detected on question entry."},
            {"name": "Execution Precision", "score": int(pct), "benchmark": "Top 25% score: 85", "interpretation": "Accuracy needs improvement across difficulties."},
            {"name": "Pacing Discipline", "score": int(max(20, 100 - abs(metrics.get("avg_time_deviation", 1) - 1) * 50)), "benchmark": "Top 25% score: 81", "interpretation": "Time management requires calibration."},
            {"name": "Trap Awareness", "score": 50, "benchmark": "Top 25% score: 80", "interpretation": "Trap detection is inconsistent."},
            {"name": "Confidence Calibration", "score": 55, "benchmark": "Top 25% score: 82", "interpretation": "Confidence partially misaligned with performance."},
            {"name": "Decision Stability", "score": int(max(20, 100 - metrics.get("decision_volatility", 0) * 100)), "benchmark": "Top 25% score: 88", "interpretation": "Answer changes affecting score stability."},
        ],
        "radar_scores": [60, int(pct), 50, 50, 55, 60],
        "top_suppressors": [
            {"severity": "extreme", "title": "Core Accuracy Deficit", "data": f"Score: {score}/{total}", "impact": "Fundamental accuracy limits score floor.", "directive": "Master all easy-tier concepts first."},
            {"severity": "high", "title": "Pacing Imbalance", "data": f"Avg time deviation: {metrics.get('avg_time_deviation', 'N/A')}", "impact": "Inconsistent pacing degrades later performance.", "directive": "Target 75 seconds per question."},
            {"severity": "moderate", "title": "Decision Volatility", "data": f"Volatility: {metrics.get('decision_volatility', 'N/A')}", "impact": "Answer changes may be hurting more than helping.", "directive": "Trust first instinct on medium questions."},
        ],
        "fastest_path": [
            "Achieve 95% accuracy on easy problems",
            "Slow pacing to minimum 75 seconds per question",
            "Maintain an error log for pattern recognition",
            "Identify traps before solving"
        ],
        "benchmarks": [
            {"name": "Pacing Discipline", "you": int(max(20, 100 - abs(metrics.get("avg_time_deviation", 1) - 1) * 50)), "top_scorers": 81},
            {"name": "Execution Precision", "you": int(pct), "top_scorers": 85},
            {"name": "Trap Awareness", "you": 50, "top_scorers": 80},
            {"name": "Confidence Calibration", "you": 55, "top_scorers": 82},
        ]
    }

    return build_report_html(fallback_data, metrics)
