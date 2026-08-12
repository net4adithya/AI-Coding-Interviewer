import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    print("DATABASE_URL not set in environment.")
    exit(1)

try:
    engine = create_engine(database_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        if result == 1:
            print("SQLAlchemy test: PASS")
            print("SELECT 1 test: PASS")
        else:
            print(f"SELECT 1 returned unexpected result: {result}")
            print("SELECT 1 test: FAIL")
            print("SQLAlchemy test: FAIL")
except Exception as e:
    print(f"SQLAlchemy / SELECT 1 test failed with exception: {type(e).__name__}: {str(e)}")
    print("SQLAlchemy test: FAIL")
    print("SELECT 1 test: FAIL")
