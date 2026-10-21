import sys
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.db import get_db
from face_atm.face_recognizer import LBPHFaceManager

def train_all():
    print("Fetching all users from database...")
    conn = get_db()
    users = conn.execute("SELECT account_number FROM users").fetchall()
    conn.close()
    
    if not users:
        print("No users found in database.")
        return

    fr = LBPHFaceManager()
    success_count = 0
    fail_count = 0

    print(f"Found {len(users)} users. Starting complete model training...\n")

    for user in users:
        acc = user['account_number']
        print(f"[{acc}] Starting training...")
        success, msg, count = fr.train_user_model(acc)
        
        if success:
            print(f"[{acc}] SUCCESS: {msg}")
            success_count += 1
        else:
            print(f"[{acc}] FAILED: {msg}")
            fail_count += 1
            
    print(f"\nTraining Complete! Successfully trained: {success_count}, Failed: {fail_count}")

if __name__ == "__main__":
    train_all()
