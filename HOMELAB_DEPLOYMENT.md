# 🧭 Homelab Deployment Guide

Deployment automático de La Brújula del Trader al homelab via GitHub Actions + Tailscale.

---

## Arquitectura

```
┌─────────────────────────────────────────────────────┐
│  GitHub                                             │
│  ─────                                              │
│  Push a main → CI/CD → Build → Push a GHCR         │
└──────────────────────┬──────────────────────────────┘
                       │
                       │ Pull de imágenes
                       │
┌──────────────────────▼──────────────────────────────┐
│  Homelab (Tailscale)                                │
│  ─────────────────                                  │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │ brujula-api  │  │ brujula-web  │                 │
│  │ :8000        │  │ :3000        │                 │
│  └──────┬───────┘  └──────┬───────┘                 │
│         │                 │                         │
│         └────────┬────────┘                         │
│                  │                                  │
│         ┌────────▼────────┐                         │
│         │ PostgreSQL 16   │ (compartido)            │
│         │ Redis 7         │ (compartido)            │
│         └─────────────────┘                         │
│                                                     │
│         ┌─────────────────┐                         │
│         │ Nginx Proxy Mgr │                         │
│         │ :81             │                         │
│         └─────────────────┘                         │
│                                                     │
│  Tailscale IP: 100.x.y.z                           │
└─────────────────────────────────────────────────────┘
```

---

## Requisitos del Homelab

| Componente | Versión | Notas |
|------------|---------|-------|
| Docker | 20.10+ | Con Docker Compose v2 |
| PostgreSQL | 16 | Como contenedor Docker, accesible en puerto 5432 |
| Redis | 7 | Como contenedor Docker, accesible en puerto 6379 |
| Nginx Proxy Manager | Latest | Para reverse proxy y SSL |
| Tailscale | Latest | Conectado a la misma tailnet que GitHub Actions |
| Disco | 10GB+ libre | En /data para imágenes y uploads |

---

## Setup Inicial (una sola vez)

### 1. Crear base de datos en PostgreSQL

```bash
# Entrar al contenedor de PostgreSQL
docker exec -it <nombre_contenedor_postgres> psql -U <usuario_admin>

# Crear usuario y base de datos
CREATE USER brujula WITH PASSWORD 'tu_password_seguro';
CREATE DATABASE brujula_db OWNER brujula;
GRANT ALL PRIVILEGES ON DATABASE brujula_db TO brujula;
\q
```

### 2. Crear directorio de trabajo

```bash
sudo mkdir -p /data/brujula
sudo chown $USER:$USER /data/brujula
cd /data/brujula
```

### 3. Clonar el repositorio

```bash
git clone https://github.com/harold2tg/brujuladeltrader.git .
git checkout developer
```

### 4. Configurar variables de entorno

```bash
cp .env.homelab.example .env
nano .env  # Editar y completar todas las variables
```

**Variables críticas:**

| Variable | Descripción | Cómo generar |
|----------|-------------|--------------|
| `POSTGRES_PASSWORD` | Password de la BD brujula | El que creaste en paso 1 |
| `REDIS_PASSWORD` | Password de Redis | El mismo que tiene tu Redis compartido |
| `JWT_SECRET_KEY` | Secret para JWT tokens | `openssl rand -hex 32` |
| `APP_SECRET_KEY` | Secret general de la app | `openssl rand -hex 32` |
| `ENCRYPTION_KEY` | Clave de encriptación | `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `ANTHROPIC_API_KEY` | API key de Anthropic | Obtener de console.anthropic.com |
| `CTRADER_CLIENT_ID` | Client ID de cTrader | Obtener de cTrader Open API |
| `CTRADER_CLIENT_SECRET` | Client Secret de cTrader | Obtener de cTrader Open API |

### 5. Configurar Nginx Proxy Manager

Abrir Nginx Proxy Manager (puerto 81) y crear dos proxy hosts:

**Proxy Host 1 — Web:**
- Domain Names: `brujula.homelab`
- Scheme: `http`
- Forward Hostname/IP: `host.docker.internal`
- Forward Port: `3000`
- SSL: Habilitar (Let's Encrypt o self-signed)

**Proxy Host 2 — API:**
- Domain Names: `api.brujula.homelab`
- Scheme: `http`
- Forward Hostname/IP: `host.docker.internal`
- Forward Port: `8000`
- SSL: Habilitar

### 6. Configurar Tailscale para GitHub Actions

1. Ir a [Tailscale Admin → Settings → Keys](https://login.tailscale.com/admin/settings/keys)
2. Generar un **OAuth Client** con tag `tag:ci`
3. Guardar el Client ID y Client Secret

### 7. Configurar SSH en el homelab

```bash
# Generar una clave dedicada para CI
ssh-keygen -t ed25519 -C "github-actions-homelab" -f ~/.ssh/github_actions

# Agregar la clave pública a authorized_keys
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys

# Mostrar la clave privada (copiar para GitHub)
cat ~/.ssh/github_actions
```

### 8. Configurar GitHub Secrets

Ir a **GitHub → Repository → Settings → Secrets and variables → Actions** y agregar:

| Secret | Valor |
|--------|-------|
| `TAILSCALE_CLIENT_ID` | OAuth Client ID de Tailscale |
| `TAILSCALE_CLIENT_SECRET` | OAuth Client Secret de Tailscale |
| `HOMELAB_SSH_KEY` | Clave privada SSH (contenido de `~/.ssh/github_actions`) |
| `HOMELAB_SSH_USER` | Usuario SSH del homelab (ej: `ubuntu`) |
| `HOMELAB_HOST` | IP de Tailscale del homelab (ej: `100.x.y.z`) |
| `NEXT_PUBLIC_API_URL` | `https://api.brujula.homelab` |

