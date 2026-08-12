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
print("Fetching Auth Users...")
res_auth = requests.get(f"{base_url}/auth/v1/admin/users", headers=headers)
if res_auth.status_code == 200:
    for u in res_auth.json().get('users', []):
        if u.get('email') in ['authority@test.com', 'intern@test.com']:
            print(f"Auth User: {u['email']} -> UID: {u['id']}")
            
            # Now let's insert into public.users if not exists
            if u['email'] == 'authority@test.com':
                print(f"Checking public.users for {u['email']}...")
                res_check = requests.get(f"{base_url}/rest/v1/users?email=eq.authority@test.com", headers=headers)
                if res_check.status_code == 200 and len(res_check.json()) == 0:
                    print("Inserting authority@test.com into public.users...")
                    data = {
                        "supabase_uid": u['id'],
                        "email": u['email'],
                        "role": "authority"
                    }
                    res_insert = requests.post(f"{base_url}/rest/v1/users", headers=headers, json=data)
                    print("Insert response:", res_insert.status_code, res_insert.text)
                else:
                    print("User exists in public.users or error:", res_check.text)
                    
            if u['email'] == 'intern@test.com':
                print(f"Checking public.users for {u['email']}...")
                res_check = requests.get(f"{base_url}/rest/v1/users?email=eq.intern@test.com", headers=headers)
                if res_check.status_code == 200 and len(res_check.json()) == 0:
                    print("Inserting intern@test.com into public.users...")
                    data = {
                        "supabase_uid": u['id'],
                        "email": u['email'],
                        "role": "intern"
                    }
                    res_insert = requests.post(f"{base_url}/rest/v1/users", headers=headers, json=data)
                    print("Insert response:", res_insert.status_code, res_insert.text)
                elif res_check.status_code == 200:
                    print("intern@test.com already in public.users:", res_check.json())
else:
    print("Failed to fetch auth users:", res_auth.status_code, res_auth.text)

