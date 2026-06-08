# AGENTS.md — brujula-infra (Docker e Infraestructura)

> **Leer antes de escribir cualquier línea de código.**
> Este documento es la fuente de verdad para el agente que configura la infraestructura de La Brújula del Trader.
> El SRS completo está en `LaBrujulaDelTrader_SRS_v1.0.md`. Este documento lo complementa con reglas técnicas de despliegue.

---

## Contexto

La Brújula del Trader se despliega en un VPS con Docker y Nginx como reverse proxy. El entorno local de desarrollo usa Docker Compose. El CI/CD corre en GitHub Actions. La infraestructura debe ser simple, reproducible y fácil de mantener por una persona.

---

## Repositorios y su relación

```
brujula-api/        → imagen Docker: brujula-api
brujula-web/        → imagen Docker: brujula-web
brujula-infra/      → docker-compose.yml de producción + configs Nginx + scripts
```

La app móvil (`brujula-mobile`) no se containeriza — se compila y distribuye vía App Store y Google Play.

---

## Estructura de `brujula-infra/`

```
brujula-infra/
├── docker-compose.yml           # Producción
├── docker-compose.dev.yml       # Desarrollo local (override)
├── nginx/
│   ├── nginx.conf               # Config global Nginx
│   ├── api.conf                 # Reverse proxy para brujula-api
│   └── web.conf                 # Reverse proxy para brujula-web
├── scripts/
│   ├── deploy.sh                # Script de despliegue en VPS
│   ├── backup_db.sh             # Backup automático de PostgreSQL
│   └── restore_db.sh            # Restauración de backup
├── .env.example                 # Variables de entorno de producción
└── AGENTS.md
```

---

## Servicios del sistema

| Servicio | Imagen | Puerto interno | Descripción |
| --- | --- | --- | --- |
| `api` | `brujula-api:latest` | 8000 | FastAPI backend |
| `worker` | `brujula-api:latest` | — | Celery worker (misma imagen, distinto comando) |
| `web` | `brujula-web:latest` | 3000 | Next.js frontend |
| `db` | `postgres:15-alpine` | 5432 | Base de datos PostgreSQL |
| `redis` | `redis:7-alpine` | 6379 | Caché y broker de Celery |
| `nginx` | `nginx:alpine` | 80, 443 | Reverse proxy y SSL |

**Regla:** Solo `nginx` expone puertos al exterior (80 y 443). Todos los demás servicios son internos a la red Docker.

---

## Docker Compose — Desarrollo local

### `docker-compose.dev.yml`

```yaml
version: "3.9"

services:
  api:
    build:
      context: ../brujula-api
      dockerfile: docker/Dockerfile.dev
    container_name: brujula_api_dev
    ports:
      - "8000:8000"
    volumes:
      - ../brujula-api/app:/app/app    # hot reload
      - uploads_data:/app/uploads
    env_file:
      - ../brujula-api/.env
    environment:
      - APP_ENV=development
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    networks:
      - brujula_net

  worker:
    build:
      context: ../brujula-api
      dockerfile: docker/Dockerfile.dev
    container_name: brujula_worker_dev
    volumes:
      - ../brujula-api/app:/app/app
      - uploads_data:/app/uploads
    env_file:
      - ../brujula-api/.env
    environment:
      - APP_ENV=development
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    command: celery -A app.worker worker --loglevel=info --concurrency=2
    networks:
      - brujula_net

  web:
    build:
      context: ../brujula-web
      dockerfile: Dockerfile.dev
    container_name: brujula_web_dev
    ports:
      - "3000:3000"
    volumes:
      - ../brujula-web:/app
      - /app/node_modules
      - /app/.next
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_DEFAULT_LOCALE=es
    depends_on:
      - api
    networks:
      - brujula_net

  db:
    image: postgres:15-alpine
    container_name: brujula_db_dev
    ports:
      - "5432:5432"           # expuesto solo en dev para conectar con cliente SQL
    environment:
      POSTGRES_DB: brujula_db
      POSTGRES_USER: brujula
      POSTGRES_PASSWORD: brujula123
    volumes:
      - postgres_data_dev:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U brujula -d brujula_db"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - brujula_net

  redis:
    image: redis:7-alpine
    container_name: brujula_redis_dev
    ports:
      - "6379:6379"           # expuesto solo en dev para inspección
    volumes:
      - redis_data_dev:/data
    networks:
      - brujula_net

networks:
  brujula_net:
    driver: bridge

volumes:
  postgres_data_dev:
  redis_data_dev:
  uploads_data:
```

