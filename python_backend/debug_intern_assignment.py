"""
debug_intern_assignment.py
Full diagnostic: DB → Backend → Endpoint
Run from python_backend/ with the venv active.
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import psycopg2
import requests
import json

DB_URL = "postgresql://postgres.rfqmnstrnvipxknvrouy:Ryanronalds%40103992@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require"
SUPABASE_URL = "https://rfqmnstrnvipxknvrouy.supabase.co"
ANON_KEY     = "sb_publishable_f6Kciw9KKmJdJwC-lbpeGQ_gNqyVtcs"
INTERN_EMAIL = "intern@test.com"
INTERN_PASS  = "intern123"   # adjust if different
API_BASE     = "http://localhost:8000"

SEP = "=" * 60

# ── 1. DATABASE ────────────────────────────────────────────────
print(SEP)
print("1. DATABASE INSPECTION")
print(SEP)

try:
    # Build a direct connection string for psycopg2
    from urllib.parse import urlparse, unquote
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

    # Auth users
    print("\n[auth.users] Supabase auth records for test accounts:")
    cur.execute(
        "SELECT id, email FROM auth.users WHERE email IN ('authority@test.com','intern@test.com') ORDER BY email"
    )
    auth_rows = cur.fetchall()
    for r in auth_rows:
        print(f"  supabase_uid={r[0]}  email={r[1]}")

    # Local users
    print("\n[public.users] Local user records:")
    cur.execute("SELECT id, supabase_uid, email, role FROM public.users ORDER BY id")
    local_rows = cur.fetchall()
    for r in local_rows:
        print(f"  local_id={r[0]}  supabase_uid={r[1]}  email={r[2]}  role={r[3]}")

    # Find intern local id
    intern_local = next((r for r in local_rows if r[2] == INTERN_EMAIL), None)
    if intern_local:
        print(f"\n[INTERN] local_id={intern_local[0]}  supabase_uid={intern_local[1]}  role={intern_local[3]}")
        intern_local_id = intern_local[0]
    else:
        print(f"\n[INTERN] NOT FOUND in public.users! This is a critical problem.")
        intern_local_id = None

    # AssessmentIntern rows
    print("\n[assessment_interns] All rows:")
    cur.execute(
        """
        SELECT ai.id, ai.assessment_id, ai.intern_id, ai.status, ai.assigned_at
        FROM assessment_interns ai
        ORDER BY ai.assigned_at DESC
        """
    )
    ai_rows = cur.fetchall()
    if not ai_rows:
        print("  (empty — NO assignments exist)")
    for r in ai_rows:
        print(f"  assignment_id={r[0]}  assessment_id={r[1]}  intern_id={r[2]}  status={r[3]}  assigned_at={r[4]}")

    # Check intern's assignments specifically
    if intern_local_id:
        print(f"\n[assessment_interns] Rows where intern_id={intern_local_id}:")
        cur.execute(
            "SELECT id, assessment_id, intern_id, status FROM assessment_interns WHERE intern_id=%s",
            (intern_local_id,)
        )
        intern_ai = cur.fetchall()
        if not intern_ai:
            print(f"  (NONE — intern_id={intern_local_id} has NO assignments)")
        for r in intern_ai:
            print(f"  assignment_id={r[0]}  assessment_id={r[1]}  intern_id={r[2]}  status={r[3]}")

        # Join with assessments
        if intern_ai:
            for row in intern_ai:
                ass_id = row[1]
                cur.execute(
                    "SELECT id, title, status, published_at FROM assessments WHERE id=%s",
                    (ass_id,)
                )
                ass = cur.fetchone()
                if ass:
                    print(f"\n[assessments] id={ass[0]}  title={ass[1]}  status={ass[2]}  published_at={ass[3]}")
                    # Questions count
                    cur.execute(
                        "SELECT COUNT(*) FROM assessment_questions WHERE assessment_id=%s",
                        (ass[0],)
                    )
                    q_count = cur.fetchone()[0]
                    print(f"  question_count_in_assessment_questions={q_count}")
                else:
                    print(f"\n[assessments] id={ass_id} NOT FOUND!")

    cur.close()
    conn.close()
except Exception as e:
    print(f"DB ERROR: {e}")
    import traceback; traceback.print_exc()

# ── 2. SUPABASE LOGIN as intern ────────────────────────────────
print(f"\n{SEP}")
print("2. LOGIN AS INTERN → GET ACCESS TOKEN")
print(SEP)

access_token = None
try:
    login_res = requests.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers={
            "apikey": ANON_KEY,
            "Content-Type": "application/json"
        },
        json={"email": INTERN_EMAIL, "password": INTERN_PASS},
        timeout=15
    )
    print(f"  Supabase login status: {login_res.status_code}")
    if login_res.status_code == 200:
        login_data = login_res.json()
        access_token = login_data.get("access_token")
        user_meta   = login_data.get("user", {}).get("user_metadata", {})
        print(f"  access_token obtained: {'YES' if access_token else 'NO'}")
        print(f"  user_metadata: {json.dumps(user_meta)}")
        print(f"  user.role from token user_metadata: {user_meta.get('role', '(not set)')}")
    else:
        print(f"  ERROR: {login_res.text[:300]}")
        print("  → Cannot continue without a valid token. Check INTERN_PASS in this script.")
except Exception as e:
    print(f"  LOGIN EXCEPTION: {e}")

# ── 3. GET /users/me ───────────────────────────────────────────
print(f"\n{SEP}")
print("3. GET /users/me  (role check)")
print(SEP)

if access_token:
    try:
        r = requests.get(
            f"{API_BASE}/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        print(f"  HTTP {r.status_code}")
        print(f"  Response: {r.text[:500]}")
        if r.status_code == 200:
            me = r.json()
            print(f"\n  ✓ DB role for intern: {me.get('role')}")
            print(f"  ✓ local id: {me.get('id')}")
            print(f"  ✓ supabase_uid: {me.get('supabase_uid')}")
    except Exception as e:
        print(f"  EXCEPTION: {e}")
else:
    print("  SKIPPED — no access token")

# ── 4. GET /api/v1/assessments/intern/me ──────────────────────
print(f"\n{SEP}")
print("4. GET /api/v1/assessments/intern/me  (intern assignment)")
print(SEP)

if access_token:
    try:
        r = requests.get(
            f"{API_BASE}/api/v1/assessments/intern/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        print(f"  HTTP {r.status_code}")
        print(f"  Response: {r.text[:1000]}")
    except requests.exceptions.ConnectionError:
        print("  CONNECTION REFUSED — backend is not running on port 8000")
    except Exception as e:
        print(f"  EXCEPTION: {e}")
else:
    print("  SKIPPED — no access token")

# ── 5. GET /api/v1/assessments/ (all assessments) ─────────────
print(f"\n{SEP}")
print("5. GET /api/v1/assessments/ (all assessments — as intern)")
print(SEP)

if access_token:
    try:
        r = requests.get(
            f"{API_BASE}/api/v1/assessments/",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )
        print(f"  HTTP {r.status_code}")
        try:
            data = r.json()
            for a in (data if isinstance(data, list) else [data]):
                print(f"  assessment id={a.get('id')} title={a.get('title')} status={a.get('status')}")
        except Exception:
            print(f"  Response: {r.text[:500]}")
    except requests.exceptions.ConnectionError:
        print("  CONNECTION REFUSED — backend is not running")
    except Exception as e:
        print(f"  EXCEPTION: {e}")
else:
    print("  SKIPPED — no access token")

print(f"\n{SEP}")
print("DIAGNOSIS COMPLETE")
print(SEP)
