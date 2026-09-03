from flask import Flask
from flask_cors import CORS
from services.database_api import Base, engine

def create_app():
    app = Flask(__name__)
    CORS(app)

    # Ensure all tables exist (single Base)
    from models.subject import Subject
    from models.student import Student
    from models.project_requirement import ProjectRequirement
    from models.group import Group
    from models.recommendation import Recommendation

    Base.metadata.create_all(bind=engine)

    from routes.normal_ui import ui_bp
    from routes.ai_mode import ai_bp
    from routes.recommendations import rec_bp

    app.register_blueprint(ui_bp, url_prefix="/ui")
    app.register_blueprint(ai_bp, url_prefix="/ai")
    app.register_blueprint(rec_bp, url_prefix="/recommendations")

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
d