### Comandos de desarrollo

```bash
# Iniciar todo
docker compose -f docker-compose.dev.yml up -d

# Ver logs de la API
docker compose -f docker-compose.dev.yml logs -f api

# Ejecutar migraciones
docker compose -f docker-compose.dev.yml exec api alembic upgrade head

# Abrir shell en la DB
docker compose -f docker-compose.dev.yml exec db psql -U brujula -d brujula_db

# Detener todo
docker compose -f docker-compose.dev.yml down

# Detener y eliminar volúmenes (reset total)
docker compose -f docker-compose.dev.yml down -v
```

---

## Docker Compose — Producción

### `docker-compose.yml`

```yaml
version: "3.9"

services:
  api:
    image: ghcr.io/${GITHUB_USER}/brujula-api:${API_VERSION:-latest}
    container_name: brujula_api
    restart: unless-stopped
    volumes:
      - uploads_data:/app/uploads
    env_file:
      - .env
    environment:
      - APP_ENV=production
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - brujula_net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  worker:
    image: ghcr.io/${GITHUB_USER}/brujula-api:${API_VERSION:-latest}
    container_name: brujula_worker
    restart: unless-stopped
    volumes:
      - uploads_data:/app/uploads
    env_file:
      - .env
    environment:
      - APP_ENV=production
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    command: celery -A app.worker worker --loglevel=warning --concurrency=4
    networks:
      - brujula_net

  web:
    image: ghcr.io/${GITHUB_USER}/brujula-web:${WEB_VERSION:-latest}
    container_name: brujula_web
    restart: unless-stopped
    env_file:
      - .env
    networks:
      - brujula_net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:15-alpine
    container_name: brujula_db
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - brujula_net
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: brujula_redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD} --save 60 1
    volumes:
      - redis_data:/data
    networks:
      - brujula_net

  nginx:
    image: nginx:alpine
    container_name: brujula_nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/api.conf:/etc/nginx/conf.d/api.conf:ro
      - ./nginx/web.conf:/etc/nginx/conf.d/web.conf:ro
      - certbot_data:/etc/letsencrypt:ro
      - certbot_www:/var/www/certbot:ro
    depends_on:
      - api
      - web
    networks:
      - brujula_net

networks:
  brujula_net:
    driver: bridge

volumes:
  postgres_data:
  redis_data:
  uploads_data:
  certbot_data:
  certbot_www:
```

---

## Dockerfiles

### `brujula-api/docker/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Poetry
RUN pip install poetry==1.8.0
RUN poetry config virtualenvs.create false

# Dependencias Python
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev --no-interaction --no-ansi

# Código fuente
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

# Usuario no-root
RUN useradd -m -u 1000 brujula && chown -R brujula:brujula /app
USER brujula

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

### `brujula-api/docker/Dockerfile.dev`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

RUN pip install poetry==1.8.0
RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi

# En dev no copiamos el código — lo montamos como volumen para hot reload
EXPOSE 8000
```

### `brujula-web/Dockerfile`

```dockerfile
FROM node:20-alpine AS base

# Dependencias
FROM base AS deps
WORKDIR /app
COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

# Build
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN yarn build

# Runtime
FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
```

### `brujula-web/Dockerfile.dev`

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package.json yarn.lock ./
RUN yarn install
# El código se monta como volumen en dev
EXPOSE 3000
CMD ["yarn", "dev"]
```

---

## Configuración Nginx

### `nginx/nginx.conf`

```nginx
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logs
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent"';
    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    keepalive_timeout 65;
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    # Seguridad
    server_tokens off;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Límite de tamaño de uploads (10 MB)
    client_max_body_size 10M;

    include /etc/nginx/conf.d/*.conf;
}
```

### `nginx/api.conf`

