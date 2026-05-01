#!/usr/bin/env python3
"""Run this to re-create the database from scratch."""
import pandas as pd, sqlite3, os

EXCEL_PATH = os.path.join(os.path.dirname(__file__), 'Robokubers-5_0-Responses.xlsx')
DB_PATH    = os.path.join(os.path.dirname(__file__), 'backend', 'robokubers.db')

if not os.path.exists(EXCEL_PATH):
    print(f"ERROR: Put your Excel file here → {EXCEL_PATH}")
    exit(1)

df = pd.read_excel(EXCEL_PATH, sheet_name='Form Responses 1')
df = df.drop(columns=['Timestamp','Picture(Formal / Semi Formal)','CV (If possible or Bring it during viva)'], errors='ignore')
df.columns = ['email_address','name','department','batch','student_id','email','phone','facebook','why_join','about_self','sectors']
df['student_id'] = df['student_id'].astype(str).str.strip()
df['name']  = df['name'].str.strip()
df['batch'] = df['batch'].astype(str)
df['phone'] = df['phone'].astype(str)
df = df.fillna('')

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute('DROP TABLE IF EXISTS participants')
c.execute('DROP TABLE IF EXISTS panelists')
c.execute('DROP TABLE IF EXISTS viva_scores')
c.execute('''CREATE TABLE participants (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id TEXT UNIQUE, name TEXT, department TEXT, batch TEXT,
  email TEXT, phone TEXT, facebook TEXT, why_join TEXT, about_self TEXT,
  sectors TEXT, viva_status TEXT DEFAULT "pending"
)''')
c.execute('CREATE TABLE panelists (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, pin TEXT)')
c.execute('''CREATE TABLE viva_scores (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  participant_id INTEGER, panelist_id INTEGER,
  segment TEXT, score INTEGER, notes TEXT, decision TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
)''')
c.execute("INSERT INTO panelists (name, pin) VALUES ('Panel 1', '1234')")
c.execute("INSERT INTO panelists (name, pin) VALUES ('Panel 2', '2345')")
c.execute("INSERT INTO panelists (name, pin) VALUES ('Admin', '0000')")
for _, row in df.iterrows():
    c.execute('''INSERT OR IGNORE INTO participants 
        (student_id,name,department,batch,email,phone,facebook,why_join,about_self,sectors)
        VALUES (?,?,?,?,?,?,?,?,?,?)''',
        tuple(row[['student_id','name','department','batch','email','phone','facebook','why_join','about_self','sectors']]))
conn.commit()
print(f"✓ Database ready. {c.execute('SELECT COUNT(*) FROM participants').fetchone()[0]} participants loaded.")
conn.close()
