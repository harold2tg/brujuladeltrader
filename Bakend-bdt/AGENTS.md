# AGENTS.md — brujula-api (Backend)

> **Leer antes de escribir cualquier línea de código.**
> Este documento es la fuente de verdad para el agente que construye el backend de La Brújula del Trader.
> El SRS completo está en `LaBrujulaDelTrader_SRS_v1.0.md`. Este documento lo complementa con reglas técnicas de implementación.

---

## Contexto del proyecto

**La Brújula del Trader** es una plataforma de análisis estadístico para traders manuales de XAUUSD (oro). El backend es el único componente que toca datos. Toda la lógica de negocio, cálculos estadísticos, integración con cTrader y llamadas a IA viven aquí. El frontend y la app móvil solo consumen esta API.

---

## Stack tecnológico

| Componente | Tecnología | Versión mínima |
| --- | --- | --- |
| Lenguaje | Python | 3.11+ |
| Framework | FastAPI | 0.110+ |
| ORM | SQLAlchemy (async) | 2.x |
| Migraciones | Alembic | última estable |
| Base de datos | PostgreSQL | 15 |
| Caché | Redis | 7 |
| Auth | python-jose + bcrypt | última estable |
| Procesamiento archivos | pandas + openpyxl | última estable |
| Tareas async | Celery + Redis broker | última estable |
| IA | Anthropic Python SDK | última estable |
| Gestor de paquetes | Poetry | última estable |
| Testing | pytest + pytest-asyncio | última estable |
| Containerización | Docker + Docker Compose | última estable |

---

## Estructura de carpetas

```
brujula-api/
├── app/
│   ├── main.py                  # Entrada FastAPI, registro de routers, CORS, middleware
│   ├── config.py                # Settings con pydantic-settings, lee desde .env
│   ├── database.py              # Engine async, sesión, Base declarativa
│   ├── worker.py                # Configuración Celery
│   ├── dependencies.py          # get_db, get_current_user, get_current_active_user
│   │
│   ├── modules/
│   │   ├── auth/
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── schemas.py
│   │   │   └── models.py
│   │   ├── ctrader/
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── client.py        # Wrapper de cTrader Open API
│   │   │   └── schemas.py
│   │   ├── uploads/
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── schemas.py
│   │   │   └── models.py
│   │   ├── parser/
│   │   │   ├── service.py       # Orquestador del parseo
│   │   │   ├── normalizer.py    # Limpieza y normalización de columnas
│   │   │   ├── validators.py    # Validación de columnas requeridas
│   │   │   └── tasks.py         # Tareas Celery del parser
│   │   ├── analytics/
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── metrics.py       # Cálculo de todas las métricas estadísticas
│   │   │   ├── sessions.py      # Clasificación de sesiones de mercado
│   │   │   ├── schemas.py
│   │   │   └── models.py
│   │   ├── reports/
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   └── schemas.py
│   │   ├── ai_engine/
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── prompts.py       # Templates de prompts para Claude
│   │   │   └── tasks.py         # Tareas Celery del AI engine
│   │   ├── alerts/
│   │   │   ├── router.py
│   │   │   ├── service.py
│   │   │   ├── rules.py         # Evaluación de reglas de alerta
│   │   │   ├── schemas.py
│   │   │   └── models.py
│   │   └── users/
│   │       ├── router.py
│   │       ├── service.py
│   │       ├── schemas.py
│   │       └── models.py
│   │
│   └── shared/
│       ├── exceptions.py        # HTTPException personalizadas con códigos de error
│       ├── pagination.py        # Esquema de paginación estándar
│       ├── responses.py         # Wrapper de respuesta estándar { data, message, success }
│       └── utils.py             # Utilidades compartidas
│
├── alembic/
│   ├── env.py
│   └── versions/
├── tests/
│   ├── conftest.py              # Fixtures globales, DB de test
│   └── modules/
│       ├── test_auth.py
│       ├── test_ctrader.py
│       ├── test_uploads.py
│       ├── test_parser.py
│       ├── test_analytics.py
│       └── test_alerts.py
├── docker/
│   ├── Dockerfile
│   └── Dockerfile.dev
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
├── pyproject.toml
└── AGENTS.md
```

