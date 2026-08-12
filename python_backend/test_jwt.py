from jose import jwt
import time
import requests
import base64

jwt_secret_str = "7P2AOXez1jrw9rRZsDWrfjy1Obzr6Ql9cANtNGZHWCKxnM+OIe6dyN0sXko7FOhG1G8w0Z7EKcld37O2UQWFjw=="
jwt_secret_decoded = base64.b64decode(jwt_secret_str)

project_ref = "rfqmnstrnvipxknvrouy"
base_url = f"https://{project_ref}.supabase.co"

payload = {
    "role": "service_role",
    "iss": "supabase",
    "iat": int(time.time()),
    "exp": int(time.time()) + 3600
}

print("Trying base64 decoded secret...")
token2 = jwt.encode(payload, jwt_secret_decoded, algorithm="HS256")
headers2 = {
    "apikey": token2,
    "Authorization": f"Bearer {token2}",
    "Content-Type": "application/json"
}

res2 = requests.get(f"{base_url}/rest/v1/users?select=*", headers=headers2)
print("Token 2 response:", res2.status_code)
if res2.status_code == 200:
    print("SUCCESS with decoded secret!")
    print(res2.json())
else:
    print("Failed.", res2.text)

# We also need to get auth.users if it works
if res2.status_code == 200:
    res3 = requests.get(f"{base_url}/auth/v1/users", headers=headers2)
    if res3.status_code == 200:
        for u in res3.json().get('users', []):
            if u.get('email') in ['authority@test.com', 'intern@test.com']:
                print(f"Auth User: {u['email']} -> {u['id']}")
