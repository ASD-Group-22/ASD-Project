import json
import os
import sqlite3
from pathlib import Path
from flask import Flask, jsonify, request

app = Flask(__name__)
DB_PATH = os.getenv("DATABASE_PATH", "/data/campus_spaces.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS campus_spaces (
    space_id INTEGER PRIMARY KEY AUTOINCREMENT,
    space_name TEXT NOT NULL,
    building TEXT NOT NULL,
    building_level TEXT NOT NULL,
    room_number TEXT NOT NULL,
    max_capacity INTEGER NOT NULL CHECK(max_capacity > 0),
    space_type TEXT NOT NULL,
    noise_level TEXT NOT NULL,
    facilities TEXT NOT NULL DEFAULT '[]',
    accessibility TEXT NOT NULL DEFAULT '',
    opening_time TEXT NOT NULL DEFAULT '08:00',
    closing_time TEXT NOT NULL DEFAULT '22:00',
    description TEXT NOT NULL DEFAULT '',
    image_url TEXT NOT NULL DEFAULT ''
);
"""

SEED = [
    (
        "UTS Reading Room",
        "Building 2 - UTS Central",
        "5",
        "Reading Room",
        1,
        "Silent Study",
        "Silent",
        ["Wi-Fi", "Power Outlets", "Individual Desks", "Desk Lights"],
        "Wheelchair Accessible",
        "08:00",
        "22:00",
        "Real silent and quiet study space in the UTS Reading Room. "
        "Entry is through Building 2 Level 5, with additional desks on Level 6.",
        "https://drupal.uts.edu.au/sites/default/files/styles/wysiwyg_large_x1/public/2020-08/IMG_6123_500x500.jpg?itok=P7xoRwmF",
    ),
    (
        "UTS Library Group Study Floor",
        "Building 2 - UTS Central",
        "7",
        "Library Level 7",
        8,
        "Collaborative Study",
        "Collaborative",
        ["Wi-Fi", "Power Outlets", "Computers", "Study Pods", "Whiteboards"],
        "Wheelchair Accessible",
        "08:00",
        "22:00",
        "The collaborative floor of UTS Library, intended for group work. "
        "Bookable study spaces and computer bays are available.",
        "https://www.lib.uts.edu.au/sites/default/files/2021-02/46_N7A8863_UTS%20Central_Andy%20Roberts_hr.jpg",
    ),
    (
        "UTS Library Quiet Floor",
        "Building 2 - UTS Central",
        "8",
        "Library Level 8",
        1,
        "Quiet Study",
        "Quiet",
        ["Wi-Fi", "Power Outlets", "Computers", "Individual Booths"],
        "Wheelchair Accessible",
        "08:00",
        "22:00",
        "The designated quiet floor of UTS Library, suitable for focused "
        "individual study. Computer bays and study booths are available.",
        "https://www.lib.uts.edu.au/sites/default/files/2021-02/46_N7A8863_UTS%20Central_Andy%20Roberts_hr.jpg",
    ),
    (
        "UTS Library Silent Floor",
        "Building 2 - UTS Central",
        "9",
        "Library Level 9",
        1,
        "Silent Study",
        "Silent",
        ["Wi-Fi", "Power Outlets", "Computers", "Individual Booths"],
        "Wheelchair Accessible",
        "08:00",
        "22:00",
        "The designated silent floor of UTS Library for distraction-free "
        "individual study.",
        "https://www.lib.uts.edu.au/sites/default/files/2021-02/IMG_5596.jpg",
    ),
    (
        "UTS Library Assistive Technology Rooms",
        "Building 2 - UTS Central",
        "8",
        "Assistive Technology Rooms",
        1,
        "Accessible Study",
        "Quiet",
        [
            "Wi-Fi",
            "Power Outlets",
            "Computer",
            "Accessible Furniture",
            "Assistive Software",
        ],
        "Enhanced Accessibility - registration required",
        "08:00",
        "22:00",
        "Accessible study rooms for students registered with UTS Accessibility "
        "Services. Includes accessible furniture and specialist software.",
        "https://www.uts.edu.au/globalassets/sites/default/files/styles/media_gallery_embed_carousel/public/2024-07/latr-02.jpg",
    ),
    (
        "UTS Library Level 8 Terraces",
        "Building 2 - UTS Central",
        "8",
        "Library Terraces",
        12,
        "Outdoor Study",
        "Moderate",
        ["Wi-Fi", "Solar Charging Benches", "Outdoor Seating"],
        "Wheelchair Accessible",
        "08:00",
        "22:00",
        "Outdoor study terraces attached to UTS Library. The northern terrace "
        "includes solar-powered charging benches.",
        "https://www.lib.uts.edu.au/sites/default/files/2021-02/IMG_5849.jpg",
    ),
    (
        "FEIT Learning Precinct",
        "Building 11",
        "5",
        "CB11.05.300",
        30,
        "Collaborative Study",
        "Moderate",
        [
            "Wi-Fi",
            "Power Outlets",
            "Computers",
            "Engineering Software",
            "Collaborative Tables",
        ],
        "Wheelchair Accessible",
        "06:00",
        "22:00",
        "The real FEIT Learning Precinct general study area. It supports "
        "individual academic work and engineering or IT group projects.",
        "https://www.uts.edu.au/globalassets/sites/default/files/styles/wysiwyg_generic_large_x1/public/2018-10/annazhu_utsfeit_2523.jpg",
    ),
    (
        "Viaduct Group Study Room",
        "Building 11",
        "5",
        "CB11.05.206",
        6,
        "Group Study Room",
        "Moderate",
        ["Wi-Fi", "Power Outlets", "Collaborative Workspace"],
        "Wheelchair Accessible",
        "06:00",
        "22:00",
        "Real bookable group study room inside the FEIT Learning Precinct. "
        "Available primarily for FEIT student group work.",
        "https://s3.studentvip.com.au/photos/entrance-183280-small.jpg",
    ),   
    (
        "Building 7 Online Learning Rooms",
        "Building 7 - Vicki Sara Building",
        "2",
        "CB07.02",
        1,
        "Online Learning Room",
        "Quiet",
        ["Wi-Fi", "Power Outlets", "Sit-Stand Desk", "Chair", "Lounge"],
        "Wheelchair Accessible",
        "08:00",
        "22:00",
        "One of eight real individual online-learning rooms on Building 7 "
        "Level 2. Designed for joining online classes without distractions.",
        "https://drupal.uts.edu.au/sites/default/files/styles/wysiwyg_generic_large_x1/public/2022-02/online-learning-room.jpg?itok=y_VfUzj8",
    ),
    (
        "Building 7 Level 2 Study Space",
        "Building 7 - Vicki Sara Building",
        "2",
        "CB07.02 Study Area",
        20,
        "Collaborative Study",
        "Moderate",
        [
            "Wi-Fi",
            "Power Outlets",
            "Collaborative Tables",
            "Individual Booths",
            "Student Kitchen",
        ],
        "Wheelchair Accessible",
        "08:00",
        "22:00",
        "Real Building 7 study area containing collaborative tables, "
        "individual booths, bookable rooms and a nearby student kitchen.",
        "https://drupal.uts.edu.au/sites/default/files/styles/wysiwyg_large_x1/public/2020-03/CB07_Andrew-Worssam_500x500.jpg?itok=mHBIkyVg",
    ),
    (
        "Building 5A Group Study Rooms",
        "Building 5A - Haymarket",
        "Various",
        "Bookable Group Study Rooms",
        6,
        "Group Study Room",
        "Collaborative",
        ["Wi-Fi", "Power Outlets", "Whiteboard"],
        "Wheelchair Accessible",
        "08:00",
        "22:00",
        "Real bookable group study rooms in Building 5A, equipped with "
        "whiteboards for collaboration and project work.",
        "https://www.lib.uts.edu.au/sites/default/files/2021-02/IMG_5596.jpg",
    ),
    (
        "Building 5A Online Learning Rooms",
        "Building 5A - Haymarket",
        "Various",
        "Online Learning Rooms",
        1,
        "Online Learning Room",
        "Quiet",
        ["Wi-Fi", "Power Outlets", "Wide-Screen Monitor", "Individual Desk"],
        "Wheelchair Accessible",
        "08:00",
        "22:00",
        "Real bookable individual rooms in Building 5A with wide-screen "
        "monitors for online classes or laptop-based study.",
        "https://drupal.uts.edu.au/sites/default/files/styles/wysiwyg_generic_large_x1/public/2022-02/online-learning-room.jpg?itok=y_VfUzj8",
    ),
   
    (
        "UTS Scholars Centre Meeting Room",
        "Building 2 - UTS Central",
        "10",
        "Scholars Centre Meeting Room",
        6,
        "Meeting Room",
        "Moderate",
        ["Wi-Fi", "Power Outlets", "AV Equipment"],
        "Wheelchair Accessible - HDR access only",
        "08:00",
        "22:00",
        "One of two bookable six-person meeting rooms in the UTS Scholars "
        "Centre. Restricted to authorised HDR students.",
        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSef2RK0vuzK5lkGJ8gjT4rg38Iowyo-uYWOY4u03qWZg&s=10",
    ),
    (
        "Alumni Green",
        "UTS City Campus",
        "Ground",
        "Alumni Green",
        30,
        "Outdoor Study",
        "Collaborative",
        ["Wi-Fi", "Under-Bench Power Outlets", "Tables", "Deckchairs"],
        "Step-Free Outdoor Access",
        "07:00",
        "22:00",
        "The central outdoor lawn and garden area at UTS, with seating, "
        "tables, deckchairs and under-bench power outlets.",
        "https://drupal.uts.edu.au/sites/default/files/styles/wysiwyg_large_x1/public/2020-03/03UTS-Alumni-Green_ASPECT_SIMON-WOOD-500x500.jpg?itok=UXaGgl9_",
    ),
]

FIELDS = [
    "space_name", "building", "building_level", "room_number", "max_capacity",
    "space_type", "noise_level", "facilities", "accessibility", "opening_time",
    "closing_time", "description", "image_url"
]


def connect():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row):
    data = dict(row)
    try:
        data["facilities"] = json.loads(data.get("facilities") or "[]")
    except json.JSONDecodeError:
        data["facilities"] = []
    return data


def normalise_payload(payload, partial=False):
    if not isinstance(payload, dict):
        raise ValueError("JSON object required")
    required = ["space_name", "building", "building_level", "room_number", "max_capacity", "space_type", "noise_level"]
    if not partial:
        missing = [k for k in required if payload.get(k) in (None, "")]
        if missing:
            raise ValueError("Missing required fields: " + ", ".join(missing))
    clean = {}
    for field in FIELDS:
        if field not in payload:
            continue
        value = payload[field]
        if field == "max_capacity":
            value = int(value)
            if value <= 0:
                raise ValueError("max_capacity must be greater than 0")
        elif field == "facilities":
            if isinstance(value, str):
                value = [x.strip() for x in value.split(",") if x.strip()]
            if not isinstance(value, list):
                raise ValueError("facilities must be an array")
            value = json.dumps(value)
        else:
            value = str(value).strip()
        clean[field] = value
    return clean


def init_db():
    conn = connect()
    conn.executescript(SCHEMA)
    count = conn.execute("SELECT COUNT(*) FROM campus_spaces").fetchone()[0]
    if count == 0:
        conn.executemany(
            """INSERT INTO campus_spaces
            (space_name, building, building_level, room_number, max_capacity, space_type,
             noise_level, facilities, accessibility, opening_time, closing_time, description, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [(a,b,c,d,e,f,g,json.dumps(h),i,j,k,l,m) for a,b,c,d,e,f,g,h,i,j,k,l,m in SEED]
        )
        conn.commit()
    conn.close()


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "student-5-database"})


