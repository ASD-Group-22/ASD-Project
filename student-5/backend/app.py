import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

from release1 import release1_bp

app = Flask(__name__)
CORS(app)
app.register_blueprint(release1_bp)

DATABASE_SERVICE_URL = os.getenv("DATABASE_SERVICE_URL", "http://student-5-database:5000")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
OLLAMA_TIMEOUT_SECONDS = int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "90"))
AI_MODE = os.getenv("AI_MODE", "true").lower() == "true"
LOG_PATH = Path(os.getenv("AGENTIC_LOG_PATH", str(Path(__file__).resolve().parent / "logs" / "agentic-loop.jsonl")))
PROMPT_DIR = Path(__file__).parent / "prompts"

LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("campus-space-agent")

FACILITY_ALIASES = {
    "wifi": "Wi-Fi", "wi-fi": "Wi-Fi", "wireless": "Wi-Fi",
    "power": "Power Outlets", "power outlet": "Power Outlets", "power outlets": "Power Outlets", "charging": "Power Outlets",
    "whiteboard": "Whiteboard", "whiteboards": "Whiteboard",
    "monitor": "Monitor", "monitors": "Monitor", "screen": "Monitor",
    "projector": "Projector", "projectors": "Projector",
    "computer": "Computers", "computers": "Computers", "pc": "Computers",
    "adjustable desk": "Adjustable Desk", "large table": "Large Tables", "large tables": "Large Tables"
}


def read_prompt(name):
    return (PROMPT_DIR / name).read_text(encoding="utf-8")


def log_stage(run_id, stage, payload):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "stage": stage,
        "payload": payload,
    }
    logger.info("AGENTIC %s | run=%s | %s", stage.upper(), run_id, json.dumps(payload, ensure_ascii=False))
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def db_request(method, path, **kwargs):
    response = requests.request(method, f"{DATABASE_SERVICE_URL}{path}", timeout=10, **kwargs)
    try:
        data = response.json()
    except ValueError:
        data = {"error": response.text or "Database service returned invalid response"}
    return response.status_code, data


def ollama_json(system_prompt, user_prompt):
    if not AI_MODE:
        raise RuntimeError("AI_MODE is disabled")
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=OLLAMA_TIMEOUT_SECONDS)
    response.raise_for_status()
    content = response.json().get("message", {}).get("content", "{}")
    return json.loads(content)


def deterministic_plan(query):
    q = query.lower()
    cap = None
    patterns = [r"(?:for|fit|fits|capacity(?: of)?)\s+(\d+)", r"(\d+)\s+(?:people|persons|students|of us)"]
    for pattern in patterns:
        m = re.search(pattern, q)
        if m:
            cap = int(m.group(1)); break
    building = None
    m = re.search(r"building\s+([a-z0-9-]+)", q)
    if m:
        building = f"Building {m.group(1)}"
    noise = None
    for n in ["silent", "quiet", "moderate", "collaborative", "loud"]:
        if n in q:
            noise = n.title()
            break
    facilities = []
    for alias, canonical in FACILITY_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", q) and canonical not in facilities:
            facilities.append(canonical)
    accessibility = any(x in q for x in ["wheelchair", "accessible", "accessibility", "step-free", "step free"])
    hard = []
    if cap: hard.append("capacity")
    if accessibility: hard.append("accessibility")
    hard.extend([f"facility:{f}" for f in facilities])
    soft = []
    if building: soft.append("building")
    if noise: soft.append("noise_level")
    return {
        "capacity": cap, "building": building, "space_type": None, "noise_level": noise,
        "facilities": facilities, "accessibility_required": accessibility,
        "required_time": None, "hard_constraints": hard, "soft_constraints": soft,
        "planner": "deterministic-fallback"
    }


def plan(query):
    try:
        result = ollama_json(read_prompt("plan.txt"), query)
        result.setdefault("capacity", None)
        result.setdefault("building", None)
        result.setdefault("space_type", None)
        result.setdefault("noise_level", None)
        result.setdefault("facilities", [])
        result.setdefault("accessibility_required", False)
        result.setdefault("required_time", None)
        result.setdefault("hard_constraints", [])
        result.setdefault("soft_constraints", [])
        result["planner"] = "qwen"
        return result
    except Exception as exc:
        logger.warning("Qwen plan unavailable; using deterministic fallback: %s", exc)
        result = deterministic_plan(query)
        result["planner_error"] = str(exc)
        return result


def normalise(s):
    return str(s or "").strip().lower()