---

## Convenciones de código — OBLIGATORIAS

### Respuestas de la API
Todos los endpoints retornan siempre esta estructura:

```python
# Éxito
{ "success": True, "data": { ... }, "message": "Descripción opcional" }

# Error HTTP
{ "detail": "Mensaje legible para el usuario", "code": "ERROR_CODE_SNAKE_CASE" }
```

### Async en todo
- Todos los endpoints son `async def`. Sin excepción.
- Todos los servicios que acceden a la DB son `async def`.
- Nunca usar funciones síncronas bloqueantes dentro de rutas async. Si una librería es síncrona, usar `asyncio.run_in_executor`.

### Separación de responsabilidades
- Los **routers** solo reciben el request, llaman al servicio y retornan la respuesta. Sin lógica de negocio.
- Los **servicios** contienen toda la lógica de negocio. No acceden directamente a la DB — usan queries SQLAlchemy dentro del mismo servicio.
- Los **modelos** son solo definiciones SQLAlchemy. Sin lógica.
- Los **schemas** son solo Pydantic. Sin lógica.

### Imports
- Usar imports absolutos desde `app.`. Nunca imports relativos con `..`.

### Manejo de errores
- Nunca usar `except Exception` sin relanzar o loggear.
- Los errores de negocio se expresan como `HTTPException` con `status_code` y `detail` descriptivo.
- Los errores inesperados se loggean y retornan `500` genérico al cliente.

---

## Módulo `auth`

### Reglas que no se pueden romper
- Las contraseñas NUNCA se almacenan en texto plano. Siempre `bcrypt` con factor de costo ≥12.
- Los tokens JWT expiran en 24 horas. Los refresh tokens expiran en 30 días.
- Al hacer logout, el `jti` del token se guarda en Redis con TTL igual al tiempo restante del token. Todo request valida que el `jti` no esté en la lista negra.
- Los errores de login siempre retornan `401` con mensaje genérico. Nunca indicar si el email existe o no.
- El campo `email` es único. Validar antes de insertar, retornar `409 Conflict` si ya existe.

### Endpoints

```
POST   /auth/register      Body: { email, password, name }
                           Response: { user, access_token, refresh_token }

POST   /auth/login         Body: { email, password }
                           Response: { access_token, refresh_token }

POST   /auth/refresh       Body: { refresh_token }
                           Response: { access_token }

POST   /auth/logout        Header: Authorization Bearer
                           Response: 204 No Content

GET    /auth/me            Header: Authorization Bearer
                           Response: { user }
```

### Modelo `users`

```sql
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
email         VARCHAR(255) UNIQUE NOT NULL
password_hash VARCHAR(255) NOT NULL
name          VARCHAR(100) NOT NULL
plan          VARCHAR(20)  NOT NULL DEFAULT 'free'   -- free | pro | admin
language      VARCHAR(10)  NOT NULL DEFAULT 'es'     -- es | en
timezone      VARCHAR(50)  NOT NULL DEFAULT 'America/Bogota'
created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
is_active     BOOLEAN      NOT NULL DEFAULT TRUE
```

---

## Módulo `ctrader`

### Contexto técnico
cTrader Open API usa protocolo **Protobuf sobre TCP**, no REST. El cliente Python debe conectarse al endpoint `live.ctraderapi.com:5035` (producción) o `demo.ctraderapi.com:5035` (demo). La librería recomendada es `ctrader-open-api` (Python SDK oficial de Spotware).

Para obtener el historial de deals se usa el mensaje `ProtoOADealListReq` con `fromTimestamp` y `toTimestamp` en milisegundos UTC.

### Reglas que no se pueden romper
- Las credenciales (Client ID, Client Secret, Access Token, Account ID) se cifran con **AES-256-GCM** antes de guardar en la DB. La clave de cifrado viene de `ENCRYPTION_KEY` en `.env`. Nunca se retornan en texto plano después de guardadas.
- El campo `access_token` en la respuesta de cualquier endpoint siempre se enmascara: `eyJhbGci...` (primeros 10 chars + `...`).
- Para consultas anuales, dividir en bloques de máximo 30 días. cTrader limita el historial a rangos específicos.
- Implementar rate limiting: máximo 5 requests por segundo a cTrader para datos históricos. Usar `asyncio.sleep` entre bloques.
- Máximo 3 reintentos con backoff exponencial (1s, 2s, 4s) si cTrader no responde.
- Si la conexión falla después de los reintentos, retornar `{ "success": false, "code": "CTRADER_UNAVAILABLE", "fallback": true }` para que el frontend ofrezca la carga manual.

