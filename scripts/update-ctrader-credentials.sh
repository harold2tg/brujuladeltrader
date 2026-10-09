#!/bin/bash
# Script para actualizar credenciales de cTrader
# Uso: ./scripts/update-ctrader-credentials.sh

set -e

echo "🔐 Actualizando credenciales de cTrader..."
echo ""

# Cargar el archivo .env
if [ ! -f .env ]; then
    echo "❌ Error: No se encontró el archivo .env"
    echo "   Copia .env.example a .env y configura tus credenciales"
    exit 1
fi

source .env

# Verificar que existan las variables necesarias
if [ -z "$CTRADER_ACCESS_TOKEN" ]; then
    echo "❌ Error: CTRADER_ACCESS_TOKEN no está configurado en .env"
    exit 1
fi

echo "✅ Leyendo credenciales desde .env"
echo "   Access Token: ${CTRADER_ACCESS_TOKEN:0:20}..."
echo ""

# Ejecutar script Python dentro del contenedor
docker compose -f docker-compose.dev.yml exec api python3 << 'PYTHON_SCRIPT'
import asyncio
import os
from sqlalchemy import select
from app.database import async_session_factory
from app.modules.ctrader.models import CtraderCredentials
from app.shared.crypto import encrypt

async def update_credentials():
    # Obtener credenciales desde variables de entorno
    access_token = os.environ.get('CTRADER_ACCESS_TOKEN')
    client_id = os.environ.get('CTRADER_CLIENT_ID')
    client_secret = os.environ.get('CTRADER_CLIENT_SECRET')
    
    if not access_token:
        print("❌ Error: CTRADER_ACCESS_TOKEN no está configurado")
        return
    
    async with async_session_factory() as session:
        # Buscar credenciales existentes para el usuario test
        from app.modules.auth.models import User
        user_result = await session.execute(
            select(User).where(User.email == 'test@test.com')
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            print("❌ Error: Usuario test@test.com no encontrado")
            return
        
        print(f"✅ Usuario encontrado: {user.email}")
        
        # Buscar credenciales de cTrader existentes
        result = await session.execute(
            select(CtraderCredentials).where(CtraderCredentials.user_id == user.id)
        )
        creds = result.scalar_one_or_none()
        
        if creds:
            print(f"✅ Actualizando credenciales existentes...")
            creds.access_token_enc = encrypt(access_token)
            if client_id:
                creds.client_id_enc = encrypt(client_id)
            if client_secret:
                creds.client_secret_enc = encrypt(client_secret)
        else:
            print("❌ Error: No se encontraron credenciales. Ejecuta primero seed_ctrader_credentials.py")
            return
        
        await session.commit()
        print("✅ Credenciales actualizadas exitosamente")
        print("✅ Ahora intenta sincronizar desde la interfaz web")

asyncio.run(update_credentials())
PYTHON_SCRIPT

echo ""
echo "✅ Proceso completado"
echo ""
echo "📝 Próximos pasos:"
echo "   1. Recarga la página web (Ctrl+F5)"
echo "   2. Ve a la sección de cTrader"
echo "   3. Intenta sincronizar"
