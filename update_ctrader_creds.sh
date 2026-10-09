#!/bin/bash
# Script para actualizar credenciales de cTrader desde .env.development
# Ejecuta este script localmente - NO requiere compartir credenciales

set -e

echo "🔐 Actualizando credenciales de cTrader desde .env.development..."

# Cargar variables del archivo .env.development
if [ ! -f ".env.development" ]; then
    echo "❌ Error: No se encontró .env.development"
    exit 1
fi

# Cargar variables
source .env.development

# Verificar que existan las variables necesarias
if [ -z "$CTRADER_CLIENT_ID" ] || [ -z "$CTRADER_CLIENT_SECRET" ] || [ -z "$CTRADER_ACCESS_TOKEN" ]; then
    echo "❌ Error: Faltan variables en .env.development"
    echo "   Necesitas: CTRADER_CLIENT_ID, CTRADER_CLIENT_SECRET, CTRADER_ACCESS_TOKEN"
    exit 1
fi

echo "✅ Variables encontradas en .env.development"

# Obtener el user_id del usuario de prueba
USER_ID=$(docker compose -f docker-compose.dev.yml exec -T db psql -U brujula -d brujula_db -t -c \
    "SELECT id FROM users WHERE email='test@test.com' LIMIT 1;" | xargs)

if [ -z "$USER_ID" ]; then
    echo "❌ Error: No se encontró el usuario test@test.com"
    exit 1
fi

echo "✅ Usuario encontrado: $USER_ID"

# Ejecutar el script de seed dentro del contenedor
docker compose -f docker-compose.dev.yml exec -T api python3 << EOF
import os
import sys
sys.path.insert(0, '/app')

from sqlalchemy import select
from app.database import async_session_factory
from app.modules.ctrader.models import CtraderCredentials
from app.shared.crypto import encrypt
import asyncio

async def update_credentials():
    # Credenciales desde variables de entorno (inyectadas por el script bash)
    client_id = os.environ['CTRADER_CLIENT_ID']
    client_secret = os.environ['CTRADER_CLIENT_SECRET']
    access_token = os.environ['CTRADER_ACCESS_TOKEN']
    user_id = '$USER_ID'
    
    async with async_session_factory() as session:
        # Buscar credenciales existentes
        result = await session.execute(
            select(CtraderCredentials).where(CtraderCredentials.user_id == user_id)
        )
        creds = result.scalar_one_or_none()
        
        if creds:
            print(f"✅ Actualizando credenciales existentes para usuario {user_id}")
            creds.client_id_enc = encrypt(client_id)
            creds.client_secret_enc = encrypt(client_secret)
            creds.access_token_enc = encrypt(access_token)
            creds.account_id_enc = encrypt('')  # Dejar vacío para auto-descubrimiento
        else:
            print(f"✅ Creando nuevas credenciales para usuario {user_id}")
            new_creds = CtraderCredentials(
                user_id=user_id,
                client_id_enc=encrypt(client_id),
                client_secret_enc=encrypt(client_secret),
                access_token_enc=encrypt(access_token),
                account_id_enc=encrypt(''),  # Dejar vacío para auto-descubrimiento
                is_demo=True
            )
            session.add(new_creds)
        
        await session.commit()
        print("✅ Credenciales actualizadas exitosamente")

asyncio.run(update_credentials())
EOF

# Pasar las variables al contenedor
export CTRADER_CLIENT_ID
export CTRADER_CLIENT_SECRET
export CTRADER_ACCESS_TOKEN

echo ""
echo "✅ Proceso completado"
echo "📊 Prueba el sync con:"
echo "   TOKEN=\$(curl -s -X POST http://localhost:8001/auth/login \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"email\":\"test@test.com\",\"password\":\"Test123!\"}' | jq -r '.data.access_token')"
echo ""
echo "   curl -X POST http://localhost:8001/ctrader/sync \\"
echo "     -H \"Authorization: Bearer \$TOKEN\" \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"mode\":\"month\",\"date\":\"2026-10-01\"}'"
