from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from init_db import engine

app = Flask(__name__)
CORS(app)

@app.get("/status")
def status():
    """Simple health check."""
    return jsonify({"database": "online"}), 200

@app.get("/tables")
def list_tables():
    """Return list of tables in the database."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    return jsonify({"tables": tables}), 200

@app.get("/check")
def check_integrity():
    """Basic DB integrity check."""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        return jsonify({"integrity": "ok", "tables": tables}), 200
    except SQLAlchemyError as e:
        return jsonify({"integrity": "error", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000, debug=True)