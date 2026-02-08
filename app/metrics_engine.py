from typing import Any


def compute_metrics(responses_data: list[dict], questions_map: dict[int, dict]) -> dict[str, Any]:
    total = len(responses_data)
    if total == 0:
        return _empty_metrics()

    correct_count = 0
    difficulty_correct = {"easy": 0, "medium": 0, "hard": 0}
    difficulty_total = {"easy": 0, "medium": 0, "hard": 0}
    time_deviations = []
    start_delays = []
    guess_count = 0
    trap_failures: dict[str, int] = {}
    precision_errors = []
    change_directions = []

    thirds = [[], [], []]
    third_size = max(1, total // 3)

    for i, resp in enumerate(responses_data):
        q = questions_map.get(resp["question_id"], {})
        difficulty = q.get("difficulty", "medium")
        ideal_time = q.get("ideal_time_seconds", 60)
        trap_type = q.get("trap_type")
        numeric_answer = q.get("numeric_answer")

        is_correct = resp.get("correct", False)
        if is_correct:
            correct_count += 1

        if difficulty in difficulty_correct:
            difficulty_total[difficulty] = difficulty_total.get(difficulty, 0) + 1
            if is_correct:
                difficulty_correct[difficulty] = difficulty_correct.get(difficulty, 0) + 1

        time_taken = resp.get("time_taken_seconds", 0) or 0
        if ideal_time > 0:
            deviation = time_taken / ideal_time
            time_deviations.append(deviation)

        start_delay = resp.get("start_delay_seconds", 0) or 0
        start_delays.append(start_delay)

        confidence = resp.get("confidence_level", "medium")
        if ideal_time > 0 and time_taken < (0.4 * ideal_time) and confidence == "low":
            guess_count += 1

        if trap_type and not is_correct:
            trap_failures[trap_type] = trap_failures.get(trap_type, 0) + 1

        if numeric_answer is not None and resp.get("numeric_distance_from_correct") is not None:
            precision_errors.append(resp["numeric_distance_from_correct"])

        change_dir = resp.get("change_direction")
        if change_dir and change_dir != "none":
            change_directions.append(change_dir)

        if i < third_size:
            thirds[0].append(is_correct)
        elif i < third_size * 2:
            thirds[1].append(is_correct)
        else:
            thirds[2].append(is_correct)

    accuracy_by_difficulty = {}
    for d in ["easy", "medium", "hard"]:
        if difficulty_total[d] > 0:
            accuracy_by_difficulty[d] = round(difficulty_correct[d] / difficulty_total[d], 2)
        else:
            accuracy_by_difficulty[d] = None

    avg_time_deviation = round(sum(time_deviations) / len(time_deviations), 2) if time_deviations else 0

    easy_wrong = difficulty_total["easy"] - difficulty_correct["easy"]
    hard_correct = difficulty_correct["hard"]
    carelessness_flag = easy_wrong >= 2 and hard_correct >= 1

    wrong_to_right = sum(1 for d in change_directions if d == "wrong_to_right")
    right_to_wrong = sum(1 for d in change_directions if d == "right_to_wrong")
    total_changes = len(change_directions)

    if total_changes == 0:
        decision_volatility = "stable"
    elif wrong_to_right > right_to_wrong:
        decision_volatility = "productive_switcher"
    elif right_to_wrong > wrong_to_right:
        decision_volatility = "self_saboteur"
    else:
        decision_volatility = "stable"

    cognitive_start_speed = round(sum(start_delays) / len(start_delays), 2) if start_delays else 0

    momentum_curve = {}
    for idx, label in enumerate(["first_third", "middle_third", "final_third"]):
        if thirds[idx]:
            momentum_curve[label] = round(sum(thirds[idx]) / len(thirds[idx]), 2)
        else:
            momentum_curve[label] = 0

    first_acc = momentum_curve.get("first_third", 0)
    final_acc = momentum_curve.get("final_third", 0)
    endurance_index = round(final_acc - first_acc, 2)

    total_time = sum(r.get("time_taken_seconds", 0) or 0 for r in responses_data)
    if total > 0:
        avg_per_q = total_time / total
        efficiency_projection = round(avg_per_q * 44, 1)
    else:
        efficiency_projection = 0

    guess_probability = round(guess_count / total, 2)

    precision_ratio = None
    if precision_errors:
        precision_ratio = round(sum(precision_errors) / len(precision_errors), 2)

    return {
        "total_score": correct_count,
        "accuracy_by_difficulty": accuracy_by_difficulty,
        "avg_time_deviation": avg_time_deviation,
        "carelessness_flag": carelessness_flag,
        "decision_volatility": decision_volatility,
        "cognitive_start_speed": cognitive_start_speed,
        "momentum_curve": momentum_curve,
        "endurance_index": endurance_index,
        "efficiency_projection": efficiency_projection,
        "trap_sensitivity": trap_failures if trap_failures else None,
        "guess_probability": guess_probability,
        "precision_ratio": precision_ratio,
    }


def _empty_metrics() -> dict[str, Any]:
    return {
        "total_score": 0,
        "accuracy_by_difficulty": {"easy": None, "medium": None, "hard": None},
        "avg_time_deviation": 0,
        "carelessness_flag": False,
        "decision_volatility": "stable",
        "cognitive_start_speed": 0,
        "momentum_curve": {"first_third": 0, "middle_third": 0, "final_third": 0},
        "endurance_index": 0,
        "efficiency_projection": 0,
        "trap_sensitivity": None,
        "guess_probability": 0,
        "precision_ratio": None,
    }
