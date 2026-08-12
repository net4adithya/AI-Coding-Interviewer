import requests

url = "https://rfqmnstrnvipxknvrouy.supabase.co/rest/v1/"
try:
    res = requests.head(url)
    print("Headers:")
    for k, v in res.headers.items():
        if 'region' in k.lower() or 'server' in k.lower() or 'sb' in k.lower() or 'x-' in k.lower():
            print(f"{k}: {v}")
except Exception as e:
    print("Error:", e)
