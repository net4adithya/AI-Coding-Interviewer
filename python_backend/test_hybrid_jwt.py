from jose import jwt
import time
import requests
import base64

jwt_secret_str = "7P2AOXez1jrw9rRZsDWrfjy1Obzr6Ql9cANtNGZHWCKxnM+OIe6dyN0sXko7FOhG1G8w0Z7EKcld37O2UQWFjw=="
# Usually Supabase JWT secrets are plain strings? Or base64? Let's just use string first.
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

res = requests.get(f"{base_url}/rest/v1/users?select=*", headers=headers)
print("Token (str) response:", res.status_code)
if res.status_code == 200:
    print(res.json())
else:
    print(res.text)
    
    # Try with base64 decoded secret
    jwt_secret_decoded = base64.b64decode(jwt_secret_str)
    token_dec = jwt.encode(payload, jwt_secret_decoded, algorithm="HS256")
    headers["Authorization"] = f"Bearer {token_dec}"
    res2 = requests.get(f"{base_url}/rest/v1/users?select=*", headers=headers)
    print("Token (dec) response:", res2.status_code)
    if res2.status_code == 200:
        print(res2.json())
    else:
        print(res2.text)
