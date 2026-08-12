import socket

try:
    ips = socket.gethostbyname_ex('aws-0-ap-south-1.pooler.supabase.com')
    print("Resolved:", ips)
except Exception as e:
    print("DNS Error:", e)

try:
    ips2 = socket.gethostbyname_ex('pooler.supabase.com')
    print("Resolved pooler:", ips2)
except Exception as e:
    print("pooler.supabase.com error:", e)