### Endpoints

```
POST   /ctrader/credentials    Body: { client_id, client_secret, access_token, account_id }
                               Response: { connected: true, account_name, broker }

GET    /ctrader/test           Response: { connected: bool, latency_ms, error? }

POST   /ctrader/sync           Body: { mode: "day"|"month"|"year", date: "YYYY-MM-DD" }
                               Response: { job_id, status: "processing", estimated_trades }

GET    /ctrader/sync/{job_id}  Response: { status, progress_pct, trades_imported, error? }

DELETE /ctrader/credentials    Response: 204
```

### Modelo `ctrader_credentials`

```sql
id             UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
client_id_enc  TEXT NOT NULL        -- cifrado AES-256-GCM
client_secret_enc TEXT NOT NULL
access_token_enc  TEXT NOT NULL
account_id_enc TEXT NOT NULL
account_name   VARCHAR(100)         -- nombre de la cuenta (no sensible)
broker_name    VARCHAR(100)         -- nombre del broker (no sensible)
is_demo        BOOLEAN NOT NULL DEFAULT FALSE
created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

---

## Módulo `uploads`

### Reglas que no se pueden romper
- Solo se aceptan `.csv` y `.xlsx`. Rechazar cualquier otra extensión con `400`.
- Tamaño máximo: 10 MB. Validar antes de guardar en disco.
- El archivo se guarda con nombre `{uuid4}.{ext}` — nunca con el nombre original del usuario.
- El archivo original NUNCA se modifica. Es inmutable una vez guardado.
- El procesamiento es asíncrono (Celery). El endpoint retorna inmediatamente con `{ upload_id, status: "pending" }`.
- Plan `free`: máximo 5 uploads activos. Validar ANTES de aceptar el archivo. Retornar `403` si se supera el límite.
- El proceso de parsing es idempotente: si se dispara dos veces sobre el mismo `upload_id`, no duplica trades.

### Endpoints

```
POST   /uploads/              Multipart: { file, period_label? }
                              Response: { upload_id, status: "pending" }

GET    /uploads/              Response: lista paginada de uploads del usuario

GET    /uploads/{id}          Response: detalle + status + métricas básicas si ready

GET    /uploads/{id}/status   Response: { status, progress_pct, error_message? }

DELETE /uploads/{id}          Response: 204  (elimina upload + trades asociados)
```

### Modelo `uploads`

```sql
id             UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id        UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
original_name  VARCHAR(255) NOT NULL
stored_name    VARCHAR(255) NOT NULL      -- uuid.ext
stored_path    VARCHAR(500) NOT NULL
file_size_kb   INTEGER NOT NULL
status         VARCHAR(20) NOT NULL DEFAULT 'pending'
               -- pending | processing | ready | error
