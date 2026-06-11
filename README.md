# 🩸 Blood Bank Management System
### DBMS Semester Project — Python + Flask + SQLite + Real-Time Visualization

---

## 📁 Project Structure

```
bloodbank/
├── app.py              ← Main Python backend (Flask + SQLite)
├── templates/
│   └── index.html      ← Real-time dashboard (HTML + Chart.js)
├── bloodbank.db        ← SQLite database (auto-created on run)
└── README.md
```

---

## ⚙️ Setup & Run

### Step 1 — Install Python dependencies
```bash
pip install flask
```

### Step 2 — Run the server
```bash
python app.py
```

### Step 3 — Open in browser
```
http://127.0.0.1:5000
```

### Step 4 — Click START
The simulation runs automatically, step by step!

---

## 🗂️ Database Tables

| Table | Description |
|-------|-------------|
| `Donors` | Stores donor profiles with blood group, city, contact |
| `Blood_Inventory` | Tracks available units per blood group |
| `Hospital_Requests` | Hospital blood requests with status |
| `Audit_Log` | Auto-logs every DB operation |

---

## 🔍 Key SQL Queries Demonstrated

1. **CREATE TABLE** — All 3 tables with constraints
2. **INSERT** — Donors and inventory initialization
3. **SELECT WHERE** — Check specific blood group stock
4. **UPDATE** — Inventory after donation/issue
5. **JOIN** — Final summary report
6. **TRIGGER** — Auto audit log on inventory change

---

## 🚀 Features

- ✅ Real-time inventory bars with color coding
- ✅ Live SQL query display with syntax highlighting
- ✅ Step-by-step simulation (11 scenarios)
- ✅ Hospital request tracking
- ✅ Donor registry with avatars
- ✅ Critical stock alerts (< 5 units)
- ✅ Chart.js inventory overview
- ✅ Audit log for all operations
- ✅ SQLite database (no external DB needed)

---

## 📊 Presentation Tips

1. Run `python app.py` before class
2. Open `http://127.0.0.1:5000` on projector
3. Click **START** — pauses naturally between steps
4. Explain each SQL query as it appears
5. Click **Reset** to demo again

---

*Developed for DBMS Semester Project*
