import asyncio
import json
import random
from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import init_db, get_db, async_session
from app.models import Question, User, TestAttempt, Response, DerivedMetrics
from app.metrics_engine import compute_metrics
from app.ai_report import generate_diagnostic_report

app = FastAPI(title="SAT Math Diagnostic")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
async def startup():
    await init_db()


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("landing.html", {
        "request": request,
    }, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/test", response_class=HTMLResponse)
async def test_page(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Question))
    all_questions = result.scalars().all()

    if len(all_questions) < 12:
        questions = all_questions
    else:
        questions = random.sample(list(all_questions), 12)

    attempt = TestAttempt()
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)

    questions_data = []
    for q in questions:
        questions_data.append({
            "id": q.id,
            "question_text": q.question_text,
            "option_a": q.option_a,
            "option_b": q.option_b,
            "option_c": q.option_c,
            "option_d": q.option_d,
            "ideal_time_seconds": q.ideal_time_seconds,
            "has_numeric": q.numeric_answer is not None,
        })

    return templates.TemplateResponse("test.html", {
        "request": request,
        "questions": json.dumps(questions_data),
        "attempt_id": attempt.id,
        "question_count": len(questions_data),
    }, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.post("/api/submit")
async def submit_test(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.json()
    attempt_id = body.get("attempt_id")
    answers = body.get("answers", [])

    attempt = await db.get(TestAttempt, attempt_id)
    if not attempt:
        return JSONResponse({"error": "Invalid attempt"}, status_code=400)

    question_ids = [a["question_id"] for a in answers]
    result = await db.execute(select(Question).where(Question.id.in_(question_ids)))
    questions = {q.id: q for q in result.scalars().all()}

    responses_data = []
    for ans in answers:
        q = questions.get(ans["question_id"])
        if not q:
            continue

        selected = ans.get("selected_answer", "")
        is_correct = selected.upper() == q.correct_answer.upper() if selected else False
        numeric_distance = None
        if q.numeric_answer is not None and ans.get("numeric_input") is not None:
            try:
                numeric_distance = abs(float(ans["numeric_input"]) - q.numeric_answer)
            except (ValueError, TypeError):
                numeric_distance = None

        answer_changed = ans.get("answer_changed", False)
        first_answer = ans.get("first_answer")
        change_direction = "none"
        if answer_changed and first_answer:
            first_was_correct = first_answer.upper() == q.correct_answer.upper()
            if first_was_correct and not is_correct:
                change_direction = "right_to_wrong"
            elif not first_was_correct and is_correct:
                change_direction = "wrong_to_right"
            else:
                change_direction = "none"

        resp = Response(
            attempt_id=attempt_id,
            question_id=q.id,
            selected_answer=selected,
            correct=is_correct,
            confidence_level=ans.get("confidence_level", "medium"),
            time_taken_seconds=ans.get("time_taken_seconds", 0),
            start_delay_seconds=ans.get("start_delay_seconds", 0),
            answer_changed=answer_changed,
            change_direction=change_direction,
            numeric_distance_from_correct=numeric_distance,
        )
        db.add(resp)
        responses_data.append({
            "question_id": q.id,
            "selected_answer": selected,
            "correct": is_correct,
            "confidence_level": ans.get("confidence_level", "medium"),
            "time_taken_seconds": ans.get("time_taken_seconds", 0),
            "start_delay_seconds": ans.get("start_delay_seconds", 0),
            "answer_changed": answer_changed,
            "change_direction": change_direction,
            "numeric_distance_from_correct": numeric_distance,
        })

    questions_map = {}
    for qid, q in questions.items():
        questions_map[qid] = {
            "difficulty": q.difficulty,
            "ideal_time_seconds": q.ideal_time_seconds,
            "trap_type": q.trap_type,
            "numeric_answer": q.numeric_answer,
        }

    metrics = compute_metrics(responses_data, questions_map)

    attempt.raw_score = metrics["total_score"]
    dm = DerivedMetrics(
        attempt_id=attempt_id,
        carelessness_flag=metrics["carelessness_flag"],
        guess_probability=metrics["guess_probability"],
        endurance_index=metrics["endurance_index"],
        momentum_curve=metrics["momentum_curve"],
        efficiency_projection=metrics["efficiency_projection"],
        trap_sensitivity=metrics["trap_sensitivity"],
        precision_ratio=metrics["precision_ratio"],
        decision_volatility=metrics["decision_volatility"],
        cognitive_start_speed=metrics["cognitive_start_speed"],
        accuracy_by_difficulty=metrics["accuracy_by_difficulty"],
        avg_time_deviation=metrics["avg_time_deviation"],
        total_score=metrics["total_score"],
    )
    db.add(dm)

    await db.commit()

    asyncio.create_task(generate_report_background(attempt_id, metrics))

    return JSONResponse({
        "attempt_id": attempt_id,
        "score": metrics["total_score"],
        "total": len(responses_data),
    })


async def generate_report_background(attempt_id: int, metrics: dict):
    try:
        report_html = await asyncio.to_thread(_generate_report_sync, metrics)
        async with async_session() as db:
            attempt = await db.get(TestAttempt, attempt_id)
            if attempt:
                attempt.ai_report = report_html
                await db.commit()
    except Exception as e:
        print(f"Background report generation failed for attempt {attempt_id}: {e}")


def _generate_report_sync(metrics):
    import asyncio as _asyncio
    loop = _asyncio.new_event_loop()
    try:
        return loop.run_until_complete(generate_diagnostic_report(metrics))
    finally:
        loop.close()


@app.post("/api/unlock-report")
async def unlock_report(request: Request, db: AsyncSession = Depends(get_db)):
    body = await request.json()
    email = body.get("email", "").strip()
    attempt_id = body.get("attempt_id")

    if not email or not attempt_id:
        return JSONResponse({"error": "Email and attempt ID required"}, status_code=400)

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        user = User(email=email)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    attempt = await db.get(TestAttempt, attempt_id)
    if not attempt:
        return JSONResponse({"error": "Invalid attempt"}, status_code=400)

    attempt.user_id = user.id
    await db.commit()

    report_html = attempt.ai_report
    report_ready = report_html is not None and len(report_html) > 0

    return JSONResponse({
        "report": report_html or "",
        "score": attempt.raw_score,
        "report_ready": report_ready,
    })


@app.get("/api/report-status/{attempt_id}")
async def report_status(attempt_id: int, db: AsyncSession = Depends(get_db)):
    attempt = await db.get(TestAttempt, attempt_id)
    if not attempt:
        return JSONResponse({"error": "Invalid attempt"}, status_code=400)
    ready = attempt.ai_report is not None and len(attempt.ai_report) > 0
    return JSONResponse({
        "ready": ready,
        "report": attempt.ai_report or "",
        "score": attempt.raw_score,
    })


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Question).order_by(Question.id.desc()))
    questions_list = result.scalars().all()
    attempts_result = await db.execute(select(func.count(TestAttempt.id)))
    total_attempts = attempts_result.scalar() or 0
    users_result = await db.execute(select(func.count(User.id)))
    total_users = users_result.scalar() or 0
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "questions": questions_list,
        "total_questions": len(questions_list),
        "total_attempts": total_attempts,
        "total_users": total_users,
    }, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.get("/admin/add-question", response_class=HTMLResponse)