error_message  TEXT
source         VARCHAR(20) NOT NULL DEFAULT 'file'  -- file | ctrader
total_trades   INTEGER
date_from      DATE
date_to        DATE
period_label   VARCHAR(50)               -- ej: "Mayo 2025", "2025"
created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
processed_at   TIMESTAMPTZ
```

---

## Módulo `parser`

### Reglas que no se pueden romper
- Detectar columnas por nombre, no por posición. Los archivos de cTrader pueden tener columnas en diferente orden.
- Columnas requeridas: `Símbolo`, `Dirección de apertura`, `Hora de cierre (UTC-5)`, `Precio de entrada`, `Precio de cierre`, `$ neto`, `Saldo $`.
- Si falta alguna columna requerida → marcar upload como `error` con mensaje que lista las columnas faltantes. No insertar datos parciales.
- La columna `Saldo $` puede contener `\xa0` (espacio no-breaking) como separador de miles. Limpiar con `str.replace('\xa0', '').replace(' ', '')` antes de convertir a float.
- La columna `Cantidad de Cierre` puede tener formato `"0.02 Lotes"`. Extraer solo el número con regex `[\d.]+`.
- Fechas en formato `DD/MM/YYYY HH:MM:SS.fff`. Parsear con `pd.to_datetime(col, format="%d/%m/%Y %H:%M:%S.%f")`.
- Trades con `$ neto == 0` se insertan normalmente. No son errores.
- Al insertar, calcular y guardar campos derivados: `hour_of_day`, `day_of_week`, `week_of_year`, `month`, `year`, `session`, `is_winner`.

### Clasificación de sesiones (UTC-5, hora Colombia)

```python
def classify_session(hour: int) -> str:
    if 7 <= hour < 9:
        return "london_open"    # 07h-09h
    elif 9 <= hour < 12:
        return "ny_overlap"     # 09h-12h — overlap Londres/NY
    elif 12 <= hour < 17:
        return "ny_session"     # 12h-17h
    else:
        return "off_hours"
```

### Modelo `trades`

```sql
id               UUID PRIMARY KEY DEFAULT gen_random_uuid()
upload_id        UUID NOT NULL REFERENCES uploads(id) ON DELETE CASCADE
user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
symbol           VARCHAR(20) NOT NULL
direction        VARCHAR(10) NOT NULL        -- Buy | Sell
closed_at        TIMESTAMPTZ NOT NULL
entry_price      NUMERIC(12,5) NOT NULL
close_price      NUMERIC(12,5) NOT NULL
lot_size         NUMERIC(8,4)
net_pnl          NUMERIC(10,2) NOT NULL
balance          NUMERIC(10,2)
-- Campos derivados (calculados al parsear)
hour_of_day      SMALLINT NOT NULL           -- 0-23
day_of_week      SMALLINT NOT NULL           -- 0=lunes, 6=domingo
week_of_year     SMALLINT NOT NULL
month            SMALLINT NOT NULL
year             SMALLINT NOT NULL
session          VARCHAR(20) NOT NULL        -- london_open | ny_overlap | ny_session | off_hours
is_winner        BOOLEAN NOT NULL            -- net_pnl > 0
trade_number     INTEGER NOT NULL            -- secuencial dentro del upload
```

---

## Módulo `analytics`

### Reglas que no se pueden romper
- Todos los cálculos en Python/pandas. No usar SQL para cálculos estadísticos complejos.
- Resultados cacheados en Redis. Clave: `analytics:{upload_id}:{endpoint}`. TTL: 1 hora.
- Si el cache existe, retornarlo directamente sin recalcular.
- `win_rate` = `ganadores / total`. Los trades con `net_pnl == 0` cuentan como perdedores.
- `rr_ratio` = `avg_win / abs(avg_loss)`. Si no hay pérdidas, retornar `null`.
- `breakeven_winrate` = `1 / (1 + rr_ratio)`.
- `profit_factor` = `gross_profit / abs(gross_loss)`. Si no hay pérdidas, retornar `null`.
- Métricas por hora: solo incluir horas con **≥5 trades**.
- Métricas por día de semana: solo incluir días con **≥10 trades**.

### Métricas que calcula `metrics.py`

```python
# Globales
total_trades: int
winning_trades: int
losing_trades: int
win_rate: float                  # 0.0 a 1.0
net_pnl: float
gross_profit: float
gross_loss: float                # negativo
avg_win: float
avg_loss: float                  # negativo
rr_ratio: float | None
breakeven_winrate: float | None
best_trade: float
worst_trade: float
profit_factor: float | None
initial_balance: float
final_balance: float
total_return_pct: float
max_win_streak: int
max_loss_streak: int
current_streak: int              # positivo=ganadora, negativo=perdedora
loss_streak_3_plus_count: int    # cuántas veces hubo racha perdedora ≥3

# Por dimensión (lista ordenada)
by_hour: List[HourMetrics]
by_day_of_week: List[DayMetrics]
by_month: List[MonthMetrics]
by_direction: DirectionMetrics   # { buy: {...}, sell: {...} }
by_session: List[SessionMetrics]

