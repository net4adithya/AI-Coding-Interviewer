"""
debug_intern_assignment2.py - ASCII-safe version
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import psycopg2
import requests
import json
from urllib.parse import urlparse, unquote

DB_URL = "postgresql://postgres.rfqmnstrnvipxknvrouy:Ryanronalds%40103992@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require"
SUPABASE_URL = "https://rfqmnstrnvipxknvrouy.supabase.co"
ANON_KEY     = "sb_publishable_f6Kciw9KKmJdJwC-lbpeGQ_gNqyVtcs"
INTERN_EMAIL = "intern@test.com"
INTERN_PASS  = "intern123"
AUTHORITY_EMAIL = "admin@test.com"
AUTHORITY_PASS  = "admin123"
API_BASE     = "http://localhost:8000"

SEP = "=" * 60

def section(title):
    print("\n" + SEP)
    print(title)
    print(SEP)

# ── DB ──────────────────────────────────────────────────────────
section("1. DATABASE - ALL TABLES")

try:
    parsed = urlparse(DB_URL)
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=parsed.username,
        password=unquote(parsed.password),
        dbname=parsed.path.lstrip("/"),
        sslmode="require",
    )
    cur = conn.cursor()

    print("\n[public.users]")
    cur.execute("SELECT id, supabase_uid, email, role FROM public.users ORDER BY id")
    for r in cur.fetchall():
        print(f"  id={r[0]}  uid={r[1]}  email={r[2]}  role={r[3]}")

    print("\n[assessments]")
    cur.execute("SELECT id, title, status, published_at FROM assessments ORDER BY id")
    assessments = cur.fetchall()
    if not assessments:
        print("  (EMPTY)")
    for r in assessments:
        print(f"  id={r[0]}  title={r[1]}  status={r[2]}  published_at={r[3]}")

    print("\n[assessment_questions] counts per assessment:")
    cur.execute("SELECT assessment_id, COUNT(*) FROM assessment_questions GROUP BY assessment_id")
    aq_rows = cur.fetchall()
    if not aq_rows:
        print("  (EMPTY)")
    for r in aq_rows:
        print(f"  assessment_id={r[0]}  question_count={r[1]}")

    print("\n[assessment_interns] ALL ROWS:")
    cur.execute("SELECT id, assessment_id, intern_id, status, assigned_at FROM assessment_interns ORDER BY id")
    ai_rows = cur.fetchall()
    if not ai_rows:
        print("  (EMPTY -- no assignments at all)")
    for r in ai_rows:
        print(f"  id={r[0]}  assessment_id={r[1]}  intern_id={r[2]}  status={r[3]}  assigned_at={r[4]}")

    cur.close()
    conn.close()
except Exception as e:
    print(f"DB ERROR: {e}")
    import traceback; traceback.print_exc()

# ── LOGIN INTERN ────────────────────────────────────────────────
section("2. LOGIN AS INTERN")

intern_token = None
try:
    r = requests.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers={"apikey": ANON_KEY, "Content-Type": "application/json"},
        json={"email": INTERN_EMAIL, "password": INTERN_PASS},
        timeout=15
    )
    print(f"  Supabase status: {r.status_code}")
    if r.status_code == 200:
        d = r.json()
        intern_token = d.get("access_token")
        user_meta = d.get("user", {}).get("user_metadata", {})
        print(f"  Token obtained: {'YES' if intern_token else 'NO'}")
        print(f"  user_metadata: {json.dumps(user_meta)}")
    else:
        print(f"  FAILED: {r.text[:300]}")
        print("  >> Try password 'Intern@123' or check INTERN_PASS <<")
except Exception as e:
    print(f"  EXCEPTION: {e}")

# ── LOGIN AUTHORITY ─────────────────────────────────────────────
section("3. LOGIN AS AUTHORITY")

authority_token = None
try:
    r = requests.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers={"apikey": ANON_KEY, "Content-Type": "application/json"},
        json={"email": AUTHORITY_EMAIL, "password": AUTHORITY_PASS},
        timeout=15
    )
    print(f"  Supabase status: {r.status_code}")
    if r.status_code == 200:
        d = r.json()
        authority_token = d.get("access_token")
        print(f"  Token obtained: {'YES' if authority_token else 'NO'}")
    else:
        print(f"  FAILED: {r.text[:300]}")
except Exception as e:
    print(f"  EXCEPTION: {e}")

# ── /users/me as intern ─────────────────────────────────────────
section("4. GET /users/me AS INTERN")

if intern_token:
    try:
        r = requests.get(f"{API_BASE}/users/me",
                         headers={"Authorization": f"Bearer {intern_token}"}, timeout=10)
        print(f"  HTTP {r.status_code}")
        print(f"  Response: {r.text[:500]}")
    except requests.exceptions.ConnectionError:
        print("  CONNECTION REFUSED -- backend not running on port 8000")
    except Exception as e:
        print(f"  EXCEPTION: {e}")
else:
    print("  SKIPPED -- no intern token")

# ── /api/v1/assessments/intern/me ──────────────────────────────
section("5. GET /api/v1/assessments/intern/me AS INTERN")

if intern_token:
    try:
        r = requests.get(f"{API_BASE}/api/v1/assessments/intern/me",
                         headers={"Authorization": f"Bearer {intern_token}"}, timeout=10)
        print(f"  HTTP {r.status_code}")
        print(f"  Response: {r.text[:800]}")
    except requests.exceptions.ConnectionError:
        print("  CONNECTION REFUSED -- backend not running")
    except Exception as e:
        print(f"  EXCEPTION: {e}")
else:
    print("  SKIPPED -- no intern token")

# ── All assessments ─────────────────────────────────────────────
section("6. GET /api/v1/assessments/ AS AUTHORITY (to see what exists)")

if authority_token:
    try:
        r = requests.get(f"{API_BASE}/api/v1/assessments/",
                         headers={"Authorization": f"Bearer {authority_token}"}, timeout=10)
        print(f"  HTTP {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list):
                for a in data:
                    print(f"  assessment id={a.get('id')} title={a.get('title')!r} status={a.get('status')}")
            else:
                print(f"  Response: {r.text[:500]}")
        else:
            print(f"  Response: {r.text[:300]}")
    except requests.exceptions.ConnectionError:
        print("  CONNECTION REFUSED -- backend not running")
    except Exception as e:
        print(f"  EXCEPTION: {e}")
else:
    print("  SKIPPED -- no authority token")

# ── /interns/candidates (authority side) ───────────────────────
section("7. GET /interns/candidates AS AUTHORITY (assignment list)")

if authority_token:
    try:
        r = requests.get(f"{API_BASE}/interns/candidates",
                         headers={"Authorization": f"Bearer {authority_token}"}, timeout=10)
        print(f"  HTTP {r.status_code}")
        print(f"  Response: {r.text[:800]}")
    except requests.exceptions.ConnectionError:
        print("  CONNECTION REFUSED -- backend not running")
    except Exception as e:
        print(f"  EXCEPTION: {e}")
else:
    print("  SKIPPED -- no authority token")

print("\n" + SEP)
print("DIAGNOSTIC COMPLETE")
print(SEP)
