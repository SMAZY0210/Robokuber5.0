# Robokubers 5.0 — Viva Management System
### BUP Robotics Club

---

## 📋 Requirements
- Python 3.8 or later (already installed on most systems)
- Flask: `pip install flask` (or `pip3 install flask`)

---

## 🚀 How to Run

### Windows
1. Double-click `START_SERVER.bat`
2. Open your browser → `http://localhost:5000`

### Linux / Mac
```bash
chmod +x start_server.sh
./start_server.sh
```
Or directly:
```bash
python3 server.py
```

---

## 🌐 LAN Hosting
The server automatically runs on `0.0.0.0:5000`, so anyone on your local network can access it.

**To find your LAN IP:**
- Windows: Run `ipconfig` → look for IPv4 Address (e.g. `192.168.1.105`)
- Linux/Mac: Run `ifconfig` or `ip addr`

Share the URL `http://192.168.x.x:5000` with panelists connected to the same WiFi/network.

---

## 🔐 Default Login Credentials

| Name    | PIN  |
|---------|------|
| Panel 1 | 1234 |
| Panel 2 | 2345 |
| Admin   | 0000 |

You can add more panelists from the **Manage** tab after logging in.

---

## 📁 File Structure
```
robokubers/
├── server.py               ← Main server (run this)
├── START_SERVER.bat        ← Windows launcher
├── start_server.sh         ← Linux/Mac launcher
├── README.md
├── backend/
│   └── robokubers.db       ← SQLite database (all participant data)
└── frontend/
    └── public/
        └── index.html      ← Complete frontend
```

---

## 🎯 Features
- **Dashboard** — Browse all 121 participants with photo, filters, search
- **Viva View** — Full candidate profile with photo, motivation, about, sector pills
- **Sector-wise Questions** — Curated questions for all 10 sectors
- **Scoring** — Score (1-10) + Notes + Decision (Selected/Hold/Rejected) per segment
- **Multi-panelist** — Each panelist scores independently; others' scores shown for reference
- **Results** — Overview table with filters and CSV export
- **Manage** — Add/view panelists, department breakdown

---

## 📤 Exporting Results
Go to the **Results** tab and click **⬇ Export CSV** to download a full results spreadsheet.

---

## 🔧 Customising Panelist PINs
After running the server, go to **Manage → Add Panelist** to create new logins.
To reset the database, delete `backend/robokubers.db` and re-run the setup:
```bash
python3 setup_db.py
```