def opening_match(space, required_time):
    if not required_time:
        return True
    try:
        return space["opening_time"] <= required_time <= space["closing_time"]
    except Exception:
        return True


def evaluate_space(space, req):
    facilities = {normalise(f) for f in (space.get("facilities") or [])}
    requested_facilities = [str(f) for f in (req.get("facilities") or [])]
    missing_facilities = [f for f in requested_facilities if normalise(f) not in facilities]
    hard_failures = []
    soft_failures = []

    if req.get("capacity") and space.get("max_capacity", 0) < int(req["capacity"]):
        hard_failures.append("capacity")
    if req.get("accessibility_required") and "accessible" not in normalise(space.get("accessibility")) and "step-free" not in normalise(space.get("accessibility")):
        hard_failures.append("accessibility")
    if missing_facilities:
        hard_failures.extend([f"facility:{f}" for f in missing_facilities])
    if req.get("required_time") and not opening_match(space, req["required_time"]):
        hard_failures.append("opening_hours")

    if req.get("building") and normalise(space.get("building")) != normalise(req["building"]):
        soft_failures.append("building")
    if req.get("noise_level") and normalise(space.get("noise_level")) != normalise(req["noise_level"]):
        soft_failures.append("noise_level")
    if req.get("space_type") and normalise(req["space_type"]) not in normalise(space.get("space_type")):
        soft_failures.append("space_type")

    score = 100 - (35 * len(set(hard_failures))) - (10 * len(set(soft_failures)))
    if req.get("capacity") and space.get("max_capacity", 0) >= int(req["capacity"]):
        score += min(10, space["max_capacity"] - int(req["capacity"]))
    return {
        "space": space,
        "hard_failures": sorted(set(hard_failures)),
        "soft_failures": sorted(set(soft_failures)),
        "score": score,
        "exact": not hard_failures and not soft_failures,
        "hard_match": not hard_failures,
    }


def act(req, spaces):
    evaluated = [evaluate_space(space, req) for space in spaces]
    exact = [e for e in evaluated if e["exact"]]
    hard_matches = [e for e in evaluated if e["hard_match"]]
    return evaluated, exact, hard_matches


def observe(evaluated, exact, hard_matches):
    return {
        "spaces_checked": len(evaluated),
        "exact_match_count": len(exact),
        "hard_match_count": len(hard_matches),
        "no_match": len(hard_matches) == 0,
    }


def adapt(evaluated, exact, hard_matches):
    if exact:
        ranked = sorted(exact, key=lambda x: x["score"], reverse=True)[:3]
        return "exact_matches", [], ranked
    if hard_matches:
        ranked = sorted(hard_matches, key=lambda x: (len(x["soft_failures"]), -x["score"]))[:3]
        relaxed = sorted({f for e in ranked for f in e["soft_failures"]})
        return "relaxed_soft_preferences", relaxed, ranked
    ranked = sorted(evaluated, key=lambda x: (len(x["hard_failures"]), len(x["soft_failures"]), -x["score"]))[:3]
    relaxed = sorted({f for e in ranked for f in e["hard_failures"] + e["soft_failures"]})
    return "closest_alternatives", relaxed, ranked


def fallback_reason(item, req, mode):
    s = item["space"]
    positives = []
    if req.get("capacity") and s["max_capacity"] >= int(req["capacity"]): positives.append(f"fits at least {req['capacity']} people")
    if req.get("noise_level") and normalise(s["noise_level"]) == normalise(req["noise_level"]): positives.append(f"is {s['noise_level'].lower()}")
    wanted = {normalise(f) for f in (req.get("facilities") or [])}
    got = {normalise(f) for f in (s.get("facilities") or [])}
    if wanted:
        matched = [f for f in (req.get("facilities") or []) if normalise(f) in got]
        if matched: positives.append("has " + ", ".join(matched))
    reason = "; ".join(positives) or "is one of the closest stored campus-space matches"
    if item["hard_failures"] or item["soft_failures"]:
        reason += ". Trade-off: " + ", ".join(item["hard_failures"] + item["soft_failures"])
    return reason + "."


