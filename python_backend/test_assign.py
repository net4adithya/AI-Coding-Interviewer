import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import psycopg2
import requests
import json

SUPABASE_URL = "https://rfqmnstrnvipxknvrouy.supabase.co"
ANON_KEY     = "sb_publishable_f6Kciw9KKmJdJwC-lbpeGQ_gNqyVtcs"
AUTHORITY_EMAIL = "admin@test.com"
AUTHORITY_PASS  = "admin123"
INTERN_EMAIL = "intern@test.com"
API_BASE     = "http://localhost:8000"

# 1. Login Authority
r = requests.post(
    f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
    headers={"apikey": ANON_KEY, "Content-Type": "application/json"},
    json={"email": AUTHORITY_EMAIL, "password": AUTHORITY_PASS},
    timeout=15
)
if r.status_code != 200:
    print("Authority login failed:", r.text)
    sys.exit(1)

auth_token = r.json()["access_token"]
print("Authority logged in.")

# 2. Get Assessments
r = requests.get(
    f"{API_BASE}/api/v1/assessments/",
    headers={"Authorization": f"Bearer {auth_token}"}
)
assessments = r.json()
print("Assessments:", json.dumps(assessments, indent=2))

published_assessment_id = None
for a in assessments:
    if a["status"] == "PUBLISHED" or a["status"] == "ASSIGNED":
        published_assessment_id = a["id"]
        break

if not published_assessment_id:
    # Try to find generated
    for a in assessments:
        if a["status"] == "GENERATED":
            print(f"Publishing assessment {a['id']}")
            r = requests.post(
                f"{API_BASE}/api/v1/assessments/{a['id']}/publish",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            print("Publish result:", r.status_code, r.text)
            published_assessment_id = a["id"]
            break

if not published_assessment_id:
    print("No published or generated assessments found.")
    sys.exit(1)

print(f"Using assessment ID: {published_assessment_id}")

# 3. Assign Assessment
r = requests.post(
    f"{API_BASE}/api/v1/assessments/{published_assessment_id}/assign-email",
    headers={"Authorization": f"Bearer {auth_token}"},
    json={"email": INTERN_EMAIL}
)
print("Assign result:", r.status_code, r.text)

# 4. Check Candidates List
r = requests.get(
    f"{API_BASE}/interns/candidates",
    headers={"Authorization": f"Bearer {auth_token}"}
)
print("Candidates list:", r.status_code, json.dumps(r.json(), indent=2))
