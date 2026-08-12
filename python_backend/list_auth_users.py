from jose import jwt
import time
import requests

jwt_secret_str = "7P2AOXez1jrw9rRZsDWrfjy1Obzr6Ql9cANtNGZHWCKxnM+OIe6dyN0sXko7FOhG1G8w0Z7EKcld37O2UQWFjw=="
anon_key = "sb_publishable_f6Kciw9KKmJdJwC-lbpeGQ_gNqyVtcs"
project_ref = "rfqmnstrnvipxknvrouy"
base_url = f"https://{project_ref}.supabase.co"

payload = {
    "role": "service_role",
    "iss": "supabase",
    "iat": int(time.time()),
    "exp": int(time.time()) + 3600
}
token_str = jwt.encode(payload, jwt_secret_str, algorithm="HS256")
headers = {
    "apikey": anon_key,
    "Authorization": f"Bearer {token_str}",
    "Content-Type": "application/json"
}

# 1. Fetch auth users
print("Fetching ALL Auth Users...")
res_auth = requests.get(f"{base_url}/auth/v1/admin/users", headers=headers)
if res_auth.status_code == 200:
    for u in res_auth.json().get('users', []):
        print(f"Auth User: {u.get('email')} -> UID: {u.get('id')}")
else:
    print("Failed to fetch auth users:", res_auth.status_code, res_auth.text)

