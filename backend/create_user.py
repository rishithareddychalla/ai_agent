import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash

async def main():
    async with AsyncSessionLocal() as db:
        hashed_password = get_password_hash("Password@123")
        user = User(
            email="admin@webpilot.ai",
            hashed_password=hashed_password,
            full_name="Admin User",
            is_active=True
        )
        db.add(user)
        try:
            await db.commit()
            print("User admin@webpilot.ai created successfully!")
        except Exception as e:
            await db.rollback()
            print(f"Error creating user: {e}")

if __name__ == "__main__":
    asyncio.run(main())
