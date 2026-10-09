# La Brújula del Trader

> Plataforma profesional de análisis estadístico para traders de XAUUSD (Oro). Conectá tu cuenta real de cTrader, importá tus operaciones automáticamente, y mejorá tu estrategia con análisis IA.

---

## Tabla de Contenidos

1. [Qué es](#qué-es)
2. [Arquitectura](#arquitectura)
3. [Prerrequisitos](#prerrequisitos)
4. [Configuración de cTrader](#configuración-de-ctrader)
5. [Setup Rápido](#setup-rápido)
6. [Variables de Entorno](#variables-de-entorno)
7. [Cómo Usar](#cómo-usar)
8. [Puertos y Servicios](#puertos-y-servicios)
9. [Comandos Útiles](#comandos-útiles)
10. [Troubleshooting](#troubleshooting)
11. [Estructura del Proyecto](#estructura-del-proyecto)
12. [Licencia](#licencia)

---

## Qué es

```
┌─────────────────────────────────────────────────────────┐
│                    TU NAVEGADOR                         │
│                  http://localhost:3001                   │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │   Dashboard  │  │ Fuentede    │  │  Análisis IA  │  │
│  │  Métricas en │  │ Datos       │  │  Claude/GPT/  │  │
│  │  tiempo real │  │ cTrader     │  │  Gemini       │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│              Conexión cTrader (OAuth2)                  │
│         Sync automática de operaciones reales           │
│    (sin subir archivos manualmente)                     │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   API (FastAPI)                         │
│                  http://localhost:8001                   │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │   Auth   │  │Data      │  │ AI Engine│  │cTrader │  │
│  │  JWT +   │  │Sources   │  │ Análisis │  │ OAuth2 │  │
│  │  bcrypt  │  │Import    │  │ trades   │  │ Auto-  │  │
│  │          │  │automático│  │ Trades   │  │ Import │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘  │
├─────────────────────────────────────────────────────────┤
│              PostgreSQL (puerto 5433)                   │
│              Redis (puerto 6379)                        │
└─────────────────────────────────────────────────────────┘
```

### ¿Cómo funciona?

**Antes:** Subías un archivo CSV manual → Esperabas a que se procesara → Veías los datos  
**Ahora:** Hacés clic en **"Conectar con cTrader"** → Inicias sesión → Tus trades reales se importan solos ✅

---

## Arquitectura

| Módulo | Descripción |
|--------|-------------|
| **Auth** | Login JWT, registro, refresh tokens |
| **DataSources** | Modelo unificado para importar datos de múltiples brokers |
| **cTrader** | OAuth2 automático para importar trades de cuentas reales |
| **Analytics** | Estadísticas por hora, día, mes, sesión, rachas |
| **AI Engine** | Análisis con Claude, GPT-4, Gemini (opcional) |
| **Alerts** | Alertas configurables por tipo de trade |
| **Reports** | Exportación mensual/anual PDF/CSV |

### Flujo de importación de datos

```
Usuario hace clic en "Conectar con cTrader"
    ↓
Popup abre https://id.ctrader.com/my/settings/openapi/grantingaccess/
    ↓
Usuario inicia sesión con su cuenta de cTrader (FxPro, Pepperstone, etc.)
    ↓
Usuario selecciona qué cuentas autorizar (Live/Demo)
    ↓
Backend recibe code → intercambia por access_token + refresh_token
    ↓
Backend descubre cuentas con get_accounts() → detecta si es LIVE o DEMO
    ↓
Credenciales guardadas (cifradas AES-256-GCM en base de datos)
    ↓
Botón "Sincronizar" → importa todos los trades cerrados de esa cuenta
    ↓
Trades almacenados en tabla 'trades' con data_source_id como FK
    ↓
Dashboard muestra métricas calculadas desde trades importados
```

---

## Prerrequisitos

| Requisito | Versión Mínima | Cómo verificar |
|-----------|----------------|----------------|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | v24+ | `docker --version` |
| Git | Cualquiera | `git --version` |

> Solo necesitás Docker. No instalés Node.js ni Python en tu máquina.

---

## Configuración de cTrader

Necesitás una aplicación cTrader Open API registrada. Es **gratuita**.

### Paso 1: Crear app en cTrader Open API

1. Andá a: **https://openapi.ctrader.com/apps**
2. Logueate con tu cuenta de cTrader (o creala gratis)
3. Click en **"Create New App"**
4. Completá:
   - **App Name**: `La Brújula del Trader` (o lo que quieras)
   - **Redirect URI**: `http://localhost:8001/ctrader/callback` ⚠️ Exactamente así, sin `/` al final
   - **App Type**: `Web App`
5. Guardá el **Client ID** y **Client Secret**

### Paso 2: Configurar acceso a cuentas

En tu plataforma cTrader (Desktop/Web):
1. Andá a **Settings → API Trading**
2. Activá las cuentas que querés sincronizar
3. Anotá los números de cuenta (ej: `1320323`)

---

## Setup Rápido

### 1. Clonar repositorio

```bash
git clone https://github.com/harold2tg/brujuladeltrader.git
cd brujuladeltrader
```

### 2. Configurar entorno backend

```bash
cp Bakend-bdt/.env.example Bakend-bdt/.env
```

Editá `Bakend-bdt/.env` y completá estos campos:

```bash
APP_SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

CTRADER_CLIENT_ID=tu_client_id_aqui
CTRADER_CLIENT_SECRET=tu_client_secret_aqui
```

Generá los secretos con los comandos de arriba (son auto-generados por openssl/python).

### 3. Configurar frontend

El `.env.local` ya viene con la configuración correcta para Docker:

```bash
# Solo verificar que exista
ls frontend-bdt/.env.local || cp frontend-bdt/.env.local.example frontend-bdt/.env.local
```

### 4. Generar migraciones e iniciar

```bash
# Construir y levantar containers
docker compose -f docker-compose.dev.yml up -d

# Ejecutar migraciones de base de datos
docker compose -f docker-compose.dev.yml exec api alembic upgrade head
```

### 5. Abrir la app

| Servicio | URL |
|----------|-----|
| **Frontend** | http://localhost:3001 |
| **Docs API** | http://localhost:8001/docs |

### 6. Loguearse

Usá tu propio email/password registrado (o creá uno nuevo desde el frontend).

### 7. Conectar cTrader

1. Andá a **http://localhost:3001/ctrader**
2. Hacé clic en **"Conectar con cTrader"**
3. Se abre un popup con el login de cTrader
4. Iniciá sesión y autorizá las cuentas
5. ¡Listo! Ya podés hacer clic en **"Sincronizar"** para importar tus trades reales

---

## Variables de Entorno

### `Bakend-bdt/.env`

| Variable | Requerida | Default | Descripción |
|----------|-----------|---------|-------------|
| `APP_SECRET_KEY` | ✅ | - | Secret key de la app (mín 32 chars hex) |
| `DATABASE_URL` | ✅ | - | PostgreSQL async (usa nombre de servicio Docker) |
| `REDIS_URL` | ✅ | `redis://redis:6379/0` | URL de Redis |
| `JWT_SECRET_KEY` | ✅ | - | Secret para firmar JWTs |
| `ENCRYPTION_KEY` | ✅ | - | Key AES-256 para cifrar credenciales |
| `CTRADER_CLIENT_ID` | ✅* | - | Client ID de tu app cTrader *(ver sección anterior)* |
| `CTRADER_CLIENT_SECRET` | ✅* | - | Client Secret de tu app cTrader |
| `CTRADER_REDIRECT_URI` | ❌ | `http://localhost:8001/ctrader/callback` | URI callback OAuth2 |
| `CORS_ORIGINS` | ❌ | `http://localhost:3000,...` | Orígenes permitidos |

### Valores de desarrollo local (Docker):

```bash
DATABASE_URL=postgresql+asyncpg://brujula:brujula123@db:5432/brujula_db
REDIS_URL=redis://redis:6379/0
```

### `frontend-bdt/.env.local`

| Variable | Default | Descripción |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8001` | URL del backend |

---

## Cómo usar

### 1. Dashboard

Muestra tus métricas en tiempo real:
- Win Rate (% de trades ganadores)
- PnL Neto (ganancia/pérdida total)
- Ratio R:R (Risk/Reward)
- Gráficos de Equity Curve, PnL mensual, sesiones

### 2. Fuentes de Datos

Aquí gestionás tus conexiones con brokers:
- **Conectar**: Clik en el botón → popup de cTrader → autorización → sync automática
- **Sincronizar**: Trae todos los trades cerrados de tu cuenta
- **Ver**: Lista de fuentes conectadas con estado (idle/syncing/error)

### 3. Análisis

Detallada por dimensión:
- Por hora del día (london_open, ny_overlap, ny_session, off_hours)
- Por día de semana
- Por mes/año
- Distribución de resultados (histograma)
- Rachas (ganadoras/perdedoras consecutivas)
- Simulaciones (stop loss fijo, mejores horas)

### 4. Alertas

Configurá reglas automáticas:
- Pérdida máxima por trade ($)
- Racha perdedora
- Pérdida diaria límite

### 5. Reportes

Exportá tu rendimiento mensual/anual en PDF o CSV.

### 6. IA

Análisis automatizado con modelos de lenguaje (requiere API key de Anthropic/OpenAI/Gemini/Ollama).

---

## Puertos y Servicios

| Servicio | Puerto Externo | Interno | Descripción |
|----------|----------------|---------|-------------|
| Frontend (Next.js) | **3001** | 3000 | App web |
| API (FastAPI) | **8001** | 8000 | Backend + Swagger docs |
| PostgreSQL | **5433** | 5432 | Base de datos |
| Redis | **6379** | 6379 | Caché + colas |

Los puertos externos están mapeados para evitar conflictos con otros proyectos locales.

---

## Comandos Útiles

```bash
# Ver logs del backend
docker compose -f docker-compose.dev.yml logs -f api

# Ver logs del frontend
docker compose -f docker-compose.dev.yml logs -f web

# Reiniciar solo la API
docker compose -f docker-compose.dev.yml restart api

# Reconstruir con Dockerfile modificado
docker compose -f docker-compose.dev.yml up -d --build

# Abrir consola de la DB
docker compose -f docker-compose.dev.yml exec db psql -U brujula -d brujula_db

# Detener todo
docker compose -f docker-compose.dev.yml down

# Reset completo (elimina volúmenes)
docker compose -f docker-compose.dev.yml down -v
```

---

## Troubleshooting

### Error "Application authentication failed: Provided application does not contain provided URI"

1. Verificá que en https://openapi.ctrader.com/apps tu Redirect URI sea EXACTAMENTE: `http://localhost:8001/ctrader/callback`
2. Sin `/` al final
3. Con `http://` (no `https://`)
4. Guardaste los cambios en cTrader antes de intentar conectar

### Los gráficos aparecen vacíos después de conectar

1. Confirmá que hiciste clic en **"Sincronizar"** después de conectar
2. Si ya sincronizó y sigue vacío, verificá en consola del navegador (F12) si hay errores
3. Reintentá: desconecta → conecta nuevamente → sincroniza

### cTrader dice "No accounts found"

1. Verificá que activaste las cuentas en Settings → API Trading de tu plataforma cTrader
2. El access token debe tener permisos de lectura para esas cuentas

### "Missing authorization token" al cargar la página

Verificá que tengas un usuario creado en la base de datos:
```bash
docker compose -f docker-compose.dev.yml exec db psql -U brujula -d brujula_db -c "SELECT email FROM users;"
```

Si no hay usuarios, registrate desde http://localhost:3001/register

### Errores de CORS en frontend

Verificá que `CORS_ORIGINS` en `.env` incluya `http://localhost:3000` o `http://localhost:3001`.

### La API no arranca

```bash
# Ver logs específicos
docker compose -f docker-compose.dev.yml logs api

# Si dice "relation does not exist":
docker compose -f docker-compose.dev.yml exec api alembic upgrade head
```

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
│   │   │   ├── analytics/   # Estadísticas y cálculos
│   │   │   ├── alerts/      # Alertas de trading
│   │   │   ├── reports/     # Reportes exportables
│   │   │   └── data_sources/# DataSource + Trade models
│   │   ├── config.py        # Configuración central
│   │   └── main.py          # Entry point
│   ├── .env.example         # Template de variables
│   └── docker/Dockerfile.dev
├── frontend-bdt/            # Frontend Next.js 15
│   ├── app/                 # App Router
│   ├── components/          # Componentes React
│   ├── lib/                 # Utils, hooks, stores
│   └── messages/            # Traducciones (ES/EN)
├── scripts/                 # Scripts utilitarios
├── openspec/                # Documentos SDD de diseño
├── docker-compose.dev.yml   # Desarrollo local
├── docker-compose.prod.yml  # Producción
└── LICENSE
```

> **Nota:** Ya no existen los módulos `parser/` y `uploads/`. La importación de datos se hace exclusivamente vía cTrader OAuth2. Esto facilita agregar nuevos brokers (MetaTrader, Binance, etc.) en el futuro — cada uno será un nuevo provider que cree un `DataSource`.

---

## Licencia

Este proyecto está bajo la licencia [Apache License 2.0](LICENSE).

Podés usar, modificar y distribuir este software libremente, incluyendo uso comercial, siempre que:
- Mantengas el aviso de copyright
- Indiques los cambios que hiciste
- Incluyas la licencia completa

Ver [LICENSE](LICENSE) para detalles.
