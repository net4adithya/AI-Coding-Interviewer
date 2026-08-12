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

users_to_update = {
    "admin@test.com": {"password": "12345678", "role": "authority"},
    "intern@test.com": {"password": "12345.", "role": "intern"}
}

# 1. Fetch all users
res_auth = requests.get(f"{base_url}/auth/v1/admin/users", headers=headers)
if res_auth.status_code != 200:
    print("Failed to fetch auth users:", res_auth.text)
    exit(1)

existing_users = {u['email']: u for u in res_auth.json().get('users', [])}

for email, data in users_to_update.items():
    if email in existing_users:
        uid = existing_users[email]['id']
        print(f"Updating password for {email} ({uid})...")
        res_update = requests.put(f"{base_url}/auth/v1/admin/users/{uid}", headers=headers, json={"password": data['password'], "user_metadata": {"role": data['role'], "full_name": email.split('@')[0]}})
        print("Update res:", res_update.status_code, res_update.text)
    else:
        print(f"Creating user {email}...")
        res_create = requests.post(f"{base_url}/auth/v1/admin/users", headers=headers, json={"email": email, "password": data['password'], "email_confirm": True, "user_metadata": {"role": data['role'], "full_name": email.split('@')[0]}})
        print("Create res:", res_create.status_code, res_create.text)
        if res_create.status_code in [200, 201]:
            uid = res_create.json()['id']
            existing_users[email] = res_create.json()
        else:
            print("Failed to create user, skipping DB insert.")
            continue
            
    # Also ensure they are in local db
    print(f"Checking public.users for {email}...")
    res_check = requests.get(f"{base_url}/rest/v1/users?email=eq.{email}", headers=headers)
    if res_check.status_code == 200:
        if len(res_check.json()) == 0:
            print(f"Inserting {email} into public.users...")
            db_data = {
                "supabase_uid": existing_users[email]['id'],
                "email": email,
                "role": data['role']
            }
            res_insert = requests.post(f"{base_url}/rest/v1/users", headers=headers, json=db_data)
            print("Insert response:", res_insert.status_code, res_insert.text)
        else:
            print(f"{email} already in public.users")
