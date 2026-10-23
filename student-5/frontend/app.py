import os
from flask import Flask, render_template

app = Flask(__name__)
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "http://localhost:8055")

@app.get("/")
def index():
    return render_template("index.html", backend_url=BACKEND_PUBLIC_URL)

@app.get("/campus-space-finder")
def finder():
    return render_template("index.html", backend_url=BACKEND_PUBLIC_URL)

@app.get("/health")
def health():
    return {"status": "ok", "service": "student-5-frontend"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8005)  # noqa: S104 - required for Docker networking
