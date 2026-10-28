import os

import requests
from flask import Flask, Response, render_template, request


app = Flask(
    __name__,
    template_folder="/app/templates",
    static_folder="/app/static",
)

BACKEND_ORIGIN = os.getenv("BACKEND_ORIGIN", "").rstrip("/")

if not BACKEND_ORIGIN:
    raise RuntimeError("BACKEND_ORIGIN is required")


def proxy_request(path: str):
    url = f"{BACKEND_ORIGIN}{path}"

    if request.query_string:
        url = f"{url}?{request.query_string.decode('utf-8')}"

    headers = {}

    if request.content_type:
        headers["Content-Type"] = request.content_type

    if request.headers.get("Accept"):
        headers["Accept"] = request.headers["Accept"]

    upstream = requests.request(
        method=request.method,
        url=url,
        data=request.get_data(),
        headers=headers,
        timeout=300,
        allow_redirects=False,
    )

    response_headers = {}

    if upstream.headers.get("Content-Type"):
        response_headers["Content-Type"] = upstream.headers["Content-Type"]

    return Response(
        upstream.content,
        status=upstream.status_code,
        headers=response_headers,
    )


@app.get("/")
def index():
    return render_template("index.html", backend_url="")


@app.get("/campus-space-finder")
def finder():
    return render_template("index.html", backend_url="")


@app.get("/frontend-health")
def frontend_health():
    return {
        "status": "ok",
        "service": "student-5-cloud-frontend",
    }


@app.get("/health")
def backend_health():
    return proxy_request("/health")


@app.route(
    "/api",
    defaults={"path": ""},
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
@app.route(
    "/api/<path:path>",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
def api_proxy(path):
    suffix = f"/{path}" if path else ""
    return proxy_request(f"/api{suffix}")


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",  # noqa: S104 - required for Azure Container Apps ingress
        port=8005,
        debug=False,
    )
