#!/usr/bin/env python3
"""
Seed script for development cTrader credentials.
Loads credentials from .env.development and stores them encrypted in the database.

Usage:
    cd Bakend-bdt
    poetry run python scripts/seed_ctrader_credentials.py
"""

import asyncio
import os
import sys
import uuid
from pathlib import Path

# Load .env.development from project root
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env.development"

if env_file.exists():
    print(f"✅ Loading credentials from {env_file}")
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())
else:
    print(f"❌ Error: {env_file} not found")
    print("Please copy .env.development.example to .env.development and fill in your credentials")
    sys.exit(1)

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import async_session_factory
from app.modules.ctrader.models import CtraderCredentials
from app.modules.auth.models import User
from app.shared.crypto import encrypt


async def seed_ctrader_credentials():
    """Seed cTrader credentials from environment variables."""
    
    # Read credentials from environment
    client_id = os.getenv("CTRADER_CLIENT_ID")
    client_secret = os.getenv("CTRADER_CLIENT_SECRET")
    access_token = os.getenv("CTRADER_ACCESS_TOKEN")
    account_id = os.getenv("CTRADER_ACCOUNT_ID")
    is_demo = os.getenv("CTRADER_IS_DEMO", "true").lower() == "true"
    
    # Validate all required credentials are present
    if not all([client_id, client_secret, access_token, account_id]):
        print("❌ Error: Missing required environment variables")
        print("Required: CTRADER_CLIENT_ID, CTRADER_CLIENT_SECRET, CTRADER_ACCESS_TOKEN, CTRADER_ACCOUNT_ID")
        print("\nPlease copy .env.development.example to .env.development and fill in your credentials")
        sys.exit(1)
    
    print("✅ All credentials found in environment")
    print(f"   Client ID: {client_id[:10]}...")
    print(f"   Account ID: {account_id}")
    print(f"   Demo: {is_demo}")
    
    # Get the first user (development user)
    async with async_session_factory() as session:
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ Error: No users found in database")
            print("Please create a user first")
            sys.exit(1)
        
        print(f"✅ Found user: {user.email} ({user.id})")
        
        # Check if credentials already exist
        result = await session.execute(
            select(CtraderCredentials).where(CtraderCredentials.user_id == user.id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"⚠️  Updating existing credentials for user {user.email}")
            existing.client_id_enc = encrypt(client_id)
            existing.client_secret_enc = encrypt(client_secret)
            existing.access_token_enc = encrypt(access_token)
            existing.account_id_enc = encrypt(account_id)
            existing.is_demo = is_demo
            existing.account_name = "Development Account"
            existing.broker_name = "cTrader Demo"
        else:
            print(f"✅ Creating new credentials for user {user.email}")
            credentials = CtraderCredentials(
                id=uuid.uuid4(),
                user_id=user.id,
                client_id_enc=encrypt(client_id),
                client_secret_enc=encrypt(client_secret),
                access_token_enc=encrypt(access_token),
                account_id_enc=encrypt(account_id),
                is_demo=is_demo,
                account_name="Development Account",
                broker_name="cTrader Demo"
            )
            session.add(credentials)
        
        await session.commit()
        print("✅ Credentials saved successfully (encrypted)")
        print("\nYou can now test cTrader sync at: POST /ctrader/sync")


if __name__ == "__main__":
    asyncio.run(seed_ctrader_credentials())
