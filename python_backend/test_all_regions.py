import psycopg2
import concurrent.futures

regions = [
    'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
    'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1', 'eu-central-2',
    'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1', 'ap-northeast-2',
    'ap-northeast-3', 'ap-south-1', 'sa-east-1', 'ca-central-1'
]

def test_region(region):
    host = f'aws-0-{region}.pooler.supabase.com'
    try:
        conn = psycopg2.connect(
            host=host,
            port=5432,
            user='postgres.rfqmnstrnvipxknvrouy',
            password='Ryanronalds@103992',
            dbname='postgres',
            sslmode='require',
            connect_timeout=5
        )
        conn.close()
        return f"SUCCESS: {region}"
    except Exception as e:
        return f"FAIL {region}: {str(e).strip()}"

print("Testing all regions...")
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = executor.map(test_region, regions)
    
for r in results:
    if "SUCCESS" in r:
        print(r)
        
print("Done.")
