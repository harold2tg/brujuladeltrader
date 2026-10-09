#!/bin/bash
# Script para actualizar credenciales de cTrader desde .env.development
# Uso: ./scripts/update_ctrader_credentials.sh

set -e

cd "$(dirname "$0")/.."

# Cargar variables del .env.development
if [ ! -f .env.development ]; then
    echo "❌ Error: No se encontró .env.development"
    exit 1
fi

source .env.development

# Verificar que existan las variables
if [ -z "$CTRADER_CLIENT_ID" ] || [ -z "$CTRADER_CLIENT_SECRET" ] || [ -z "$CTRADER_ACCESS_TOKEN" ]; then
    echo "❌ Error: Faltan variables en .env.development"
    echo "Necesitas definir:"
    echo "  CTRADER_CLIENT_ID"
    echo "  CTRADER_CLIENT_SECRET"
    echo "  CTRADER_ACCESS_TOKEN"
    exit 1
fi

# Obtener el user_id del usuario de prueba
USER_ID=$(docker compose -f docker-compose.dev.yml exec -T db psql -U brujula -d brujula_db -t -c \
    "SELECT id FROM users WHERE email='test@test.com'" | tr -d '[:space:]')

if [ -z "$USER_ID" ]; then
    echo "❌ Error: No se encontró el usuario test@test.com"
    exit 1
fi

echo "✅ Usuario encontrado: $USER_ID"

# Ejecutar el script de actualización dentro del contenedor
docker compose -f docker-compose.dev.yml exec -T api python3 - <<EOF
import sys
import os
sys.path.insert(0, '/app')

# Establecer variables de entorno desde el script bash
os.environ['CTRADER_CLIENT_ID'] = '$CTRADER_CLIENT_ID'
os.environ['CTRADER_CLIENT_SECRET'] = '$CTRADER_CLIENT_SECRET'
os.environ['CTRADER_ACCESS_TOKEN'] = '$CTRADER_ACCESS_TOKEN'

from sqlalchemy import select
from app.database import async_session_factory
from app.modules.ctrader.models import CtraderCredentials
from app.shared.crypto import encrypt
import asyncio

async def update_credentials():
    client_id = os.environ['CTRADER_CLIENT_ID']
    client_secret = os.environ['CTRADER_CLIENT_SECRET']
    access_token = os.environ['CTRADER_ACCESS_TOKEN']
    user_id = '$USER_ID'
    
    async with async_session_factory() as session:
        result = await session.execute(
            select(CtraderCredentials).where(CtraderCredentials.user_id == user_id)
        )
        creds = result.scalar_one_or_none()
        
        if creds:
            print(f"✅ Actualizando credenciales para usuario {user_id}")
            creds.client_id_enc = encrypt(client_id)
            creds.client_secret_enc = encrypt(client_secret)
            creds.access_token_enc = encrypt(access_token)
            creds.account_id_enc = encrypt('')  # Auto-descubrir
        else:
            print(f"❌ No se encontró credenciales para usuario {user_id}")
            print("   Ejecuta primero: poetry run python scripts/seed_ctrader_credentials.py")
            return
        
        await session.commit()
        print("✅ Credenciales actualizadas exitosamente")
        print("✅ Account ID está vacío - se auto-descubrirá en el próximo sync")

asyncio.run(update_credentials())
EOF

echo ""
echo "✅ Proceso completado"
echo ""
echo "Ahora prueba el sync:"
echo "  TOKEN=\$(curl -s -X POST http://localhost:8001/auth/login \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"email\":\"test@test.com\",\"password\":\"Test123!\"}' | jq -r '.data.access_token')"
echo ""
echo "  curl -X POST http://localhost:8001/ctrader/sync \\"
echo "    -H \"Authorization: Bearer \$TOKEN\" \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"mode\":\"month\",\"date\":\"2026-10-01\"}'"
