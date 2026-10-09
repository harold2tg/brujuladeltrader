#!/usr/bin/env python3
"""
Script para actualizar credenciales de cTrader desde .env.development
Uso: cd Bakend-bdt && poetry run python scripts/update_ctrader_credentials.py
"""

import os
import sys
import asyncio
from pathlib import Path

# Cargar variables desde .env.development
env_file = Path(__file__).parent.parent.parent / '.env.development'
if not env_file.exists():
    print(f"❌ Error: No se encontró {env_file}")
    sys.exit(1)

# Leer variables del archivo
with open(env_file) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key] = value

# Verificar que existan las variables necesarias
required_vars = ['CTRADER_CLIENT_ID', 'CTRADER_CLIENT_SECRET', 'CTRADER_ACCESS_TOKEN']
missing = [var for var in required_vars if not os.environ.get(var)]
if missing:
    print(f"❌ Error: Faltan variables en .env.development:")
    for var in missing:
        print(f"   - {var}")
    sys.exit(1)

# Importar después de cargar las variables
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.database import async_session_factory
from app.modules.ctrader.models import CtraderCredentials
from app.shared.crypto import encrypt

async def main():
    client_id = os.environ['CTRADER_CLIENT_ID']
    client_secret = os.environ['CTRADER_CLIENT_SECRET']
    access_token = os.environ['CTRADER_ACCESS_TOKEN']
    
    # Buscar el usuario de prueba
    async with async_session_factory() as session:
        from app.modules.auth.models import User
        result = await session.execute(
            select(User).where(User.email == 'test@test.com')
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ Error: No se encontró el usuario test@test.com")
            sys.exit(1)
        
        print(f"✅ Usuario encontrado: {user.email}")
        
        # Buscar credenciales existentes
        result = await session.execute(
            select(CtraderCredentials).where(CtraderCredentials.user_id == user.id)
        )
        creds = result.scalar_one_or_none()
        
        if not creds:
            print(f"❌ Error: No se encontraron credenciales para el usuario")
            print("   Ejecuta primero: poetry run python scripts/seed_ctrader_credentials.py")
            sys.exit(1)
        
        # Actualizar credenciales
        print(f"✅ Actualizando credenciales para usuario {user.email}")
        creds.client_id_enc = encrypt(client_id)
        creds.client_secret_enc = encrypt(client_secret)
        creds.access_token_enc = encrypt(access_token)
        creds.account_id_enc = encrypt('')  # Auto-descubrir
        
        await session.commit()
        
        print("✅ Credenciales actualizadas exitosamente")
        print("✅ Account ID está vacío - se auto-descubrirá en el próximo sync")
        print()
        print("Ahora prueba el sync:")
        print("  TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \\")
        print("    -H 'Content-Type: application/json' \\")
        print("    -d '{\"email\":\"test@test.com\",\"password\":\"Test123!\"}' | jq -r '.data.access_token')")
        print()
        print("  curl -X POST http://localhost:8001/ctrader/sync \\")
        print("    -H \"Authorization: Bearer $TOKEN\" \\")
        print("    -H 'Content-Type: application/json' \\")
        print("    -d '{\"mode\":\"month\",\"date\":\"2026-10-01\"}'")

if __name__ == '__main__':
    asyncio.run(main())
