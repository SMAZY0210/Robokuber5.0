#!/usr/bin/env python3
"""
Robokubers 5.0 — Viva Management System
BUP Robotics Club
Run: python3 server.py
"""
from flask import Flask, request, jsonify, send_from_directory, Response
import sqlite3, os, io, csv, socket, logging, json
from datetime import datetime
from logging.handlers import RotatingFileHandler

# ── PATHS ─────────────────────────────────────────────────────────────────────
BASE     = os.path.dirname(__file__)
DB_PATH  = os.path.join(BASE, 'backend', 'robokubers.db')
LOG_PATH = os.path.join(BASE, 'backend', 'activity.log')

os.makedirs(os.path.join(BASE, 'backend'), exist_ok=True)

# ── LOGGING SETUP ─────────────────────────────────────────────────────────────
logger = logging.getLogger('robokubers')
logger.setLevel(logging.INFO)

# Rotating file: max 5 MB, keep 3 backups
fh = RotatingFileHandler(LOG_PATH, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
fh.setLevel(logging.INFO)
fh.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(fh)

# Also print to console
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S'))
logger.addHandler(ch)

def log(event, detail='', panelist='—', extra=None):
    """Write a structured log entry."""
    entry = {
        'ts':       datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'event':    event,
        'panelist': panelist,
        'detail':   detail,
        'ip':       request.remote_addr if request else '—',
    }
    if extra:
        entry.update(extra)
    logger.info(json.dumps(entry, ensure_ascii=False))

def read_logs(limit=500):
    """Read last `limit` log lines from file."""
    entries = []
    try:
        with open(LOG_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in reversed(lines[-limit:]):
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except Exception:
                    entries.append({'ts':'?','event':'raw','detail':line,'panelist':'—','ip':'—'})
    except FileNotFoundError:
        pass
    return list(reversed(entries))  # newest first

# ── FLASK APP ─────────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder='frontend/public')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ── STATIC ────────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ua = request.headers.get('User-Agent', '—')[:80]
    log('PAGE_VISIT', f'ua: {ua}', panelist='—', extra={'ip_addr': ip})
    return send_from_directory('frontend/public', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    if filename == 'log':
        return serve_log_page()
    return send_from_directory('frontend/public', filename)

# ── LOG VIEWER ────────────────────────────────────────────────────────────────
@app.route('/log')
def serve_log_page():
    entries = read_logs(1000)

    EVENT_STYLE = {
        'PAGE_VISIT':      ('🌐', '#58a6ff', 'Page Visit'),
        'LOGIN_OK':        ('🟢', '#3fb950', 'Login'),
        'LOGIN_FAIL':      ('🔴', '#f85149', 'Login Failed'),
        'LOGOUT':          ('⚪', '#8b949e', 'Logout'),
        'VIEW_CANDIDATE':  ('👁',  '#58a6ff', 'Viewed'),
        'SCORE_SAVED':     ('💾', '#58a6ff', 'Score Saved'),
        'STATUS_OVERRIDE': ('⚡', '#f0883e', 'Status Override'),
        'ADD_PARTICIPANT': ('➕', '#3fb950', 'Added Participant'),
        'ADD_PANELIST':    ('👤', '#bc8cff', 'Added Panelist'),
        'DEL_PANELIST':    ('🗑',  '#f85149', 'Removed Panelist'),
        'EXPORT_CSV':      ('📥', '#d29922', 'CSV Export'),
        'SECTOR_UPDATE':   ('🎯', '#bc8cff', 'Sectors Updated'),
        'SERVER_START':    ('🚀', '#3fb950', 'Server Started'),
    }

    rows_html = ''
    for e in entries:
        ev    = e.get('event','—')
        icon, color, label = EVENT_STYLE.get(ev, ('📋', '#8b949e', ev))
        ts    = e.get('ts','—')
        pan   = e.get('panelist','—')
        detail= e.get('detail','')
        ip    = e.get('ip','—')
        rows_html += f'''<tr>
            <td class="ts">{ts}</td>
            <td><span class="badge" style="color:{color};border-color:{color}">{icon} {label}</span></td>
            <td class="pan">{pan}</td>
            <td class="detail">{detail}</td>
            <td class="ip">{ip}</td>
        </tr>\n'''

    if not rows_html:
        rows_html = '<tr><td colspan="5" class="empty">No activity logged yet.</td></tr>'

    total = len(entries)
    logins = sum(1 for e in entries if e.get('event')=='LOGIN_OK')
    scores = sum(1 for e in entries if e.get('event')=='SCORE_SAVED')
    views  = sum(1 for e in entries if e.get('event')=='VIEW_CANDIDATE')

    page = f'''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Activity Log — Robokubers 5.0</title>
<style>
  :root {{
    --bg:#0d1117;--bg2:#161b26;--card:#1c2333;--card2:#222d42;
    --border:#2a3650;--text:#e6edf3;--text2:#8b949e;--text3:#58687e;
    --accent:#58a6ff;--green:#3fb950;--red:#f85149;--orange:#f0883e;
    --font:'DM Sans',system-ui,sans-serif;--mono:'DM Mono',monospace;
  }}
  [data-theme="light"] {{
    --bg:#f0f4f8;--bg2:#fff;--card:#fff;--card2:#f0f4f8;
    --border:#d0d7de;--text:#1c2433;--text2:#57606a;--text3:#8c959f;
    --accent:#0969da;--green:#1a7f37;--red:#cf222e;--orange:#bc4c00;
  }}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:var(--font);background:var(--bg);color:var(--text);font-size:13px}}
  header{{background:var(--card);border-bottom:1px solid var(--border);padding:14px 24px;
    display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap}}
  .logo{{font-size:18px;font-weight:700;color:var(--accent)}}
  .logo span{{color:var(--text2);font-size:13px;font-weight:400;margin-left:8px}}
  .hdr-right{{display:flex;align-items:center;gap:10px}}
  .theme-btn{{padding:6px 12px;border-radius:6px;background:var(--card2);border:1px solid var(--border);
    color:var(--text2);cursor:pointer;font-size:13px}}
  .back-btn{{padding:6px 14px;border-radius:6px;background:var(--accent);color:#fff;
    text-decoration:none;font-size:13px;font-weight:600}}
  .refresh-btn{{padding:6px 14px;border-radius:6px;background:var(--card2);
    border:1px solid var(--border);color:var(--text2);cursor:pointer;font-size:13px}}
  .inner{{padding:20px 24px;max-width:1400px}}
  .stats{{display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap}}
  .stat{{background:var(--card);border:1px solid var(--border);border-radius:10px;
    padding:14px 20px;text-align:center;min-width:100px}}
  .stat-num{{font-size:26px;font-weight:700;line-height:1}}
  .stat-label{{font-size:10px;text-transform:uppercase;letter-spacing:.6px;color:var(--text3);margin-top:3px}}
  .filter-bar{{display:flex;gap:8px;margin-bottom:14px;flex-wrap:wrap;align-items:center}}
  .filter-bar input,.filter-bar select{{
    background:var(--bg2);border:1px solid var(--border);color:var(--text);
    border-radius:6px;padding:7px 11px;font-size:13px;outline:none;font-family:var(--font)}}
  .filter-bar input:focus,.filter-bar select:focus{{border-color:var(--accent)}}
  .filter-bar input{{flex:1;min-width:200px}}
  .table-wrap{{background:var(--card);border:1px solid var(--border);border-radius:10px;overflow:hidden;overflow-x:auto}}
  table{{width:100%;border-collapse:collapse}}
  th{{text-align:left;padding:10px 14px;background:var(--card2);border-bottom:1px solid var(--border);
    font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:var(--text3);white-space:nowrap}}
  td{{padding:9px 14px;border-bottom:1px solid var(--border);vertical-align:middle}}
  tr:last-child td{{border-bottom:none}}
  tr:hover td{{background:var(--card2)}}
  .ts{{font-family:var(--mono);font-size:11px;color:var(--text3);white-space:nowrap}}
  .pan{{font-weight:600;white-space:nowrap}}
  .detail{{color:var(--text2);max-width:400px}}
  .ip{{font-family:var(--mono);font-size:11px;color:var(--text3);white-space:nowrap}}
  .badge{{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;border-radius:20px;
    font-size:11px;font-weight:700;border:1px solid;background:transparent;white-space:nowrap}}
  .empty{{text-align:center;padding:40px;color:var(--text3)}}
  ::-webkit-scrollbar{{width:5px;height:5px}}
  ::-webkit-scrollbar-thumb{{background:var(--border);border-radius:3px}}
</style>
</head>
<body>
<header>
  <div class="logo">🤖 Robokubers 5.0 <span>Activity Log</span></div>
  <div class="hdr-right">
    <span style="font-size:12px;color:var(--text3)">{total} events</span>
    <button class="refresh-btn" onclick="location.reload()">↺ Refresh</button>
    <button class="theme-btn" onclick="toggleTheme()" id="tbtn">☀️</button>
    <a class="back-btn" href="/">← Dashboard</a>
  </div>
</header>
<div class="inner">
  <div class="stats">
    <div class="stat"><div class="stat-num" style="color:var(--accent)">{total}</div><div class="stat-label">Total Events</div></div>
    <div class="stat"><div class="stat-num" style="color:var(--green)">{logins}</div><div class="stat-label">Logins</div></div>
    <div class="stat"><div class="stat-num" style="color:var(--accent)">{scores}</div><div class="stat-label">Scores Saved</div></div>
    <div class="stat"><div class="stat-num" style="color:var(--text2)">{views}</div><div class="stat-label">Profiles Viewed</div></div>
  </div>
  <div class="filter-bar">
    <input type="text" id="search" placeholder="🔍 Search panelist, detail, IP…" oninput="filterRows()">
    <select id="ev-filter" onchange="filterRows()">
      <option value="">All Events</option>
      <option value="LOGIN_OK">Login</option>
      <option value="LOGIN_FAIL">Login Failed</option>
      <option value="VIEW_CANDIDATE">Viewed Candidate</option>
      <option value="SCORE_SAVED">Score Saved</option>
      <option value="STATUS_OVERRIDE">Status Override</option>
      <option value="ADD_PARTICIPANT">Added Participant</option>
      <option value="EXPORT_CSV">CSV Export</option>
    </select>
  </div>
  <div class="table-wrap">
    <table id="log-table">
      <thead><tr>
        <th>Timestamp</th><th>Event</th><th>Panelist</th><th>Detail</th><th>IP Address</th>
      </tr></thead>
      <tbody id="log-body">{rows_html}</tbody>
    </table>
  </div>
</div>
<script>
// Store all rows for client-side filtering
const allRows = Array.from(document.querySelectorAll('#log-body tr'));

function filterRows() {{
  const q    = document.getElementById('search').value.toLowerCase();
  const evf  = document.getElementById('ev-filter').value.toLowerCase();
  allRows.forEach(row => {{
    const text = row.textContent.toLowerCase();
    const badge = row.querySelector('.badge');
    const evText = badge ? badge.textContent.toLowerCase() : '';
    const matchQ  = !q   || text.includes(q);
    const matchEv = !evf || evText.includes(evf.replace('_',' ').toLowerCase()) || text.includes(evf.replace('_',' '));
    row.style.display = (matchQ && matchEv) ? '' : 'none';
  }});
}}

function toggleTheme() {{
  const html = document.documentElement;
  html.dataset.theme = html.dataset.theme === 'dark' ? 'light' : 'dark';
  document.getElementById('tbtn').textContent = html.dataset.theme === 'dark' ? '☀️' : '🌙';
}}
// Sync with main app theme
const saved = localStorage.getItem('theme');
if (saved === 'light') {{
  document.documentElement.dataset.theme = 'light';
  document.getElementById('tbtn').textContent = '🌙';
}}
// Auto-refresh every 30s
setTimeout(() => location.reload(), 30000);
</script>
</body>
</html>'''
    return Response(page, mimetype='text/html')

@app.route('/api/logs')
def get_logs_json():
    return jsonify(read_logs(500))

# ── AUTH ──────────────────────────────────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    db = get_db()
    row = db.execute('SELECT * FROM panelists WHERE uid=? AND password=?',
                     (data.get('uid','').strip(), data.get('password','').strip())).fetchone()
    db.close()
    if row:
        log('LOGIN_OK', f"UID: {data.get('uid','')}", panelist=row['name'])
        return jsonify({'success': True, 'panelist': dict(row)})
    log('LOGIN_FAIL', f"UID attempted: {data.get('uid','')}")
    return jsonify({'success': False, 'error': 'Invalid UID or password'}), 401

# ── PANELISTS ─────────────────────────────────────────────────────────────────
@app.route('/api/panelists', methods=['GET'])
def get_panelists():
    db = get_db()
    rows = db.execute('SELECT id, name, uid, is_admin FROM panelists ORDER BY is_admin DESC, name').fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/panelists', methods=['POST'])
def add_panelist():
    data = request.json
    actor = request.headers.get('X-Panelist-Name', '—')
    db = get_db()
    try:
        db.execute('INSERT INTO panelists (name, uid, password, is_admin) VALUES (?,?,?,?)',
                   (data['name'], data['uid'], data['password'], data.get('is_admin', 0)))
        db.commit()
        log('ADD_PANELIST', f"Added: {data['name']} (uid: {data['uid']})", panelist=actor)
    except sqlite3.IntegrityError:
        db.close()
        return jsonify({'success': False, 'error': 'UID already exists'}), 400
    db.close()
    return jsonify({'success': True})

@app.route('/api/panelists/<int:pid>', methods=['DELETE'])
def delete_panelist(pid):
    actor = request.headers.get('X-Panelist-Name', '—')
    db = get_db()
    row = db.execute('SELECT name FROM panelists WHERE id=?', (pid,)).fetchone()
    name = row['name'] if row else f'id:{pid}'
    db.execute('DELETE FROM panelists WHERE id=? AND is_admin=0', (pid,))
    db.commit()
    db.close()
    log('DEL_PANELIST', f"Removed: {name}", panelist=actor)
    return jsonify({'success': True})

# ── PARTICIPANTS ──────────────────────────────────────────────────────────────
@app.route('/api/participants', methods=['GET'])
def get_participants():
    search = request.args.get('search', '')
    dept   = request.args.get('department', '')
    batch  = request.args.get('batch', '')
    status = request.args.get('status', '')
    db = get_db()
    q = 'SELECT id, student_id, name, department, batch, sectors, viva_status, form_photo FROM participants WHERE 1=1'
    params = []
    if search:
        q += ' AND (name LIKE ? OR student_id LIKE ?)'; params += [f'%{search}%', f'%{search}%']
    if dept:
        q += ' AND department=?'; params.append(dept)
    if batch:
        q += ' AND batch=?'; params.append(batch)
    if status:
        q += ' AND viva_status=?'; params.append(status)
    q += ' ORDER BY name'
    rows = db.execute(q, params).fetchall()
    result = []
    for r in rows:
        s = db.execute('SELECT COUNT(DISTINCT panelist_id) as p, AVG(score) as avg FROM viva_scores WHERE participant_id=?', (r['id'],)).fetchone()
        d = dict(r); d['panelist_count'] = s['p']; d['avg_score'] = round(s['avg'],1) if s['avg'] else None
        result.append(d)
    db.close()
    return jsonify(result)

@app.route('/api/participants', methods=['POST'])
def add_participant():
    data = request.json
    actor = request.headers.get('X-Panelist-Name', '—')
    db = get_db()
    try:
        db.execute('INSERT INTO participants (student_id,name,department,batch,email,phone,facebook,why_join,about_self,sectors) VALUES (?,?,?,?,?,?,?,?,?,?)',
                   (data.get('student_id',''),data.get('name',''),data.get('department',''),data.get('batch',''),
                    data.get('email',''),data.get('phone',''),data.get('facebook',''),
                    data.get('why_join',''),data.get('about_self',''),data.get('sectors','')))
        db.commit()
        log('ADD_PARTICIPANT', f"{data.get('name','')} — {data.get('student_id','')}", panelist=actor)
    except sqlite3.IntegrityError:
        db.close()
        return jsonify({'success': False, 'error': 'Student ID already exists'}), 400
    db.close()
    return jsonify({'success': True})

@app.route('/api/participants/<int:pid>', methods=['GET'])
def get_participant(pid):
    actor = request.headers.get('X-Panelist-Name', '—')
    db = get_db()
    p = db.execute('SELECT * FROM participants WHERE id=?', (pid,)).fetchone()
    if not p: db.close(); return jsonify({'error': 'Not found'}), 404
    scores = db.execute('''SELECT vs.*, pan.name as panelist_name FROM viva_scores vs
        JOIN panelists pan ON pan.id=vs.panelist_id
        WHERE vs.participant_id=? ORDER BY pan.name, vs.segment''', (pid,)).fetchall()
    result = dict(p); result['scores'] = [dict(s) for s in scores]
    db.close()
    log('VIEW_CANDIDATE', f"{p['name']} ({p['student_id']})", panelist=actor)
    return jsonify(result)

@app.route('/api/participants/<int:pid>', methods=['PUT'])
def update_participant(pid):
    data = request.json
    actor = request.headers.get('X-Panelist-Name', '—')
    db = get_db()
    fields = ['name','department','batch','email','phone','facebook','why_join','about_self','sectors','viva_status']
    sets = ', '.join(f'{f}=?' for f in fields if f in data)
    vals = [data[f] for f in fields if f in data]
    if sets:
        db.execute(f'UPDATE participants SET {sets} WHERE id=?', vals + [pid])
        db.commit()
        if 'sectors' in data:
            p = get_db().execute('SELECT name FROM participants WHERE id=?',(pid,)).fetchone()
            log('SECTOR_UPDATE', f"Sectors updated for id:{pid}", panelist=actor)
    db.close()
    return jsonify({'success': True})

@app.route('/api/participants/<int:pid>/status', methods=['PUT'])
def update_status(pid):
    data = request.json
    actor = request.headers.get('X-Panelist-Name', '—')
    db = get_db()
    p = db.execute('SELECT name FROM participants WHERE id=?', (pid,)).fetchone()
    name = p['name'] if p else f'id:{pid}'
    db.execute('UPDATE participants SET viva_status=? WHERE id=?', (data['status'], pid))
    db.commit()
    db.close()
    log('STATUS_OVERRIDE', f"{name} → {data['status']}", panelist=actor)
    return jsonify({'success': True})

# ── SCORES ────────────────────────────────────────────────────────────────────
@app.route('/api/scores', methods=['POST'])
def save_scores():
    data = request.json
    actor = request.headers.get('X-Panelist-Name', '—')
    db = get_db()
    db.execute('DELETE FROM viva_scores WHERE participant_id=? AND panelist_id=?',
               (data['participant_id'], data['panelist_id']))
    for seg in data['segments']:
        db.execute('INSERT INTO viva_scores (participant_id,panelist_id,segment,score,notes,decision) VALUES (?,?,?,?,?,?)',
                   (data['participant_id'],data['panelist_id'],seg['segment'],seg['score'],seg['notes'],seg['decision']))

    all_decisions = [d['decision'] for d in db.execute(
        'SELECT decision FROM viva_scores WHERE participant_id=?', (data['participant_id'],)).fetchall()]
    panelist_count = db.execute(
        'SELECT COUNT(DISTINCT panelist_id) FROM viva_scores WHERE participant_id=?', (data['participant_id'],)).fetchone()[0]

    if panelist_count >= 2:
        if all(d=='Selected' for d in all_decisions): status='selected'
        elif all(d=='Rejected' for d in all_decisions): status='rejected'
        elif all(d=='Hold' for d in all_decisions): status='hold'
        else: status='disputed'
    else:
        if all(d=='Selected' for d in all_decisions): status='selected'
        elif any(d=='Rejected' for d in all_decisions): status='rejected'
        elif any(d=='Hold' for d in all_decisions): status='hold'
        else: status='pending'

    db.execute('UPDATE participants SET viva_status=? WHERE id=?', (status, data['participant_id']))
    db.commit()

    p = db.execute('SELECT name FROM participants WHERE id=?', (data['participant_id'],)).fetchone()
    p_name = p['name'] if p else f"id:{data['participant_id']}"
    segs_summary = ', '.join(f"{s['segment']}:{s['score']}/{s['decision']}" for s in data['segments'])
    log('SCORE_SAVED', f"{p_name} — {segs_summary} → {status}", panelist=actor)

    db.close()
    return jsonify({'success': True, 'viva_status': status})

# ── STATS ─────────────────────────────────────────────────────────────────────
@app.route('/api/stats')
def get_stats():
    db = get_db()
    def cnt(q): return db.execute(q).fetchone()[0]
    total    = cnt('SELECT COUNT(*) FROM participants')
    pending  = cnt("SELECT COUNT(*) FROM participants WHERE viva_status='pending'")
    selected = cnt("SELECT COUNT(*) FROM participants WHERE viva_status='selected'")
    hold     = cnt("SELECT COUNT(*) FROM participants WHERE viva_status='hold'")
    rejected = cnt("SELECT COUNT(*) FROM participants WHERE viva_status='rejected'")
    disputed = cnt("SELECT COUNT(*) FROM participants WHERE viva_status='disputed'")
    by_dept  = db.execute("SELECT department, COUNT(*) as cnt FROM participants GROUP BY department ORDER BY cnt DESC").fetchall()
    sector_rows = db.execute("SELECT sectors FROM participants WHERE sectors!=''").fetchall()
    db.close()
    from collections import Counter
    sc = Counter()
    for r in sector_rows:
        for s in r['sectors'].split(','):
            s=s.strip()
            if s: sc[s]+=1
    return jsonify({'total':total,'pending':pending,'done':total-pending,
                    'selected':selected,'hold':hold,'rejected':rejected,'disputed':disputed,
                    'by_department':[dict(r) for r in by_dept],'by_sector':dict(sc)})

# ── EXPORT ────────────────────────────────────────────────────────────────────
@app.route('/api/export/csv')
def export_csv():
    actor = request.headers.get('X-Panelist-Name', '—')
    log('EXPORT_CSV', 'Results exported to CSV', panelist=actor)
    db = get_db()
    rows = db.execute('''SELECT p.student_id,p.name,p.department,p.batch,p.email,p.phone,
        p.sectors,p.viva_status,
        GROUP_CONCAT(DISTINCT pan.name||': '||vs.segment||' ('||vs.score||'/10, '||vs.decision||')') as all_scores,
        AVG(vs.score) as avg_score
        FROM participants p LEFT JOIN viva_scores vs ON vs.participant_id=p.id
        LEFT JOIN panelists pan ON pan.id=vs.panelist_id
        GROUP BY p.id ORDER BY p.viva_status,p.name''').fetchall()
    db.close()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(['Student ID','Name','Department','Batch','Email','Phone','Sectors','Status','All Scores','Avg Score'])
    for r in rows:
        w.writerow([r['student_id'],r['name'],r['department'],r['batch'],r['email'],r['phone'],
                    r['sectors'],r['viva_status'],r['all_scores'] or '',
                    round(r['avg_score'],1) if r['avg_score'] else ''])
    return Response(out.getvalue(), mimetype='text/csv',
                    headers={'Content-Disposition':'attachment; filename=robokubers5_results.csv'})

# ── PHOTO PROXY ───────────────────────────────────────────────────────────────
# Proxies Google Drive photos through the server, bypassing browser CORS/auth blocks
@app.route('/api/photo-proxy')
def photo_proxy():
    """Fetch a Google Drive photo server-side and stream to browser."""
    url = request.args.get('url', '')
    if not url or 'drive.google.com' not in url:
        return Response('Invalid URL', status=400)
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            content_type = resp.headers.get('Content-Type', 'image/jpeg')
            data = resp.read()
        return Response(data, mimetype=content_type,
                        headers={'Cache-Control': 'public, max-age=3600'})
    except Exception as e:
        # Return empty 1px transparent GIF on failure so <img> onerror fires
        import base64
        gif = base64.b64decode('R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7')
        return Response(gif, mimetype='image/gif', status=200)


# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    hostname = socket.gethostname()
    try: lan_ip = socket.gethostbyname(hostname)
    except: lan_ip = '0.0.0.0'

    log('SERVER_START', f'Listening on 0.0.0.0:5000 | LAN: {lan_ip}')

    print(f"""
╔══════════════════════════════════════════════════════╗
║        ROBOKUBERS 5.0 — Viva Management System       ║
║                 BUP Robotics Club                    ║
╠══════════════════════════════════════════════════════╣
║  Local:   http://localhost:5000                      ║
║  Network: http://{lan_ip}:5000{' '*(22-len(lan_ip))}║
║  Log:     http://{lan_ip}:5000/log{' '*(18-len(lan_ip))}║
╚══════════════════════════════════════════════════════╝
""")
    app.run(host='0.0.0.0', port=5000, debug=False)
