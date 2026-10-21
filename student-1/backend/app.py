from flask import Flask
from flask_cors import CORS

from routes import (
    projects_bp,
    tasks_bp,
    ai_bp
)

from routes.mcp_mode import mcp_bp
from routes.rag_mode import rag_bp
from routes.multi_agent_mode import multi_agent_bp


app = Flask(__name__)

CORS(app)


# Register API routes
app.register_blueprint(projects_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(mcp_bp)
app.register_blueprint(rag_bp)
app.register_blueprint(multi_agent_bp)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health", methods=["GET"])
def health():
    return {
        "status": "healthy",
        "service": "backend-service"
    }


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5001,
        debug=True
    )