async def add_question_form(request: Request):
    return templates.TemplateResponse("add_question.html", {
        "request": request,
    }, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.post("/admin/add-question")
async def add_question(
    request: Request,
    question_text: str = Form(...),
    option_a: str = Form(...),
    option_b: str = Form(...),
    option_c: str = Form(...),
    option_d: str = Form(...),
    correct_answer: str = Form(...),
    concept: str = Form(...),
    difficulty: str = Form(...),
    ideal_time_seconds: int = Form(...),
    trap_type: str = Form(None),
    numeric_answer: float = Form(None),
    db: AsyncSession = Depends(get_db),
):
    q = Question(
        question_text=question_text,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        correct_answer=correct_answer.upper(),
        concept=concept,
        difficulty=difficulty,
        ideal_time_seconds=ideal_time_seconds,
        trap_type=trap_type if trap_type else None,
        numeric_answer=numeric_answer,
    )
    db.add(q)
    await db.commit()
    return RedirectResponse(url="/admin?success=added", status_code=303)


@app.get("/admin/edit-question/{question_id}", response_class=HTMLResponse)
async def edit_question_form(request: Request, question_id: int, db: AsyncSession = Depends(get_db)):
    q = await db.get(Question, question_id)
    if not q:
        return RedirectResponse(url="/admin?error=not_found", status_code=303)
    return templates.TemplateResponse("edit_question.html", {
        "request": request,
        "question": q,
    }, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})


@app.post("/admin/edit-question/{question_id}")
async def edit_question(
    request: Request,
    question_id: int,
    question_text: str = Form(...),
    option_a: str = Form(...),
    option_b: str = Form(...),
    option_c: str = Form(...),
    option_d: str = Form(...),
    correct_answer: str = Form(...),
    concept: str = Form(...),
    difficulty: str = Form(...),
    ideal_time_seconds: int = Form(...),
    trap_type: str = Form(None),
    numeric_answer: float = Form(None),
    db: AsyncSession = Depends(get_db),
):
    q = await db.get(Question, question_id)
    if not q:
        return RedirectResponse(url="/admin?error=not_found", status_code=303)
    q.question_text = question_text
    q.option_a = option_a
    q.option_b = option_b
    q.option_c = option_c
    q.option_d = option_d
    q.correct_answer = correct_answer.upper()
    q.concept = concept
    q.difficulty = difficulty
    q.ideal_time_seconds = ideal_time_seconds
    q.trap_type = trap_type if trap_type else None
    q.numeric_answer = numeric_answer
    await db.commit()
    return RedirectResponse(url="/admin?success=updated", status_code=303)


@app.post("/admin/delete-question/{question_id}")
async def delete_question(question_id: int, db: AsyncSession = Depends(get_db)):
    q = await db.get(Question, question_id)
    if q:
        await db.delete(q)
        await db.commit()
    return RedirectResponse(url="/admin?success=deleted", status_code=303)


@app.get("/api/questions/count")
async def question_count(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(func.count(Question.id)))
    count = result.scalar()
    return JSONResponse({"count": count})