# Distribución por rangos
distribution: List[BucketMetrics]
# Rangos fijos: <-20, -20/-10, -10/-5, -5/0, 0/5, 5/10, >10

# Simulaciones
sim_max_loss_5_pnl: float        # PnL si toda pérdida > $5 se hubiera cortado en $5
sim_best_3_hours_pnl: float      # PnL operando solo en las 3 mejores horas
```

### Endpoints

```
GET /analytics/{upload_id}               → métricas globales + todas las dimensiones
GET /analytics/{upload_id}/summary       → solo métricas globales
GET /analytics/{upload_id}/by-hour       → desglose por hora
GET /analytics/{upload_id}/by-day        → desglose por día de semana
GET /analytics/{upload_id}/by-month      → desglose por mes
GET /analytics/{upload_id}/by-session    → desglose por sesión de mercado
GET /analytics/{upload_id}/streaks       → rachas
GET /analytics/{upload_id}/distribution  → distribución de resultados
GET /analytics/{upload_id}/simulate      → simulaciones
GET /analytics/compare?ids=id1,id2       → comparar dos uploads (mismo usuario)
```

---

## Módulo `ai_engine`

### Arquitectura: AIProvider abstraction

El sistema usa una **interfaz abstracta `AIProvider`** para que el proveedor de IA sea intercambiable sin cambiar la lógica de negocio. Nunca se llama a un SDK de IA directamente desde la lógica de negocio.

**Cada usuario configura su propio proveedor de IA** desde un formulario en su perfil. Las API keys se cifran con AES-256-GCM (igual que las credenciales de cTrader) y se almacenan en la tabla `ai_credentials`.

```python
# shared/ai_provider.py
from abc import ABC, abstractmethod
from typing import Optional

class AIProvider(ABC):
    """Interfaz abstracta para proveedores de IA."""

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1500,
        temperature: float = 0.7
    ) -> str:
        """Genera una respuesta de IA. Retorna el texto generado."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Verifica si el proveedor está disponible."""
        pass
```

### Proveedores soportados

| Provider | Modelo por defecto | Campo en formulario |
|----------|-------------------|---------------------|
| `claude` | `claude-sonnet-4-20250514` | API Key (Anthropic) |
| `openai` | `gpt-4o` | API Key (OpenAI) |
| `gemini` | `gemini-2.0-flash` | API Key (Google) |
| `ollama` | `llama3` (local) | URL del servidor Ollama |

### Modelo `ai_credentials`

```sql
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
provider        VARCHAR(20) NOT NULL        -- claude | openai | gemini | ollama
api_key_enc     TEXT                        -- cifrado AES-256-GCM (null para ollama)
base_url        VARCHAR(500)                -- solo para ollama (URL local)
model_override  VARCHAR(100)                -- modelo personalizado (opcional)
is_active       BOOLEAN NOT NULL DEFAULT TRUE
created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

### Reglas que no se pueden romper
- **Siempre usar la interfaz `AIProvider`**. Nunca importar `anthropic`, `openai`, ni `google.generativeai` directamente en services o routers.
- **Cada usuario tiene su propia configuración de IA** en la tabla `ai_credentials`.
- Las API keys se cifran con **AES-256-GCM** antes de guardar. La clave de cifrado viene de `ENCRYPTION_KEY` en `.env`. Nunca se retornan en texto plano después de guardadas.
- El campo `api_key` en la respuesta siempre se enmascara: `sk-ant-...xxxx` (primeros 10 chars + `...`).
- Si el usuario no tiene credenciales de IA configuradas, el sistema usa el fallback determinista (análisis sin IA).
- `max_tokens`: 1500 para análisis completo, 500 para resumen rápido.
- El contexto del trader se incluye en el `system` prompt de CADA llamada. Nunca omitirlo.
- Las llamadas a IA son asíncronas vía Celery. El endpoint retorna `{ job_id, status: "processing" }` inmediatamente.
- Cache en Redis. Clave: `ai:{upload_id}:{analysis_type}:{language}`. TTL: 24 horas.
- Plan `free`: máximo 10 llamadas a IA por usuario por día. Contador en Redis con TTL hasta medianoche UTC-5.
- Si el proveedor falla o el usuario superó el límite, retornar el análisis determinista del módulo `reports` como fallback. Nunca mostrar el error de la API al usuario final.
- Nunca enviar datos de múltiples usuarios en el mismo prompt.
- Cada provider implementa retry con backoff exponencial (máximo 3 intentos).

