from flask import Flask, jsonify
from flask_cors import CORS

from routes import normal_ui_bp, ai_mode_bp


app = Flask(__name__)

CORS(app)


app.register_blueprint(normal_ui_bp)
app.register_blueprint(ai_mode_bp)


@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "healthy",
        "service": "project-service"
    })


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5001,
        debug=True
    )