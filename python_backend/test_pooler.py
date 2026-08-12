import psycopg2

try:
    print('Testing pooler connection on 5432...')
    conn = psycopg2.connect(
        host='aws-0-ap-south-1.pooler.supabase.com',
        port=5432,
        user='postgres.rfqmnstrnvipxknvrouy',
        password='Ryanronalds@103992',
        dbname='postgres',
        sslmode='require',
        connect_timeout=10
    )
    with conn.cursor() as cur:
        cur.execute("SELECT id, email, role FROM public.users")
        for row in cur.fetchall():
            print(row)
    print("SUCCESS!")
    conn.close()
except Exception as e:
    print('ERROR:', e)
