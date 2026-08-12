import requests

project_ref = 'rfqmnstrnvipxknvrouy'
urls_to_try = [
    f'https://{project_ref}.supabase.co/rest/v1/jwks',
    f'https://{project_ref}.supabase.co/auth/v1/jwks',
    f'https://{project_ref}.supabase.co/auth/v1/.well-known/jwks.json',
    f'https://{project_ref}.supabase.co/auth/v1/projects/{project_ref}/jwks'
]

for url in urls_to_try:
    print("Trying:", url)
    try:
        res = requests.get(url)
        print("Status:", res.status_code)
        if res.status_code == 200:
            print("Response:", res.text[:200])
    except Exception as e:
        print("Error:", e)
