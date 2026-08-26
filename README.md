# La Brújula del Trader

> Plataforma de análisis de trading para traders de XAUUSD (Oro). Subí tus operaciones, analizalas con IA, y improve tu estrategia.

---

## Tabla de Contenidos

1. [Qué es](#qué-es)
2. [Prerrequisitos](#prerrequisitos)
3. [Servicios de Terceros (API Keys)](#servicios-de-terceros-api-keys)
4. [Configuración Rápida](#configuración-rápida)
5. [Variables de Entorno](#variables-de-entorno)
6. [Ejecutar el Proyecto](#ejecutar-el-proyecto)
7. [Puertos y Servicios](#puertos-y-servicios)
8. [Cuenta de Prueba](#cuenta-de-prueba)
9. [Comandos Útiles](#comandos-útiles)
10. [Troubleshooting](#troubleshooting)

---

## Qué es

```
┌─────────────────────────────────────────────────────────┐
│                    TU NAVEGADOR                         │
│                  http://localhost:3001                   │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │   Dashboard  │  │  Subir CSV   │  │  Análisis IA  │  │
│  │  Resumen de  │  │  Operaciones │  │  Claude/GPT/  │  │
│  │  trades      │  │  de trading  │  │  Gemini       │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
├─────────────────────────────────────────────────────────┤
│              Conexión cTrader (OAuth2)                  │
│         Sync automática de operaciones reales           │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   API (FastAPI)                         │
│                  http://localhost:8001                   │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │   Auth   │  │  Parser  │  │ AI Engine│  │cTrader │  │
│  │  JWT +   │  │  CSV/    │  │ Análisis │  │ OAuth2 │  │
│  │  bcrypt  │  │  MT4/MT5 │  │ trades   │  │ Sync   │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘  │
├─────────────────────────────────────────────────────────┤
│              PostgreSQL (puerto 5433)                   │
│              Redis (puerto 6379)                        │
└─────────────────────────────────────────────────────────┘
```

---

## Prerrequisitos

| Requisito | Versión Mínima | Cómo verificar |
|-----------|----------------|----------------|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | v24+ | `docker --version` |
| [Docker Compose](https://docs.docker.com/compose/install/) | v2.20+ | `docker compose version` |
| Git | Cualquiera | `git --version` |
| [Node.js](https://nodejs.org/) | 18+ (solo sin Docker) | `node --version` |

> **Nota:** Solo necesitás Docker. No es obligatorio instalar Node.js ni Python en tu máquina.

---

## Servicios de Terceros (API Keys)

Para que el sistema funcione al 100%, necesitás cuentas en estos servicios. **Algunos son opcionales**.

### 🔴 OBLIGATORIO

#### 1. cTrader Open API (conexión automática de trades)

| Campo | Dónde obtenerlo |
|-------|-----------------|
| **Client ID** | https://openapi.ctrader.com/apps → Create New App |
| **Client Secret** | Se genera al crear la app |

**Pasos:**
1. Andá a https://openapi.ctrader.com/apps
2. Creá una cuenta (o logueate con tu cuenta de cTrader)
3. Click en **"Create New App"**
4. Completá:
   - **App Name**: `La Brújula del Trader` (o lo que quieras)
   - **Redirect URI**: `http://localhost:8001/ctrader/callback`
   - **App Type**: `Web App`
5. Guardá el **Client ID** y **Client Secret**
6. En **cTrader Desktop**, andá a **Settings → API Trading** y activá las cuentas que querés sincronizar

> ⚠️ **El Redirect URI debe ser EXACTAMENTE** `http://localhost:8001/ctrader/callback` (sin `/` al final)

### 🟡 OPCIONAL (al menos uno para análisis IA)

#### 2. Anthropic Claude (recomendado)

| Campo | Dónde obtenerlo |
|-------|-----------------|
| **API Key** | https://console.anthropic.com/ → API Keys |

**Costo:** ~$3-10/mes depending on usage

#### 3. OpenAI

| Campo | Dónde obtenerlo |
|-------|-----------------|
| **API Key** | https://platform.openai.com/api-keys |

**Costo:** ~$5-15/mes depending on usage

#### 4. Google Gemini

| Campo | Dónde obtenerlo |
|-------|-----------------|
| **API Key** | https://aistudio.google.com/apikey |

**Costo:** Gratis tier disponible

#### 5. Ollama (gratis, local)

No necesita API key. Corre en tu máquina.

```bash
# Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Descargar modelo
ollama pull llama3
```

### 🟢 OPCIONAL (producción)

#### 6. AWS S3 (almacenamiento en la nube)

| Campo | Dónde obtenerlo |
|-------|-----------------|
| **AWS_ACCESS_KEY_ID** | AWS Console → IAM → Users → Security credentials |
| **AWS_SECRET_ACCESS_KEY** | Se genera al crear access key |
| **AWS_BUCKET_NAME** | AWS Console → S3 → Create bucket |

> En desarrollo local no necesitás S3. Los archivos se guardan en disco.

---

## Configuración Rápida

### Paso 1: Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/brujuladeltrader.git
cd brujuladeltrader
```

### Paso 2: Crear archivos de entorno

```bash
# Backend
cp Bakend-bdt/.env.example Bakend-bdt/.env

# Frontend (ya viene configurado para Docker)
cp frontend-bdt/.env.local.example frontend-bdt/.env.local
```

### Paso 3: Generar secrets

```bash
# Generar APP_SECRET_KEY
openssl rand -hex 32

# Generar JWT_SECRET_KEY
openssl rand -hex 32

# Generar ENCRYPTION_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copiá cada valor generado en `Bakend-bdt/.env`:

```bash
APP_SECRET_KEY=tu_valor_generado_1
JWT_SECRET_KEY=tu_valor_generado_2
ENCRYPTION_KEY=tu_valor_generado_3
```

### Paso 4: Configurar cTrader (si vas a usar)

En https://openapi.ctrader.com/apps, creá una app con:
- **Redirect URI**: `http://localhost:8001/ctrader/callback`

### Paso 5: Iniciar

```bash
docker compose -f docker-compose.dev.yml up -d
```

### Paso 6: Correr migraciones

```bash
docker compose -f docker-compose.dev.yml exec api alembic upgrade head
```

### Paso 7: Abrir

| Servicio | URL |
|----------|-----|
| **Frontend** | http://localhost:3001 |
| **API Docs** | http://localhost:8001/docs |
| **API** | http://localhost:8001 |

---

## Variables de Entorno

### `Bakend-bdt/.env` (Backend)

| Variable | Requerida | Default | Descripción |
|----------|-----------|---------|-------------|
| `APP_SECRET_KEY` | ✅ | - | Secret key para la app (mín 32 chars) |
| `DATABASE_URL` | ✅ | - | URL de conexión a PostgreSQL |
| `DATABASE_URL_SYNC` | ✅ | - | URL síncrona para Alembic |
| `REDIS_URL` | ✅ | `redis://localhost:6379/0` | URL de Redis |
| `JWT_SECRET_KEY` | ✅ | - | Secret para firmar JWTs |
| `ENCRYPTION_KEY` | ✅ | - | Key AES-256 para cifrar credenciales (64 hex chars) |
| `STORAGE_TYPE` | ❌ | `local` | `local` o `gcs` |
| `CTRADER_REDIRECT_URI` | ❌ | `http://localhost:8001/ctrader/callback` | URI de callback OAuth2 |
| `CORS_ORIGINS` | ❌ | `http://localhost:3000,...` | Orígenes permitidos |

**Valores para desarrollo local (Docker):**

```bash
# Base de datos (usa los nombres de servicio de Docker)
DATABASE_URL=postgresql+asyncpg://brujula:brujula123@db:5432/brujula_db
DATABASE_URL_SYNC=postgresql://brujula:brujula123@db:5432/brujula_db

# Redis
REDIS_URL=redis://redis:6379/0
```

> ⚠️ **NUNCA** subas tu `.env` a Git. Ya está en `.gitignore`.

### `frontend-bdt/.env.local` (Frontend)

| Variable | Requerida | Default | Descripción |
|----------|-----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | ❌ | `http://localhost:8001` | URL del backend |
| `NEXT_PUBLIC_APP_NAME` | ❌ | `La Brújula del Trader` | Nombre de la app |
| `NEXT_PUBLIC_DEFAULT_LOCALE` | ❌ | `es` | Idioma por defecto |

### `.env.docker` (Docker - passwords de servicios)

| Variable | Descripción |
|----------|-------------|
| `POSTGRES_PASSWORD` | Password de PostgreSQL (solo para Docker) |

---

## Ejecutar el Proyecto

### Iniciar todo

```bash
docker compose -f docker-compose.dev.yml up -d
```

### Verificar que está corriendo

```bash
docker compose -f docker-compose.dev.yml ps
```

Deberías ver:

```
NAME            STATUS          PORTS
brujula_api     Up (healthy)    0.0.0.0:8001->8000/tcp
brujula_web     Up              0.0.0.0:3001->3000/tcp
brujula_db      Up (healthy)    0.0.0.0:5433->5432/tcp
brujula_redis   Up              0.0.0.0:6379->6379/tcp
```

### Crear usuario de prueba

```bash
docker compose -f docker-compose.dev.yml exec api python3 -c "
import bcrypt
from uuid import uuid4
import asyncio
from app.dependencies import get_db
from app.modules.auth.models import User
from sqlalchemy import insert

password = 'brujula123'
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

async def create():
    async for db in get_db():
        await db.execute(insert(User).values(
            id=str(uuid4()),
            email='harold2tg@gmail.com',
            password_hash=hashed,
            name='Harold Torres',
            plan='free',
            language='es',
            timezone='America/Bogota'
        ))
        await db.commit()
        print('Usuario creado: harold2tg@gmail.com / brujula123')

asyncio.run(create())
"
```

### Login

1. Andá a http://localhost:3001
2. Email: `harold2tg@gmail.com`
3. Password: `brujula123`

---

## Puertos y Servicios

| Servicio | Puerto Externo | Puerto Interno | Descripción |
|----------|----------------|----------------|-------------|
| Frontend (Next.js) | **3001** | 3000 | App web |
| API (FastAPI) | **8001** | 8000 | Backend + docs |
| PostgreSQL | **5433** | 5432 | Base de datos |
| Redis | **6379** | 6379 | Caché + colas |

> Los puertos externos están mapeados para evitar conflictos con otros proyectos.

---

## Cuenta de Prueba

Si no tenés cuenta de cTrader, podés probar con datos mock:

1. Andá a http://localhost:3001/es/uploads
2. Subí un CSV de ejemplo con estas columnas:
   ```csv
   ticket,symbol,side,volume,open_time,close_time,open_price,close_price,profit
   12345,XAUUSD,buy,0.1,2026-01-15 10:00:00,2026-01-15 14:00:00,2650.50,2665.30,148.00
   12346,XAUUSD,sell,0.05,2026-01-16 09:00:00,2026-01-16 11:00:00,2670.00,2662.50,37.50
   ```

---

## Comandos Útiles

```bash
# Ver logs del backend
docker compose -f docker-compose.dev.yml logs -f api

# Ver logs del frontend
docker compose -f docker-compose.dev.yml logs -f web

# Ver logs de todos
docker compose -f docker-compose.dev.yml logs -f

# Reiniciar solo la API
docker compose -f docker-compose.dev.yml restart api

# Ejecutar tests
docker compose -f docker-compose.dev.yml --profile test run --rm test

# Abrir consola de la DB
docker compose -f docker-compose.dev.yml exec db psql -U brujula -d brujula_db

# Detener todo
docker compose -f docker-compose.dev.yml down

# Detener y eliminar volúmenes (reset completo)
docker compose -f docker-compose.dev.yml down -v

# Reconstruir containers (si cambiaste Dockerfile)
docker compose -f docker-compose.dev.yml up -d --build
```

---

## Troubleshooting

### El container de la API no arranca

```bash
# Ver logs
docker compose -f docker-compose.dev.yml logs api

# Si dice "relation users does not exist"
docker compose -f docker-compose.dev.yml exec api alembic upgrade head
```

### Puerto 8001 ya en uso

```bash
# Ver qué lo usa
lsof -i :8001

# Matar el proceso
kill -9 <PID>
```

### cTrader "Not Found" al conectar

1. Verificá que creaste la app en https://openapi.ctrader.com/apps
2. El **Redirect URI** debe ser EXACTAMENTE: `http://localhost:8001/ctrader/callback`
3. Sin `/` al final
4. Con `http://` (no `https://`)

### Frontend no carga

```bash
# Ver logs
docker compose -f docker-compose.dev.yml logs web

# Reiniciar
docker compose -f docker-compose.dev.yml restart web
```

### "Missing authorization token" al hacer login

1. Verificá que la DB tiene el usuario:
   ```bash
   docker compose -f docker-compose.dev.yml exec db psql -U brujula -d brujula_db -c "SELECT email FROM users;"
   ```
2. Si no existe, crealo (ver "Crear usuario de prueba")

### Los secrets no están generados

```bash
# Generar los 3 secrets
echo "APP_SECRET_KEY=$(openssl rand -hex 32)"
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)"
echo "ENCRYPTION_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
```

Copiá cada valor a `Bakend-bdt/.env`.

---

## Estructura del Proyecto

```
brujuladeltrader/
├── Bakend-bdt/              # Backend FastAPI
│   ├── app/
│   │   ├── modules/
│   │   │   ├── auth/        # Login, JWT, registro
│   │   │   ├── ctrader/     # Conexión cTrader OAuth2
│   │   │   ├── ai_engine/   # Análisis con IA
│   │   │   ├── parser/      # Parsing de CSVs
│   │   │   ├── uploads/     # Subida de archivos
│   │   │   ├── analytics/   # Estadísticas
│   │   │   ├── alerts/      # Alertas de trading
│   │   │   └── reports/     # Reportes
│   │   ├── config.py        # Configuración central
│   │   └── main.py          # Entry point
│   ├── .env.example         # Template de variables
│   └── docker/Dockerfile.dev
├── frontend-bdt/            # Frontend Next.js
│   ├── app/                 # App Router (Next.js 15)
│   ├── components/          # Componentes React
│   ├── lib/                 # Utilities y hooks
│   ├── messages/            # Traducciones (ES/EN)
│   └── .env.local.example   # Template frontend
├── docker-compose.dev.yml   # Desarrollo local
├── docker-compose.prod.yml  # Producción
├── .env.prod.example        # Template producción
└── DEPLOYMENT.md            # Guía de deploy
```

---

## Licencia

Hecho con ❤️ para traders que quieren mejorar su estrategia.
