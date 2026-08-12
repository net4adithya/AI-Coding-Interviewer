import requests

url = "https://rfqmnstrnvipxknvrouy.supabase.co/auth/v1/token?grant_type=password"
headers = {
    "apikey": "sb_publishable_f6Kciw9KKmJdJwC-lbpeGQ_gNqyVtcs",
    "Content-Type": "application/json"
}

for email in ['authority@test.com', 'intern@test.com']:
    data = {
        "email": email,
        "password": "Ryanronalds@103992"
    }
    print(f"Logging in {email}...")
    res = requests.post(url, headers=headers, json=data)
    if res.status_code == 200:
        user = res.json().get('user')
        print(f"SUCCESS: {email} -> UID: {user.get('id')}")
        print(f"Token: {res.json().get('access_token')[:20]}...")
    else:
        print(f"FAILED {email}:", res.status_code, res.text)
