import psycopg2

try:
    print('Testing port 6543...')
    conn = psycopg2.connect(
        host='db.rfqmnstrnvipxknvrouy.supabase.co',
        port=6543,
        user='postgres',
        password='Ryanronalds@103992',
        dbname='postgres',
        sslmode='require',
        connect_timeout=10
    )
    print("SUCCESS on 6543!")
    conn.close()
except Exception as e:
    print('ERROR on 6543:', e)

try:
    print('Testing IPv4 resolution...')
    import socket
    ips = socket.gethostbyname_ex('db.rfqmnstrnvipxknvrouy.supabase.co')
    print("IPs:", ips)
except Exception as e:
    print('DNS Error:', e)