def explain(query, req, mode, relaxed, ranked):
    compact = [
        {
            "space_id": e["space"]["space_id"], "space_name": e["space"]["space_name"],
            "building": e["space"]["building"], "room_number": e["space"]["room_number"],
            "max_capacity": e["space"]["max_capacity"], "noise_level": e["space"]["noise_level"],
            "facilities": e["space"]["facilities"], "accessibility": e["space"]["accessibility"],
            "hard_failures": e["hard_failures"], "soft_failures": e["soft_failures"]
        } for e in ranked
    ]
    try:
        ai = ollama_json(
            read_prompt("explain.txt"),
            json.dumps({"user_request": query, "requirements": req, "mode": mode, "relaxed": relaxed, "spaces": compact}, ensure_ascii=False)
        )
        return ai
    except Exception as exc:
        logger.warning("Qwen explanation unavailable; using deterministic explanation: %s", exc)
        return {
            "summary": "Recommendations are based on the closest matching records in the campus-space database.",
            "reasons": {str(e["space"]["space_id"]): fallback_reason(e, req, mode) for e in ranked},
            "explanation_error": str(exc)
        }


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "student-5-backend", "ai_mode": AI_MODE, "mcp_mode": os.getenv("MCP_MODE", "true").lower() == "true", "rag_mode": os.getenv("RAG_MODE", "true").lower() == "true", "multi_agent_mode": os.getenv("MULTI_AGENT_MODE", "false").lower() == "true", "model": OLLAMA_MODEL})


@app.route("/api/spaces", methods=["GET", "POST"])
def spaces_collection():
    if request.method == "GET":
        status, data = db_request("GET", "/spaces")
        return jsonify(data), status
    status, data = db_request("POST", "/spaces", json=request.get_json(silent=True) or {})
    return jsonify(data), status


@app.route("/api/spaces/<int:space_id>", methods=["GET", "PUT", "DELETE"])
def space_item(space_id):
    kwargs = {}
    if request.method == "PUT":
        kwargs["json"] = request.get_json(silent=True) or {}
    status, data = db_request(request.method, f"/spaces/{space_id}", **kwargs)
    return jsonify(data), status


@app.post("/api/spaces/recommend")
def recommend():
    if not AI_MODE:
        return jsonify({"error": "AI Mode is disabled in this environment"}), 503
    body = request.get_json(silent=True) or {}
    query = str(body.get("query") or "").strip()
    if len(query) < 3:
        return jsonify({"error": "query must contain at least 3 characters"}), 400

    run_id = f"s5-{int(time.time() * 1000)}"

    # PLAN
    requirements = plan(query)
    log_stage(run_id, "plan", {"query": query, "requirements": requirements})

    # ACT
    status, spaces = db_request("GET", "/spaces")
    if status != 200:
        return jsonify({"error": "Could not retrieve campus spaces", "details": spaces}), 503
    evaluated, exact, hard_matches = act(requirements, spaces)
    log_stage(run_id, "act", {
        "action": "retrieve_and_filter_campus_spaces",
        "spaces_checked": len(spaces),
        "exact_candidates": [e["space"]["space_id"] for e in exact],
        "hard_match_candidates": [e["space"]["space_id"] for e in hard_matches]
    })

    # OBSERVE
    observation = observe(evaluated, exact, hard_matches)
    log_stage(run_id, "observe", observation)

    # ADAPT
    mode, relaxed, ranked = adapt(evaluated, exact, hard_matches)
    ai_explanation = explain(query, requirements, mode, relaxed, ranked)
    log_stage(run_id, "adapt", {
        "mode": mode,
        "relaxed_constraints": relaxed,
        "selected_space_ids": [e["space"]["space_id"] for e in ranked]
    })

    reasons = ai_explanation.get("reasons", {}) if isinstance(ai_explanation, dict) else {}
    recommendations = []
    for e in ranked:
        s = dict(e["space"])
        s["reason"] = reasons.get(str(s["space_id"])) or fallback_reason(e, requirements, mode)
        s["match"] = {
            "hard_failures": e["hard_failures"],
            "soft_failures": e["soft_failures"],
            "score": e["score"]
        }
        recommendations.append(s)

    return jsonify({
        "run_id": run_id,
        "summary": ai_explanation.get("summary", "Campus-space recommendations generated."),
        "agentic_loop": {
            "plan": requirements,
            "act": {"spaces_checked": len(spaces), "database_service": DATABASE_SERVICE_URL},
            "observe": observation,
            "adapt": {"mode": mode, "relaxed_constraints": relaxed}
        },
        "recommendations": recommendations
    })


@app.get("/api/agentic/logs")
def get_agentic_logs():
    limit = max(1, min(int(request.args.get("limit", 30)), 200))
    if not LOG_PATH.exists():
        return jsonify([])
    lines = LOG_PATH.read_text(encoding="utf-8").splitlines()[-limit:]
    return jsonify([json.loads(line) for line in lines if line.strip()])


from release2 import bp as release2_blueprint
app.register_blueprint(release2_blueprint)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8055)