@app.get("/spaces")
def get_spaces():
    conn = connect()
    rows = conn.execute("SELECT * FROM campus_spaces ORDER BY space_id").fetchall()
    conn.close()
    return jsonify([row_to_dict(r) for r in rows])


@app.get("/spaces/<int:space_id>")
def get_space(space_id):
    conn = connect()
    row = conn.execute("SELECT * FROM campus_spaces WHERE space_id = ?", (space_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Space not found"}), 404
    return jsonify(row_to_dict(row))


@app.post("/spaces")
def create_space():
    try:
        clean = normalise_payload(request.get_json(silent=True) or {})
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400
    columns = list(clean.keys())
    conn = connect()
    cur = conn.execute(
        f"INSERT INTO campus_spaces ({','.join(columns)}) VALUES ({','.join(['?'] * len(columns))})",  # noqa: S608 - columns restricted to FIELDS allowlist
        [clean[c] for c in columns],
    )
    conn.commit()
    new_id = cur.lastrowid
    row = conn.execute("SELECT * FROM campus_spaces WHERE space_id = ?", (new_id,)).fetchone()
    conn.close()
    return jsonify(row_to_dict(row)), 201


@app.put("/spaces/<int:space_id>")
def update_space(space_id):
    try:
        clean = normalise_payload(request.get_json(silent=True) or {}, partial=True)
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 400
    if not clean:
        return jsonify({"error": "No valid fields supplied"}), 400
    conn = connect()
    exists = conn.execute("SELECT 1 FROM campus_spaces WHERE space_id = ?", (space_id,)).fetchone()
    if not exists:
        conn.close()
        return jsonify({"error": "Space not found"}), 404
    assignments = ", ".join([f"{k} = ?" for k in clean])
    conn.execute(f"UPDATE campus_spaces SET {assignments} WHERE space_id = ?", [*clean.values(), space_id])  # noqa: S608 - columns restricted to FIELDS allowlist
    conn.commit()
    row = conn.execute("SELECT * FROM campus_spaces WHERE space_id = ?", (space_id,)).fetchone()
    conn.close()
    return jsonify(row_to_dict(row))


@app.delete("/spaces/<int:space_id>")
def delete_space(space_id):
    conn = connect()
    cur = conn.execute("DELETE FROM campus_spaces WHERE space_id = ?", (space_id,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        return jsonify({"error": "Space not found"}), 404
    return jsonify({"deleted": True, "space_id": space_id})


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)  # noqa: S104 - required for Docker networking
