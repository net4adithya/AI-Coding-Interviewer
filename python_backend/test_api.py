import os
import sys
sys.path.insert(0, os.path.abspath("."))
import requests
import json
from fastapi.testclient import TestClient
from main import app

# 1. Fetch real token from Supabase
url = 'https://rfqmnstrnvipxknvrouy.supabase.co/auth/v1/token?grant_type=password'
headers = {
    'apikey': 'sb_publishable_f6Kciw9KKmJdJwC-lbpeGQ_gNqyVtcs',
    'Content-Type': 'application/json'
}
data = {
    'email': 'intern@test.com',
    'password': '12345.'
}
res = requests.post(url, headers=headers, json=data)
token = res.json().get('access_token')

if not token:
    print("Failed to get token!")
    exit(1)

print("Got real token from Supabase")

# 2. Test endpoints with TestClient (which uses the real get_current_user and JWT verification)
client = TestClient(app)
api_headers = {
    "Authorization": f"Bearer {token}"
}

# Test 1: GET /users/me
print("Testing GET /users/me ...")
res_me = client.get("/users/me", headers=api_headers)
print("GET /users/me ->", res_me.status_code)
if res_me.status_code == 200:
    print(res_me.json())
else:
    print(res_me.text)

# Test 2: Upload PDF
print("Testing PDF upload ...")
pdf_path = "tests/test.pdf" # Make sure this exists, or create a dummy one
if not os.path.exists(pdf_path):
    print("No test.pdf found, creating a dummy one...")
    os.makedirs("tests", exist_ok=True)
    with open(pdf_path, "wb") as f:
        f.write(b"%PDF-1.4\n1 0 obj\n<<\n/Title (Dummy PDF)\n>>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF")

with open(pdf_path, "rb") as f:
    files = {"file": ("test.pdf", f, "application/pdf")}
    res_upload = client.post("/api/v1/assessments/question-banks/upload", headers=api_headers, files=files)
    
print("PDF Upload ->", res_upload.status_code)
if res_upload.status_code == 200:
    print(res_upload.json())
else:
    print(res_upload.text)

