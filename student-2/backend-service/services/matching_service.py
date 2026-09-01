import json
import re

from services.database_api import get_listings
from services.llm_client import (
    ENABLE_REVIEW_MODEL,
    OLLAMA_MODEL,
    OLLAMA_REVIEW_MODEL,
    create_chat_completion,
    parse_json_object,
)
from services.prompt_loader import load_prompt
from services.skill_profile_api import get_profile


def _norm(value):
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def _availability_tokens(value):
    return {
        token for token in re.split(r"[^a-z0-9]+", _norm(value)) if len(token) >= 3
    }


def deterministic_candidates(target, all_listings):
    """Find evidence-backed candidates before any LLM call."""
    target_offered = _norm(target.get("skill_offered"))
    target_wanted = _norm(target.get("skill_wanted"))
    target_availability = _availability_tokens(target.get("availability"))

    candidates = []
    for candidate in all_listings:
        if candidate.get("listing_id") == target.get("listing_id"):
            continue
        if candidate.get("status") != "active":
            continue

        # Minimum eligibility: candidate can teach the skill the requester wants.
        offered_match = _norm(candidate.get("skill_offered")) == target_wanted
        if not offered_match:
            continue

        mutual = _norm(candidate.get("skill_wanted")) == target_offered
        candidate_availability = _availability_tokens(candidate.get("availability"))
        availability_overlap = bool(target_availability & candidate_availability)

        score = 2
        reasons = [f"offers the requested skill ({target.get('skill_wanted')})"]
        if mutual:
            score += 2
            reasons.append(f"also wants the requester's offered skill ({target.get('skill_offered')})")
        if availability_overlap:
            score += 1
            reasons.append("has an availability overlap")

        enriched = dict(candidate)
        enriched.update({
            "score": score,
            "match_level": "Strong Match" if score >= 4 else "Partial Match",
            "reason": "; ".join(reasons),
        })

        profile = get_profile(candidate.get("student_id"))
        if profile:
            enriched["skill_profile"] = profile
        candidates.append(enriched)

    candidates.sort(key=lambda item: (-item["score"], item["listing_id"]))
    return candidates


def _evidence_for_prompt(target, candidates):
    safe_candidates = []
    for candidate in candidates:
        safe_candidates.append({
            "listing_id": candidate["listing_id"],
            "student_id": candidate["student_id"],
            "student_name": candidate["student_name"],
            "skill_offered": candidate["skill_offered"],
            "skill_wanted": candidate["skill_wanted"],
            "availability": candidate["availability"],
            "description": candidate.get("description", ""),
            "deterministic_score": candidate["score"],
            "deterministic_match_level": candidate["match_level"],
            "skill_profile": candidate.get("skill_profile"),
        })

    return {
        "requester": {
            "listing_id": target["listing_id"],
            "student_id": target["student_id"],
            "student_name": target["student_name"],
            "skill_offered": target["skill_offered"],
            "skill_wanted": target["skill_wanted"],
            "availability": target["availability"],
            "description": target.get("description", ""),
            "skill_profile": get_profile(target.get("student_id")),
        },
        "candidates": safe_candidates,
        "allowed_listing_ids": [item["listing_id"] for item in safe_candidates],
    }


def _validate_recommendations(parsed, evidence):
    allowed = set(evidence["allowed_listing_ids"])
    recommendations = parsed.get("ranked_matches")
    if not isinstance(recommendations, list):
        return False, "ranked_matches must be a list", []

    candidate_by_id = {item["listing_id"]: item for item in evidence["candidates"]}
    validated, seen = [], set()
    for item in recommendations:
        if not isinstance(item, dict):
            return False, "each recommendation must be an object", []
        try:
            listing_id = int(item.get("listing_id"))
        except (TypeError, ValueError):
            return False, "recommendation has an invalid listing_id", []
        if listing_id not in allowed:
            return False, f"unsupported listing_id {listing_id}", []
        if listing_id in seen:
            continue
        seen.add(listing_id)

        source = candidate_by_id[listing_id]
        match_level = str(item.get("match_level") or source["deterministic_match_level"]).strip()
        if match_level not in {"Strong Match", "Partial Match", "No Match"}:
            match_level = source["deterministic_match_level"]
        reason = str(item.get("reason") or source["deterministic_match_level"]).strip()

        validated.append({
            "listing_id": listing_id,
            "student_id": source["student_id"],
            "student_name": source["student_name"],
            "skill_offered": source["skill_offered"],
            "skill_wanted": source["skill_wanted"],
            "availability": source["availability"],
            "match_level": match_level,
            "reason": reason,
        })

    if not validated and allowed:
        return False, "model returned no supported candidate even though candidates exist", []
    return True, "all returned listing IDs are supported by supplied evidence", validated


