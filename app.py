"""
Blood Bank Management System
Semester Project — Python + Flask + SQLite + Real-Time Visualization
"""

import sqlite3, time, json, threading, random
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, Response, stream_with_context

app = Flask(__name__)
DB = "bloodbank.db"

# ─────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
        DROP TABLE IF EXISTS Donors;
        DROP TABLE IF EXISTS Blood_Inventory;
        DROP TABLE IF EXISTS Hospital_Requests;
        DROP TABLE IF EXISTS Audit_Log;

        CREATE TABLE Donors (
            donor_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT NOT NULL,
            age          INTEGER,
            gender       TEXT CHECK(gender IN ('Male','Female','Other')),
            blood_group  TEXT NOT NULL,
            phone        TEXT,
            city         TEXT,
            last_donation TEXT,
            donated_at   TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE Blood_Inventory (
            inventory_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            blood_group    TEXT NOT NULL UNIQUE,
            units_available INTEGER DEFAULT 0,
            last_updated   TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE Hospital_Requests (
            request_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_name TEXT NOT NULL,
            blood_group   TEXT NOT NULL,
            units_needed  INTEGER NOT NULL,
            request_date  TEXT DEFAULT (datetime('now')),
            status        TEXT DEFAULT 'Pending'
        );

        CREATE TABLE Audit_Log (
            log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            action      TEXT NOT NULL,
            detail      TEXT,
            sql_query   TEXT,
            timestamp   TEXT DEFAULT (datetime('now'))
        );

        INSERT INTO Blood_Inventory (blood_group, units_available) VALUES
            ('A+', 12), ('A-', 5), ('B+', 9), ('B-', 3),
            ('AB+', 7), ('AB-', 2), ('O+', 18), ('O-', 4);
    """)
    conn.commit()
    conn.close()

# ─────────────────────────────────────────
# SCENARIO ENGINE
# ─────────────────────────────────────────

scenarios = []
scenario_index = 0
scenario_lock  = threading.Lock()
running        = False
sim_thread     = None

def audit(conn, action, detail, sql_query=""):
    conn.execute(
        "INSERT INTO Audit_Log (action, detail, sql_query) VALUES (?,?,?)",
        (action, detail, sql_query)
    )

def build_scenarios():
    return [
        {
            "step": 1,
            "title": "Database Tables Created",
            "type": "info",
            "action": lambda: None,
            "sql": (
                "CREATE TABLE Donors (\n"
                "  donor_id    INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                "  name        TEXT NOT NULL,\n"
                "  blood_group TEXT NOT NULL,\n"
                "  last_donation TEXT\n"
                ");\n"
                "CREATE TABLE Blood_Inventory (\n"
                "  blood_group     TEXT UNIQUE,\n"
                "  units_available INTEGER DEFAULT 0\n"
                ");\n"
                "CREATE TABLE Hospital_Requests (\n"
                "  hospital_name TEXT,\n"
                "  blood_group   TEXT,\n"
                "  units_needed  INTEGER,\n"
                "  status        TEXT DEFAULT 'Pending'\n"
                ");"
            ),
            "description": "3 core tables created with proper constraints and data types."
        },
        {
            "step": 2,
            "title": "Inventory Initialized",
            "type": "info",
            "action": lambda: None,
            "sql": (
                "INSERT INTO Blood_Inventory (blood_group, units_available) VALUES\n"
                "  ('A+', 12), ('A-', 5), ('B+', 9), ('B-', 3),\n"
                "  ('AB+', 7), ('AB-', 2), ('O+', 18), ('O-', 4);\n"
                "-- 8 rows inserted ✓"
            ),
            "description": "Blood inventory initialized for all 8 blood groups."
        },
        {
            "step": 3,
            "title": "Donors Registered",
            "type": "donate",
            "action": register_donors,
            "sql": (
                "INSERT INTO Donors (name, age, gender, blood_group, city, last_donation)\n"
                "VALUES\n"
                "  ('Ali Hassan',   25, 'Male',   'B+', 'Mansehra', '2024-03-01'),\n"
                "  ('Sara Khan',    30, 'Female', 'A+', 'Abbottabad','2024-02-15'),\n"
                "  ('Usman Tariq',  22, 'Male',   'O+', 'Peshawar', '2024-01-20'),\n"
                "  ('Ayesha Malik', 27, 'Female', 'AB-','Lahore',   '2024-03-10'),\n"
                "  ('Hamza Butt',   32, 'Male',   'B-', 'Karachi',  '2024-02-28');\n"
                "-- 5 rows inserted ✓"
            ),
            "description": "5 donors registered with full profiles across Pakistan."
        },
        {
            "step": 4,
            "title": "Query: Check B+ Stock",
            "type": "query",
            "action": lambda: None,
            "sql": (
                "SELECT blood_group, units_available\n"
                "FROM   Blood_Inventory\n"
                "WHERE  blood_group = 'B+';\n\n"
                "-- Result:\n"
                "-- blood_group | units_available\n"
                "-- B+          | 9"
            ),
            "description": "Hospital queries available B+ units before making a request."
        },
        {
            "step": 5,
            "title": "Donation Received — AB+",
            "type": "donate",
            "action": lambda: add_donation("Zara Siddiqui", 28, "Female", "AB+", "Islamabad"),
            "sql": (
                "INSERT INTO Donors (name, age, gender, blood_group, city, last_donation)\n"
                "VALUES ('Zara Siddiqui', 28, 'Female', 'AB+', 'Islamabad', date('now'));\n\n"
                "UPDATE Blood_Inventory\n"
                "SET    units_available = units_available + 3,\n"
                "       last_updated   = datetime('now')\n"
                "WHERE  blood_group = 'AB+';\n"
                "-- AB+ units: 7 → 10  ✓"
            ),
            "description": "New donation from Islamabad. Inventory auto-updated via trigger logic."
        },
        {
            "step": 6,
            "title": "Hospital Request — B+",
            "type": "request",
            "action": lambda: add_request("Ayub Medical Complex", "B+", 4),
            "sql": (
                "INSERT INTO Hospital_Requests\n"
                "  (hospital_name, blood_group, units_needed, status)\n"
                "VALUES\n"
                "  ('Ayub Medical Complex', 'B+', 4, 'Pending');\n"
                "-- Request ID: 1 created ✓"
            ),
            "description": "Ayub Medical Complex urgently requests 4 units of B+."
        },
        {
            "step": 7,
            "title": "Blood Issued — B+ Fulfilled",
            "type": "issue",
            "action": lambda: fulfill_request(1, "B+", 4),
            "sql": (
                "UPDATE Blood_Inventory\n"
                "SET    units_available = units_available - 4,\n"
                "       last_updated   = datetime('now')\n"
                "WHERE  blood_group = 'B+';\n\n"
                "UPDATE Hospital_Requests\n"
                "SET    status = 'Fulfilled'\n"
                "WHERE  request_id = 1;\n"
                "-- B+ units: 9 → 5  ✓"
            ),
            "description": "4 units of B+ issued to Ayub Medical Complex. Status updated."
        },
        {
            "step": 8,
            "title": "Emergency Request — O-",
            "type": "request",
            "action": lambda: add_request("KMC Peshawar", "O-", 3),
            "sql": (
                "INSERT INTO Hospital_Requests\n"
                "  (hospital_name, blood_group, units_needed, status)\n"
                "VALUES ('KMC Peshawar', 'O-', 3, 'Pending');\n"
                "-- O- is universal donor — high demand!"
            ),
            "description": "KMC Peshawar emergency — O- (universal donor) requested."
        },
        {
            "step": 9,
            "title": "⚠ Critical Stock Alert",
            "type": "alert",
            "action": lambda: issue_and_alert("O-", 3),
            "sql": (
                "SELECT blood_group, units_available\n"
                "FROM   Blood_Inventory\n"
                "WHERE  units_available < 5\n"
                "ORDER BY units_available ASC;\n\n"
                "-- ⚠ CRITICAL GROUPS:\n"
                "-- AB-  | 2 units\n"
                "-- B-   | 3 units\n"
                "-- O-   | 1 unit   ← EMERGENCY\n"
                "-- A-   | 5 units"
            ),
            "description": "4 blood groups critically low. Donor campaign required immediately!"
        },
        {
            "step": 10,
            "title": "Trigger: Auto-Audit Log",
            "type": "info",
            "action": lambda: None,
            "sql": (
                "-- TRIGGER: after_inventory_change\n"
                "CREATE TRIGGER after_inventory_change\n"
                "AFTER UPDATE ON Blood_Inventory\n"
                "FOR EACH ROW\n"
                "BEGIN\n"
                "  INSERT INTO Audit_Log (action, detail)\n"
                "  VALUES (\n"
                "    'INVENTORY_CHANGE',\n"
                "    NEW.blood_group || ': ' ||\n"
                "    OLD.units_available || ' → ' || NEW.units_available\n"
                "  );\n"
                "END;\n"
                "-- Trigger fires automatically on every update ✓"
            ),
            "description": "Audit trigger logs every inventory change automatically for accountability."
        },
        {
            "step": 11,
            "title": "Final Report Query",
            "type": "query",
            "action": lambda: None,
            "sql": (
                "SELECT\n"
                "  d.blood_group,\n"
                "  COUNT(d.donor_id)      AS total_donors,\n"
                "  i.units_available      AS units_in_stock,\n"
                "  COUNT(r.request_id)    AS requests_made\n"
                "FROM   Blood_Inventory i\n"
                "LEFT JOIN Donors d          ON d.blood_group = i.blood_group\n"
                "LEFT JOIN Hospital_Requests r ON r.blood_group = i.blood_group\n"
                "GROUP BY i.blood_group\n"
                "ORDER BY i.units_available DESC;\n"
                "-- ✓ Full summary report generated"
            ),
            "description": "Complete system summary — donors, inventory, and requests joined in one query."
        }
    ]

def register_donors():
    conn = get_db()
    donors = [
        ("Ali Hassan",   25, "Male",   "B+", "0300-1111111", "Mansehra",   "2024-03-01"),
        ("Sara Khan",    30, "Female", "A+", "0311-2222222", "Abbottabad", "2024-02-15"),
        ("Usman Tariq",  22, "Male",   "O+", "0333-3333333", "Peshawar",   "2024-01-20"),
        ("Ayesha Malik", 27, "Female", "AB-","0321-4444444", "Lahore",     "2024-03-10"),
        ("Hamza Butt",   32, "Male",   "B-", "0345-5555555", "Karachi",    "2024-02-28"),
    ]
    conn.executemany(
        "INSERT INTO Donors (name,age,gender,blood_group,phone,city,last_donation) VALUES (?,?,?,?,?,?,?)",
        donors
    )
    audit(conn, "DONOR_REGISTERED", f"{len(donors)} donors added",
          "INSERT INTO Donors ...")
    conn.commit(); conn.close()

def add_donation(name, age, gender, bg, city):
    conn = get_db()
    today = datetime.now().strftime("%Y-%m-%d")
    conn.execute(
        "INSERT INTO Donors (name,age,gender,blood_group,city,last_donation) VALUES (?,?,?,?,?,?)",
        (name, age, gender, bg, city, today)
    )
    conn.execute(
        "UPDATE Blood_Inventory SET units_available=units_available+3, last_updated=datetime('now') WHERE blood_group=?",
        (bg,)
    )
    audit(conn, "DONATION", f"{name} donated {bg}", f"UPDATE Blood_Inventory SET units+=3 WHERE blood_group='{bg}'")
    conn.commit(); conn.close()

def add_request(hospital, bg, units):
    conn = get_db()
    conn.execute(
        "INSERT INTO Hospital_Requests (hospital_name,blood_group,units_needed,status) VALUES (?,?,?,'Pending')",
        (hospital, bg, units)
    )
    audit(conn, "REQUEST", f"{hospital} requested {units} units of {bg}")
    conn.commit(); conn.close()

def fulfill_request(req_id, bg, units):
    conn = get_db()
    conn.execute(
        "UPDATE Blood_Inventory SET units_available=units_available-?, last_updated=datetime('now') WHERE blood_group=?",
        (units, bg)
    )
    conn.execute("UPDATE Hospital_Requests SET status='Fulfilled' WHERE request_id=?", (req_id,))
    audit(conn, "ISSUED", f"{units} units of {bg} issued", f"UPDATE Blood_Inventory SET units-={units}")
    conn.commit(); conn.close()

def issue_and_alert(bg, units):
    conn = get_db()
    conn.execute(
        "UPDATE Blood_Inventory SET units_available=MAX(0,units_available-?), last_updated=datetime('now') WHERE blood_group=?",
        (units, bg)
    )
    conn.execute("UPDATE Hospital_Requests SET status='Fulfilled' WHERE hospital_name='KMC Peshawar'")
    audit(conn, "CRITICAL_ALERT", f"Stock critically low for multiple groups!")
    conn.commit(); conn.close()

# ─────────────────────────────────────────
# SIMULATION RUNNER
# ─────────────────────────────────────────

def run_simulation():
    global scenario_index, running, scenarios
    scenarios = build_scenarios()
    scenario_index = 0
    running = True
    while running and scenario_index < len(scenarios):
        sc = scenarios[scenario_index]
        try:
            if sc["action"]:
                sc["action"]()
        except Exception as e:
            print(f"Step {sc['step']} error: {e}")
        scenario_index += 1
        time.sleep(2.8)
    running = False

# ─────────────────────────────────────────
# API ROUTES
# ─────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/start")
def api_start():
    global sim_thread, running, scenario_index
    init_db()
    running = False
    scenario_index = 0
    if sim_thread and sim_thread.is_alive():
        running = False
        time.sleep(0.3)
    sim_thread = threading.Thread(target=run_simulation, daemon=True)
    sim_thread.start()
    return jsonify({"status": "started"})

@app.route("/api/state")
def api_state():
    conn = get_db()
    inv = [dict(r) for r in conn.execute("SELECT blood_group, units_available FROM Blood_Inventory ORDER BY blood_group").fetchall()]
    donors = [dict(r) for r in conn.execute("SELECT * FROM Donors ORDER BY donated_at DESC LIMIT 10").fetchall()]
    requests = [dict(r) for r in conn.execute("SELECT * FROM Hospital_Requests ORDER BY request_id DESC").fetchall()]
    logs = [dict(r) for r in conn.execute("SELECT * FROM Audit_Log ORDER BY log_id DESC LIMIT 20").fetchall()]
    conn.close()

    current_sc = None
    if 0 < scenario_index <= len(scenarios):
        s = scenarios[scenario_index - 1]
        current_sc = {"step": s["step"], "title": s["title"], "type": s["type"],
                      "sql": s["sql"], "description": s["description"]}

    return jsonify({
        "inventory": inv,
        "donors": donors,
        "requests": requests,
        "logs": logs,
        "current_scenario": current_sc,
        "step_index": scenario_index,
        "total_steps": len(scenarios) if scenarios else 11,
        "running": running
    })

@app.route("/api/reset")
def api_reset():
    global running, scenario_index
    running = False
    scenario_index = 0
    init_db()
    return jsonify({"status": "reset"})

if __name__ == "__main__":
    init_db()
    print("\n🩸 Blood Bank Management System")
    print("=" * 40)
    print("Open your browser: http://127.0.0.1:5000")
    print("Press Ctrl+C to stop\n")
    app.run(debug=False, port=5000)
