import psycopg2

try:
    conn = psycopg2.connect(
        host='db.rfqmnstrnvipxknvrouy.supabase.co',
        port=5432,
        user='postgres',
        password='Ryanronalds@103992',
        dbname='postgres',
        sslmode='require'
    )
    with conn.cursor() as cur:
        print('--- AUTH USERS ---')
        cur.execute("SELECT id, email FROM auth.users WHERE email IN ('authority@test.com', 'intern@test.com')")
        for row in cur.fetchall():
            print(row)
            
        print('--- PUBLIC USERS ---')
        cur.execute("SELECT id, supabase_uid, email, role FROM public.users")
        for row in cur.fetchall():
            print(row)
except Exception as e:
    print('ERROR:', e)