def _call_primary(evidence, correction=None):
    system_prompt = load_prompt("implementation/system_prompt.txt")
    task_prompt = load_prompt("implementation/match_prompt.txt")
    user_prompt = f"""{task_prompt}\n\nVALIDATION EVIDENCE:\n{json.dumps(evidence, ensure_ascii=False, indent=2)}"""
    if correction:
        user_prompt += f"\n\nADAPTATION CORRECTION:\n{correction}"

    raw = create_chat_completion(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model=OLLAMA_MODEL,
        max_tokens=700,
        temperature=0.1,
    )
    return raw, parse_json_object(raw)


def _run_review(recommendations, evidence):
    if not ENABLE_REVIEW_MODEL:
        return "disabled", None
    review_prompt = load_prompt("review/review_prompt.txt")
    payload = {
        "recommendations": recommendations,
        "allowed_listing_ids": evidence["allowed_listing_ids"],
        "requester": evidence["requester"],
        "candidates": evidence["candidates"],
    }
    try:
        raw = create_chat_completion(
            [
                {"role": "system", "content": review_prompt},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False, indent=2)},
            ],
            model=OLLAMA_REVIEW_MODEL,
            max_tokens=350,
            temperature=0.0,
        )
        parsed = parse_json_object(raw)
        approved = bool(parsed.get("approved")) and not (parsed.get("invalid_listing_ids") or [])
        return ("approved" if approved else "review-warning"), parsed
    except Exception as exc:
        # Backend validation already guarantees supported candidate IDs; reviewer failure is recorded, not hidden.
        return "review-error", {"error": str(exc)}


def run_agentic_match(target):
    workflow = [{
        "stage": "PLAN",
        "message": "Identify requester listing, required exchange evidence, optional Skill Profile API context, and AI ranking task.",
    }]

    all_listings = get_listings(include_inactive=False)
    candidates = deterministic_candidates(target, all_listings)
    evidence = _evidence_for_prompt(target, candidates)
    workflow.append({
        "stage": "ACT",
        "message": f"Retrieved {len(candidates)} eligible candidate(s) from application data; only these IDs may be ranked by the LLM.",
    })

    if not candidates:
        workflow.extend([
            {"stage": "OBSERVE", "message": "No evidence-backed candidate exists; no candidate is invented."},
            {"stage": "ADAPT", "message": "Return no recommendation and allow the user to broaden the listing or availability."},
        ])
        return {
            "workflow": workflow,
            "recommendations": [],
            "model": OLLAMA_MODEL,
            "review_model": OLLAMA_REVIEW_MODEL if ENABLE_REVIEW_MODEL else None,
            "review_status": "not-required",
            "review": None,
        }

    _, parsed = _call_primary(evidence)
    valid, validation_message, recommendations = _validate_recommendations(parsed, evidence)
    workflow.append({
        "stage": "OBSERVE",
        "message": f"Primary output checked against allowed candidate IDs: {validation_message}.",
    })

    if not valid:
        correction = (
            f"Previous output failed validation because: {validation_message}. "
            f"Return JSON only and use listing_id values only from {evidence['allowed_listing_ids']}."
        )
        workflow.append({
            "stage": "ADAPT",
            "message": "Refine the instruction and rerun the primary model once with stricter candidate-ID constraints.",
        })
        _, parsed = _call_primary(evidence, correction=correction)
        valid, validation_message, recommendations = _validate_recommendations(parsed, evidence)
        if not valid:
            raise ValueError(f"AI output remained invalid after adaptation: {validation_message}")
    else:
        workflow.append({
            "stage": "ADAPT",
            "message": "No primary prompt correction required; continue to review and return the validated result.",
        })

    review_status, review_payload = _run_review(recommendations, evidence)
    return {
        "workflow": workflow,
        "recommendations": recommendations,
        "model": OLLAMA_MODEL,
        "review_model": OLLAMA_REVIEW_MODEL if ENABLE_REVIEW_MODEL else None,
        "review_status": review_status,
        "review": review_payload,
    }
