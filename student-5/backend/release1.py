"""Release 1 MCP and RAG routes for Student 5."""

from __future__ import annotations

import asyncio
import os
from typing import Any

import requests
from flask import Blueprint, jsonify, request
from mcp import Client

release1_bp = Blueprint("student5_release1", __name__)

ALLOWED_MCP_TOOLS = {"student5_find_campus_spaces"}


def env_enabled(name: str, default: bool = True) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def mcp_server_url() -> str:
    return os.getenv("MCP_SERVER_URL", "http://host.docker.internal:5100/mcp")


def rag_server_url() -> str:
    return os.getenv("RAG_SERVER_URL", "http://host.docker.internal:500").rstrip("/")


async def _call_mcp(tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
    async with Client(mcp_server_url()) as client:
        result = await client.call_tool(tool, arguments)
        if result.is_error:
            message = "MCP tool returned an error"
            if result.content:
                message = " ".join(str(getattr(item, "text", item)) for item in result.content)
            raise RuntimeError(message)
        if isinstance(result.structured_content, dict):
            return result.structured_content
        raise RuntimeError("MCP tool did not return structured content")


@release1_bp.post("/api/mcp")
def mcp_request():
    if not env_enabled("MCP_MODE", True):
        return jsonify({"error": "mcp_disabled", "message": "MCP Mode is disabled"}), 503

    body = request.get_json(silent=True) or {}
    tool = str(body.get("tool") or "student5_find_campus_spaces").strip()
    arguments = body.get("arguments") or {}

    if tool not in ALLOWED_MCP_TOOLS:
        return jsonify({"error": "tool_not_allowed", "allowed_tools": sorted(ALLOWED_MCP_TOOLS)}), 400
    if not isinstance(arguments, dict):
        return jsonify({"error": "arguments must be a JSON object"}), 400

    try:
        result = asyncio.run(_call_mcp(tool, arguments))
    except Exception as exc:
        return jsonify({"error": "mcp_unavailable", "message": str(exc)}), 503

    return jsonify({"status": "ok", "mode": "mcp", "tool": tool, "result": result})


@release1_bp.post("/api/rag")
def rag_request():
    if not env_enabled("RAG_MODE", True):
        return jsonify({"error": "rag_disabled", "message": "RAG Mode is disabled"}), 503

    body = request.get_json(silent=True) or {}
    query = str(body.get("query") or "").strip()
    if len(query) < 3:
        return jsonify({"error": "query must contain at least 3 characters"}), 400

    try:
        response = requests.post(
f"{rag_server_url()}/answer",
json={"caller": "student5", "query": query, "k": 5},
timeout=150,
        )
        data = response.json()
    except requests.RequestException as exc:
        return jsonify({"error": "rag_unavailable", "message": str(exc)}), 503
    except ValueError:
        return jsonify({"error": "invalid_rag_response"}), 502

    if response.status_code >= 400:
        return jsonify(data), response.status_code

    if str(data.get("answer", "")).startswith("Ollama unavailable:"):
        return jsonify({
            "status": "error",
            "mode": "rag",
            "error": "generation_unavailable",
            "message": data["answer"],
        }), 503

    # Map the shared RAG response to the frontend's expected format.
    if str(data.get("answer", "")).startswith("Ollama unavailable:"):
        return jsonify({
            "status": "error",
            "mode": "rag",
            "error": "generation_unavailable",
            "message": data["answer"],
        }), 503
    if data.get("status") == "success":
        data["status"] = "ok"

    data["sources"] = data.get("citations", [])
    data["confidence"] = data.get("confidence_category", "")
    if data.get("status") == "ok":
        if not data.get("answer"):
            return jsonify({"error": "invalid_rag_response", "message": "answer missing"}), 502
        if not isinstance(data.get("sources"), list) or not data["sources"]:
            return jsonify({"error": "invalid_rag_response", "message": "sources missing"}), 502
        if data.get("confidence") not in {"High", "Medium", "Low"}:
            return jsonify({"error": "invalid_rag_response", "message": "confidence invalid"}), 502
    elif data.get("status") == "insufficient_context":
        data["sources"] = []
        data["confidence"] = "Insufficient Context"
    else:
        return jsonify({"error": "invalid_rag_response", "upstream": data}), 502

    return jsonify({"mode": "rag", **data})


@release1_bp.get("/api/release1/health")
def release1_health():
    result = {
        "status": "ok",
        "mcp_mode": env_enabled("MCP_MODE", True),
        "rag_mode": env_enabled("RAG_MODE", True),
        "mcp_server_url": mcp_server_url(),
        "rag_server_url": rag_server_url(),
    }
    try:
        response = requests.get(f"{rag_server_url()}/health", timeout=3)
        result["rag_reachable"] = response.ok
    except requests.RequestException:
        result["rag_reachable"] = False
    return jsonify(result)
