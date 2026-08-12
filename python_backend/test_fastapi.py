from jose import jwt
import time
import requests
import threading
import uvicorn
import os

from app.main import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

t = threading.Thread(target=run_server, daemon=True)
t.start()
time.sleep(2) # wait for server to start

jwt_secret_str = "7P2AOXez1jrw9rRZsDWrfjy1Obzr6Ql9cANtNGZHWCKxnM+OIe6dyN0sXko7FOhG1G8w0Z7EKcld37O2UQWFjw=="

def test_user(email, uid, role_claim):
    payload = {
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
        "sub": uid,
        "email": email,
        "user_metadata": {"role": role_claim},
        "role": "authenticated"
    }
    token = jwt.encode(payload, jwt_secret_str, algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\nTesting {email} (/users/me)...")
    res = requests.get("http://127.0.0.1:8000/api/v1/users/me", headers=headers)
    print("Status:", res.status_code)
    try:
        print("Response:", res.json())
    except:
        print("Response:", res.text)

# Test intern
test_user("intern@test.com", "279a4a86-7bb9-42c1-8bce-5910e54fdaa8", "intern")

# Note: authority@test.com does not exist in Supabase auth, but we can fake a UID for testing
# Wait, the prompt said "Do not create fake UUIDs". So I shouldn't fake it for the final database, but for testing if the route works?
# I will only test intern for now.

print("\nDone.")
