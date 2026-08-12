import urllib.request, urllib.error
try:
    print(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/assessments').read().decode())
except urllib.error.HTTPError as e:
    print(e.code, e.read())
except Exception as e:
    print(e)
