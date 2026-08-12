from jose import jwt
import time
import requests

jwt_secret = "7P2AOXez1jrw9rRZsDWrfjy1Obzr6Ql9cANtNGZHWCKxnM+OIe6dyN0sXko7FOhG1G8w0Z7EKcld37O2UQWFjw=="
project_ref = "rfqmnstrnvipxknvrouy"
base_url = f"https://{project_ref}.supabase.co"

# Mint a service_role JWT
payload = {
    "role": "service_role",
    "iss": "supabase",
    "iat": int(time.time()),
    "exp": int(time.time()) + 3600
}

token = jwt.encode(payload, jwt_secret, algorithm="HS256")
headers = {
    "apikey": token,
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 1. Fetch auth users
print("Fetching Auth Users...")
res = requests.get(f"{base_url}/auth/v1/users", headers=headers)
if res.status_code == 200:
    for u in res.json().get('users', []):
        if u.get('email') in ['authority@test.com', 'intern@test.com']:
            print(f"Auth User: {u['email']} -> {u['id']}")
else:
    print(f"Failed to fetch auth users: {res.status_code} {res.text}")

# 2. Fetch public users
print("\nFetching Public Users...")
res = requests.get(f"{base_url}/rest/v1/users?select=*", headers=headers)
if res.status_code == 200:
    for u in res.json():
        if u.get('email') in ['authority@test.com', 'intern@test.com']:
            print(f"Public User: {u}")
else:
    print(f"Failed to fetch public users: {res.status_code} {res.text}")