```nginx
server {
    listen 443 ssl;
    server_name api.brujula.app;

    ssl_certificate     /etc/letsencrypt/live/api.brujula.app/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.brujula.app/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    location / {
        proxy_pass         http://brujula_api:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 10s;
    }

    # Rate limiting básico en Nginx
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;
    location /auth/ {
        limit_req zone=api burst=10 nodelay;
        proxy_pass http://brujula_api:8000;
    }
}

server {
    listen 80;
    server_name api.brujula.app;
    return 301 https://$host$request_uri;
}
```

### `nginx/web.conf`

```nginx
server {
    listen 443 ssl;
    server_name brujula.app www.brujula.app;

    ssl_certificate     /etc/letsencrypt/live/brujula.app/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/brujula.app/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    location / {
        proxy_pass         http://brujula_web:3000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name brujula.app www.brujula.app;
    return 301 https://$host$request_uri;
}
```

---

## CI/CD con GitHub Actions

### Estructura de workflows

```
.github/
└── workflows/
    ├── api.yml        # CI/CD del backend
    ├── web.yml        # CI/CD del frontend
    └── deploy.yml     # Despliegue a VPS (se dispara desde api.yml y web.yml)
```

### `.github/workflows/api.yml`

```yaml
name: API CI/CD

on:
  push:
    branches: [main, develop]
    paths: ['brujula-api/**']
  pull_request:
    branches: [main]
    paths: ['brujula-api/**']

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_DB: brujula_test
          POSTGRES_USER: brujula
          POSTGRES_PASSWORD: testpass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        options: --health-cmd "redis-cli ping" --health-interval 10s

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        working-directory: brujula-api
        run: |
          pip install poetry
          poetry install
      - name: Run tests
        working-directory: brujula-api
        env:
          TEST_DATABASE_URL: postgresql+asyncpg://brujula:testpass@localhost:5432/brujula_test
          REDIS_URL: redis://localhost:6379/0
          JWT_SECRET_KEY: test_secret_32_chars_minimum_here
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          ENCRYPTION_KEY: ${{ secrets.ENCRYPTION_KEY }}
        run: poetry run pytest tests/ -v --cov=app --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v4

  build-and-push:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Login to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: brujula-api
          file: brujula-api/docker/Dockerfile
          push: true
          tags: |
            ghcr.io/${{ github.repository_owner }}/brujula-api:latest
            ghcr.io/${{ github.repository_owner }}/brujula-api:${{ github.sha }}

  deploy:
    needs: build-and-push
    uses: ./.github/workflows/deploy.yml
    with:
      service: api
    secrets: inherit
```

### `.github/workflows/deploy.yml`

```yaml
name: Deploy to VPS

on:
  workflow_call:
    inputs:
      service:
        required: true
        type: string

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /opt/brujula
            docker compose pull ${{ inputs.service }}
            docker compose up -d --no-deps ${{ inputs.service }}
            docker compose exec -T api alembic upgrade head
            docker system prune -f
```

---

## Script de despliegue inicial (`scripts/deploy.sh`)

```bash
#!/bin/bash
# Uso: ./scripts/deploy.sh
# Ejecutar en el VPS en el primer despliegue o para reset completo.

set -e

echo "🧭 La Brújula del Trader — Deploy inicial"

# Verificar que existe .env
if [ ! -f .env ]; then
  echo "❌ Error: .env no encontrado. Copiar .env.example y completar las variables."
  exit 1
fi

# Login a GHCR
echo $GHCR_TOKEN | docker login ghcr.io -u $GITHUB_USER --password-stdin

# Pull de imágenes
docker compose pull

# Levantar DB y Redis primero
docker compose up -d db redis
echo "⏳ Esperando que la DB esté lista..."
sleep 10

# Ejecutar migraciones
docker compose run --rm api alembic upgrade head
echo "✅ Migraciones aplicadas"

# Levantar todos los servicios
docker compose up -d
echo "✅ Todos los servicios corriendo"

# Verificar health
sleep 5
docker compose ps
echo "🎉 Deploy completado"
```

---

## Script de backup (`scripts/backup_db.sh`)

