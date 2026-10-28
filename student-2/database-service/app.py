from flask import Flask, jsonify, request
import os
import sqlite3

app = Flask(__name__)
DATABASE_NAME = os.getenv("DATABASE_NAME", "/app/data/skill_exchange.db")

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def validate_payload(payload):
    required = ["student_id", "student_name", "skill_offered", "skill_wanted", "availability"]
    missing = [field for field in required if payload.get(field) in (None, "")]
    if missing:
        return "Missing required fields: " + ", ".join(missing)
    try:
        if int(payload["student_id"]) <= 0:
            return "student_id must be a positive integer"
    except (TypeError, ValueError):
        return "student_id must be a positive integer"
    if payload.get("status", "active") not in {"active", "inactive"}:
        return "status must be active or inactive"
    return None


def get_listing_or_none(conn, listing_id):
    return conn.execute(
        """
        SELECT
            listing_id, student_id, student_name, skill_offered, skill_wanted,
            availability, description, status, created_at, updated_at
        FROM skill_exchange_listings
        WHERE listing_id = ?
        """,
        (listing_id,),
    ).fetchone()


@app.get("/")
def health():
    conn = get_db_connection()
    count = conn.execute("SELECT COUNT(*) FROM skill_exchange_listings").fetchone()[0]
    conn.close()
    return jsonify({"service": "student-2-skill-exchange-database", "status": "running", "records": count}), 200


@app.get("/listings")
def get_listings():
    include_inactive = request.args.get("include_inactive", "false").lower() == "true"
    conn = get_db_connection()

    if include_inactive:
        rows = conn.execute(
            """
            SELECT
                listing_id, student_id, student_name, skill_offered, skill_wanted,
                availability, description, status, created_at, updated_at
            FROM skill_exchange_listings
            ORDER BY listing_id
            """
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT
                listing_id, student_id, student_name, skill_offered, skill_wanted,
                availability, description, status, created_at, updated_at
            FROM skill_exchange_listings
            WHERE status = ?
            ORDER BY listing_id
            """,
            ("active",),
        ).fetchall()

    conn.close()
    return jsonify([dict(row) for row in rows]), 200


@app.get("/listings/search")
def search_listings():
    skill = request.args.get("skill", "").strip()
    if not skill:
        return jsonify({"error": "skill query is required"}), 400
    like = f"%{skill}%"
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT
            listing_id, student_id, student_name, skill_offered, skill_wanted,
            availability, description, status, created_at, updated_at
        FROM skill_exchange_listings
        WHERE status = 'active'
          AND (skill_offered LIKE ? COLLATE NOCASE OR skill_wanted LIKE ? COLLATE NOCASE)
        ORDER BY listing_id
        """,
        (like, like),
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows]), 200


@app.get("/listings/<int:listing_id>")
def get_listing(listing_id):
    conn = get_db_connection()
    row = get_listing_or_none(conn, listing_id)
    conn.close()
    if row is None:
        return jsonify({"error": "Listing not found"}), 404
    return jsonify(dict(row)), 200


@app.post("/listings")
def create_listing():
    payload = request.get_json(silent=True) or {}
    error = validate_payload(payload)
    if error:
        return jsonify({"error": error}), 400
    conn = get_db_connection()
    cursor = conn.execute(
        """
        INSERT INTO skill_exchange_listings (
            student_id, student_name, skill_offered, skill_wanted,
            availability, description, status, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            int(payload["student_id"]), str(payload["student_name"]).strip(),
            str(payload["skill_offered"]).strip(), str(payload["skill_wanted"]).strip(),
            str(payload["availability"]).strip(), str(payload.get("description", "")).strip(),
            payload.get("status", "active"),
        ),
    )
    listing_id = cursor.lastrowid
    conn.commit()
    row = get_listing_or_none(conn, listing_id)
    conn.close()
    return jsonify({"listing": dict(row)}), 201


@app.put("/listings/<int:listing_id>")
def update_listing(listing_id):
    payload = request.get_json(silent=True) or {}
    error = validate_payload(payload)
    if error:
        return jsonify({"error": error}), 400
    conn = get_db_connection()
    existing = get_listing_or_none(conn, listing_id)
    if existing is None:
        conn.close()
        return jsonify({"error": "Listing not found"}), 404
    conn.execute(
        """
        UPDATE skill_exchange_listings
        SET student_id = ?, student_name = ?, skill_offered = ?, skill_wanted = ?,
            availability = ?, description = ?, status = ?, updated_at = CURRENT_TIMESTAMP
        WHERE listing_id = ?
        """,
        (
            int(payload["student_id"]), str(payload["student_name"]).strip(),
            str(payload["skill_offered"]).strip(), str(payload["skill_wanted"]).strip(),
            str(payload["availability"]).strip(), str(payload.get("description", "")).strip(),
            payload.get("status", "active"), listing_id,
        ),
    )
    conn.commit()
    row = get_listing_or_none(conn, listing_id)
    conn.close()
    return jsonify({"listing": dict(row)}), 200


@app.delete("/listings/<int:listing_id>")
def deactivate_listing(listing_id):
    conn = get_db_connection()
    existing = get_listing_or_none(conn, listing_id)
    if existing is None:
        conn.close()
        return jsonify({"error": "Listing not found"}), 404
    conn.execute(
        "UPDATE skill_exchange_listings SET status = 'inactive', updated_at = CURRENT_TIMESTAMP WHERE listing_id = ?",
        (listing_id,),
    )
    conn.commit()
    row = get_listing_or_none(conn, listing_id)
    conn.close()
    return jsonify({"message": "Listing deactivated", "listing": dict(row)}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False)  # noqa: S104 - container service must listen outside loopback
