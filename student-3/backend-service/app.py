from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)

    from routes.normal_ui import ui_bp
    from routes.ai_mode import ai_bp
    from routes.recommendations import rec_bp

    app.register_blueprint(ui_bp, url_prefix="/ui")
    app.register_blueprint(ai_bp, url_prefix="/ai")
    app.register_blueprint(rec_bp, url_prefix="/recommendations")

    return app

<<<<<<< HEAD
=======

>>>>>>> e9c0fc0c277d73d0205f7956d635768df3270521
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