```bash
#!/bin/bash
# Ejecutar desde cron: 0 2 * * * /opt/brujula/scripts/backup_db.sh

set -e
source /opt/brujula/.env

BACKUP_DIR="/opt/brujula/backups"
DATE=$(date +%Y%m%d_%H%M%S)
FILE="$BACKUP_DIR/brujula_db_$DATE.sql.gz"

mkdir -p $BACKUP_DIR

docker compose -f /opt/brujula/docker-compose.yml exec -T db \
  pg_dump -U $POSTGRES_USER $POSTGRES_DB | gzip > $FILE

echo "✅ Backup guardado: $FILE"

# Eliminar backups de más de 7 días
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
echo "🧹 Backups antiguos eliminados"
```

---

## Variables de entorno de producción (`.env.example`)

```env
# GitHub
GITHUB_USER=tu_usuario_github

# PostgreSQL
POSTGRES_DB=brujula_db
POSTGRES_USER=brujula
POSTGRES_PASSWORD=password_seguro_aqui

# Redis
REDIS_PASSWORD=password_redis_seguro
REDIS_URL=redis://:password_redis_seguro@redis:6379/0

# API
DATABASE_URL=postgresql+asyncpg://brujula:password_seguro_aqui@db:5432/brujula_db
DATABASE_URL_SYNC=postgresql://brujula:password_seguro_aqui@db:5432/brujula_db
JWT_SECRET_KEY=genera_con_openssl_rand_hex_32
APP_SECRET_KEY=genera_con_openssl_rand_hex_32
ENCRYPTION_KEY=genera_con_python_secrets_token_hex_32
ANTHROPIC_API_KEY=sk-ant-...
APP_ENV=production
DEBUG=false

# Storage
STORAGE_TYPE=local
STORAGE_LOCAL_PATH=/app/uploads

# Planes
FREE_PLAN_MAX_UPLOADS=5
FREE_PLAN_MAX_AI_CALLS_PER_DAY=10
FREE_PLAN_MAX_ALERT_RULES=3
MAX_UPLOAD_SIZE_MB=10

# cTrader
CTRADER_HOST_LIVE=live.ctraderapi.com
CTRADER_HOST_DEMO=demo.ctraderapi.com
CTRADER_PORT=5035

# CORS
CORS_ORIGINS=https://brujula.app,https://www.brujula.app

# Web
NEXT_PUBLIC_API_URL=https://api.brujula.app
NEXT_PUBLIC_DEFAULT_LOCALE=es

# VPS (para GitHub Actions)
VPS_HOST=ip_del_vps
VPS_USER=ubuntu
```

---

## Reglas de infraestructura — OBLIGATORIAS

- **Nunca exponer la DB ni Redis al exterior.** Solo accesibles dentro de la red Docker `brujula_net`.
- **Solo Nginx expone los puertos 80 y 443.** Todos los demás servicios sin `ports` en producción.
- **Todo en HTTPS en producción.** HTTP redirige a HTTPS con `301`. Sin excepciones.
- **Las imágenes de producción se toman de GHCR**, nunca se buildean en el VPS.
- **Las migraciones de Alembic se ejecutan en el deploy**, antes de levantar la nueva versión de la API.
- **El volumen `uploads_data` nunca se elimina** en un deploy. Es persistente entre versiones.
- **`restart: unless-stopped`** en todos los servicios de producción para recuperación automática tras reinicios del VPS.
- **`docker system prune -f`** al final de cada deploy para limpiar imágenes antiguas y no llenar el disco.

---

## Orden de configuración en VPS (primera vez)

```
1. Apuntar dominios: brujula.app → IP del VPS, api.brujula.app → IP del VPS
2. Instalar Docker y Docker Compose en el VPS
3. Clonar brujula-infra en /opt/brujula
4. Copiar .env.example → .env y completar todas las variables
5. Obtener certificados SSL con Certbot:
   certbot certonly --standalone -d brujula.app -d www.brujula.app -d api.brujula.app
6. Ejecutar ./scripts/deploy.sh
7. Configurar cron para backup diario:
   0 2 * * * /opt/brujula/scripts/backup_db.sh >> /var/log/brujula_backup.log 2>&1
8. Configurar GitHub Actions secrets en el repositorio:
   VPS_HOST, VPS_USER, VPS_SSH_KEY, GHCR_TOKEN, ANTHROPIC_API_KEY, ENCRYPTION_KEY
```