### Endpoints de credenciales IA

```
POST   /ai/credentials       Body: { provider, api_key, base_url?, model_override? }
                             Response: { connected: true, provider, model }

GET    /ai/credentials       Response: lista de credenciales del usuario (keys enmascaradas)

PUT    /ai/credentials/{id}  Body: { api_key?, model_override?, is_active? }
                             Response: credencial actualizada

DELETE /ai/credentials/{id}  Response: 204

POST   /ai/credentials/test  Body: { provider, api_key, base_url? }
                             Response: { connected: bool, latency_ms, model, error? }
```

### Estructura de archivos del módulo

```
modules/ai_engine/
├── __init__.py
├── router.py
├── service.py
├── prompts.py          # Templates de prompts (independientes del provider)
├── tasks.py            # Tareas Celery
├── models.py           # Modelo ai_credentials
├── schemas.py          # Pydantic schemas
└── providers/          # Implementaciones concretas
    ├── __init__.py
    ├── base.py         # AIProvider (interfaz abstracta)
    ├── claude.py       # Anthropic SDK
    ├── openai.py       # OpenAI SDK
    ├── gemini.py       # Google Generative AI SDK
    └── ollama.py       # Ollama HTTP client
```

### System prompt base (`prompts.py`)

```python
SYSTEM_PROMPT = {
    "es": """Eres un analista cuantitativo especializado en trading de XAUUSD (oro).
Analizas el historial de operaciones de un trader con estas características:
- Estilo: scalping intraday manual
- Gráficos utilizados: M1, M5 y M10
- Zona horaria: Colombia (UTC-5)
- Experiencia: trader en desarrollo buscando mejorar consistencia

Responde siempre en español colombiano. Sé directo y usa datos numéricos concretos.
Nunca inventes datos que no estén en las métricas proporcionadas.
Tus recomendaciones deben ser accionables, específicas y ordenadas por impacto.""",

    "en": """You are a quantitative analyst specialized in XAUUSD (gold) trading.
You analyze the trade history of a trader with these characteristics:
- Style: manual intraday scalping
- Charts: M1, M5, and M10
- Timezone: Colombia (UTC-5)
- Experience: developing trader seeking to improve consistency

Always respond in English. Be direct and use concrete numerical data.
Never fabricate data not present in the provided metrics.
Your recommendations must be actionable, specific, and ordered by impact."""
}
```

### Tipos de análisis disponibles

```python
ANALYSIS_TYPES = {
    "full_diagnosis":    "Diagnóstico completo con todas las métricas",
    "monthly_review":    "Revisión de un mes específico",
    "improvement_plan":  "Plan de mejora basado en patrones detectados",
    "quick_summary":     "Resumen ejecutivo en 3 puntos clave",
    "session_analysis":  "Análisis de las mejores y peores horas y sesiones"
}
```

### Endpoints

```
POST /ai/{upload_id}/analyze     Body: { analysis_type, language: "es"|"en" }
                                 Response: { job_id, status: "processing" }

GET  /ai/jobs/{job_id}           Response: { status, result?, error?, fallback_used: bool }

GET  /ai/{upload_id}/insights    Response: últimos insights cacheados del upload
```

---

## Módulo `alerts`

### Reglas que no se pueden romper
- Las alertas se evalúan cada vez que un upload cambia a estado `ready`.
- Una misma alerta no puede dispararse más de una vez por hora por usuario. Control en Redis.
- Plan `free`: máximo 3 reglas activas. Plan `pro`: ilimitado.
- Al dispararse una alerta, guardar registro en `alert_history` con timestamp y valor que la activó.

### Tipos de reglas

```python
ALERT_TYPES = {
    "max_loss_per_trade":  "Pérdida máxima por operación ($)",
    "loss_streak":         "Racha perdedora consecutiva (n ops)",
    "daily_loss_limit":    "Pérdida máxima acumulada en el día ($)",
    "win_rate_drop":       "Win rate cae por debajo de X% en el upload",
    "rr_below":            "Ratio R:R cae por debajo de X en el upload"
}
```

