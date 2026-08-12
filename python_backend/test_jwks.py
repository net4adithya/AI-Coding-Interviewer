import requests
from jose import jwt
import json

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

jwks_url = 'https://rfqmnstrnvipxknvrouy.supabase.co/auth/v1/.well-known/jwks.json'
jwks = requests.get(jwks_url).json()

try:
    payload = jwt.decode(token, jwks, algorithms=['ES256', 'RS256'], options={"verify_aud": False})
    print("SUCCESS PAYLOAD:", payload.get("email"))
except Exception as e:
    print("ERROR:", e)
