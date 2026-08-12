import sys
from app.db.session import SessionLocal
from app.users.models import User
from sqlalchemy import text
from app.config import settings

def run():
    print('Testing DB Connection via App Session...')
    try:
        db = SessionLocal()
        print('--- PUBLIC USERS ---')
        users = db.query(User).all()
        for u in users:
            print(u.id, u.supabase_uid, u.email, u.role)
        
        print('--- SUPABASE USERS ---')
        res = db.execute(text("SELECT id, email FROM auth.users WHERE email IN ('authority@test.com', 'intern@test.com')"))
        for r in res:
            print(r)
        
    except Exception as e:
        print('Error:', e)
    finally:
        db.close()

if __name__ == '__main__':
    run()