### Endpoints

```
GET    /alerts/rules              → reglas activas del usuario
POST   /alerts/rules              → { alert_type, threshold, is_active }
PUT    /alerts/rules/{id}         → actualizar threshold o is_active
DELETE /alerts/rules/{id}         → eliminar regla
GET    /alerts/history            → historial de alertas disparadas (paginado)
```

### Modelos

```sql
-- alert_rules
id           UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
alert_type   VARCHAR(50) NOT NULL
threshold    NUMERIC(10,2) NOT NULL
is_active    BOOLEAN NOT NULL DEFAULT TRUE
created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()

-- alert_history
id           UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE
rule_id      UUID NOT NULL REFERENCES alert_rules(id) ON DELETE CASCADE
upload_id    UUID REFERENCES uploads(id)
triggered_value NUMERIC(10,2)
triggered_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

---

## Módulo `users`

### Endpoints

```
GET    /users/profile          → perfil completo (sin password_hash)
PUT    /users/profile          → { name?, language?, timezone? }
PUT    /users/password         → { current_password, new_password }
GET    /users/stats            → métricas agregadas de todos sus uploads
DELETE /users/account          → eliminar cuenta y todos sus datos (soft delete primero)
```

---

## Variables de entorno (`.env.example`)

```env
# App
APP_ENV=development                    # development | production
APP_SECRET_KEY=min_32_chars_secret_here
DEBUG=true

# Base de datos
DATABASE_URL=postgresql+asyncpg://brujula:brujula123@db:5432/brujula_db
DATABASE_URL_SYNC=postgresql://brujula:brujula123@db:5432/brujula_db

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
JWT_SECRET_KEY=min_32_chars_jwt_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30

# Cifrado de credenciales (cTrader + AI providers)
# Generar con: python -c "import secrets; print(secrets.token_hex(32))"
ENCRYPTION_KEY=32_bytes_hex_key_here

# Almacenamiento
STORAGE_TYPE=local                     # local | s3
STORAGE_LOCAL_PATH=/app/uploads
AWS_BUCKET_NAME=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1

# Límites por plan
FREE_PLAN_MAX_UPLOADS=5
FREE_PLAN_MAX_AI_CALLS_PER_DAY=10
FREE_PLAN_MAX_ALERT_RULES=3
MAX_UPLOAD_SIZE_MB=10

# cTrader
CTRADER_HOST_LIVE=live.ctraderapi.com
CTRADER_HOST_DEMO=demo.ctraderapi.com
CTRADER_PORT=5035

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

> **Nota**: Las API keys de proveedores de IA (Anthropic, OpenAI, Gemini) y las credenciales de cTrader **NO van en `.env`**. Se almacenan cifradas en la base de datos, una por usuario, configuradas desde formularios en la interfaz.

---

## Orden de implementación obligatorio

Implementar en este orden exacto. No avanzar al siguiente módulo sin que el anterior tenga tests pasando.

```
1. auth          → sin autenticación nada funciona
2. users         → perfil básico, necesario para auth
3. uploads       → recepción de archivos
4. parser        → sin datos no hay análisis
5. analytics     → corazón del producto
6. ctrader       → integración con cTrader (fuente principal de datos)
7. reports       → empaqueta analytics para el cliente
8. ai_engine     → valor agregado sobre analytics
9. alerts        → feature de retención de usuarios
```

---

## Testing

- Cada módulo tiene su archivo de tests en `tests/modules/test_{modulo}.py`.
- Los tests usan una base de datos PostgreSQL de test separada (variable `TEST_DATABASE_URL`).
- Fixtures globales en `conftest.py`: usuario de prueba, upload de prueba con 50 trades sintéticos.
- Los tests de `ctrader` usan mocks del cliente cTrader. No hacen llamadas reales a la API.
- Los tests de `ai_engine` usan mocks del Anthropic SDK. No hacen llamadas reales a Claude.
- Cobertura mínima requerida: 80% en módulos `auth`, `analytics` y `parser`.