### 9. Primera ejecución manual

```bash
cd /data/brujula

# Pull de imágenes
docker compose -f docker-compose.homelab.yml pull

# Iniciar servicios
docker compose -f docker-compose.homelab.yml up -d

# Ejecutar migraciones de base de datos
docker compose -f docker-compose.homelab.yml exec api alembic upgrade head

# Verificar estado
docker compose -f docker-compose.homelab.yml ps

# Ver logs
docker compose -f docker-compose.homelab.yml logs -f
```

---

## Deployment Automático

Una vez configurado, el deploy es automático:

1. Push a `main` → GitHub Actions corre tests
2. Tests pasan → Build de imágenes Docker
3. Imágenes pusheadas a GHCR
4. SSH al homelab via Tailscale → Pull + Restart

**Flujo:**
```
git push origin main → ~5 min → Homelab actualizado
```

---

## Deployment Manual

Para desplegar manualmente sin push a main:

```bash
# En el homelab
cd /data/brujula

# Pull de últimas imágenes
docker compose -f docker-compose.homelab.yml pull

# Reiniciar servicios
docker compose -f docker-compose.homelab.yml up -d

# Ejecutar migraciones (si las hay)
docker compose -f docker-compose.homelab.yml exec api alembic upgrade head
```

---

## Rollback

Si algo sale mal, podés hacer rollback a una versión anterior:

```bash
# Ver imágenes disponibles
docker images | grep brujula

# Editar docker-compose.homelab.yml y cambiar el tag
# Ejemplo: brujula-api:main-abc1234 → brujula-api:main-def5678

# O usar variables de entorno
export API_VERSION=main-abc1234
export WEB_VERSION=main-abc1234
docker compose -f docker-compose.homelab.yml up -d
```

---

## Troubleshooting

### Servicios no inician

```bash
# Ver logs detallados
docker compose -f docker-compose.homelab.yml logs api
docker compose -f docker-compose.homelab.yml logs web

# Verificar que PostgreSQL y Redis están accesibles
docker compose -f docker-compose.homelab.yml exec api ping host.docker.internal
docker compose -f docker-compose.homelab.yml exec api redis-cli -h host.docker.internal -p 6379 ping
```

### API no puede conectar a PostgreSQL

```bash
# Verificar que PostgreSQL acepta conexiones desde Docker
# En el contenedor de PostgreSQL, verificar pg_hba.conf
# Agregar línea: host all all 172.16.0.0/12 md5

# Reiniciar PostgreSQL
docker restart <nombre_contenedor_postgres>
```

### Web no puede conectar a API

```bash
# Verificar que NEXT_PUBLIC_API_URL está correcto en .env
# Debe ser la URL pública: https://api.brujula.homelab
# NO localhost:8000 (eso es desde el navegador del usuario, no desde el contenedor)
```

### Tailscale no conecta

```bash
# Verificar que Tailscale está activo
tailscale status

# Verificar que el homelab tiene IP de Tailscale
tailscale ip -4

# Reconectar si es necesario
sudo tailscale up
```

### Disco lleno

```bash
# Limpiar imágenes antiguas
docker image prune -a

# Limpiar volúmenes sin usar
docker volume prune

# Ver uso de disco
docker system df
```

---

## Monitoreo

### Logs en tiempo real

```bash
# Todos los servicios
docker compose -f docker-compose.homelab.yml logs -f

# Solo API
docker compose -f docker-compose.homelab.yml logs -f api

# Solo Worker
docker compose -f docker-compose.homelab.yml logs -f worker
```

### Health checks

```bash
# API health
curl http://localhost:8000/health

# Web health
curl http://localhost:3000

# Estado de contenedores
docker compose -f docker-compose.homelab.yml ps
```

### Métricas de recursos

```bash
# Uso de CPU/RAM por contenedor
docker stats

# Uso de disco
docker system df -v
```

---

## Backups

### Backup manual de base de datos

```bash
# Dump de la base de datos
docker exec <postgres_container> pg_dump -U brujula brujula_db > backup_$(date +%Y%m%d).sql

# Restaurar
cat backup.sql | docker exec -i <postgres_container> psql -U brujula brujula_db
```

### Backup automático

Agregar al crontab del homelab:

```bash
# Backup diario a las 2 AM
0 2 * * * cd /data/brujula && docker exec postgres pg_dump -U brujula brujula_db | gzip > /backups/brujula_db_$(date +\%Y\%m\%d).sql.gz
```

---

## Actualización de dependencias

Cuando hay cambios en `pyproject.toml` o `package.json`:

1. Push a main
2. GitHub Actions reconstruye las imágenes con las nuevas dependencias
3. El deploy automático pulla las nuevas imágenes

**No es necesario** SSH manual ni rebuild local.

---

## Seguridad

- ✅ Todos los secrets en GitHub Secrets, nunca en el código
- ✅ Tailscale para cifrado de red entre GitHub y homelab
- ✅ SSH con clave, sin passwords
- ✅ PostgreSQL y Redis solo accesibles desde la red Docker
- ✅ Nginx Proxy Manager maneja SSL/TLS
- ✅ Non-root users en contenedores Docker

---

## Soporte

- Documentación del proyecto: `README.md`
- Especificación completa: `LaBrujulaDelTrader_SRS_v1.0.md`
- Issues: https://github.com/harold2tg/brujuladeltrader/issues
