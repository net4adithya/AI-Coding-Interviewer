import requests
import json
from jose import jwt

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
if res.status_code == 200:
    token = res.json().get('access_token')
    print('Token fetched')
    header = jwt.get_unverified_header(token)
    print("HEADER:")
    print(json.dumps(header, indent=2))
else:
    print("FAILED:", res.status_code, res.text)
