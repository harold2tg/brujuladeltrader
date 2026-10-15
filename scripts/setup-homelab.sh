#!/bin/bash
# =============================================================================
# La Brújula del Trader — Script de Setup para Homelab
# =============================================================================
# Este script configura el homelab para correr Brujula del Trader
# Ejecutar UNA VEZ como setup inicial
#
# Uso: ./scripts/setup-homelab.sh
# =============================================================================

set -e

echo "🧭 La Brújula del Trader — Setup de Homelab"
echo "=============================================="
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funciones helper
log_info() { echo -e "${GREEN}✓${NC} $1"; }
log_warn() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }

# ──────────────────────────────────────────────
# 1. Verificar requisitos
# ──────────────────────────────────────────────
echo "1️⃣  Verificando requisitos..."

# Verificar Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker no está instalado"
    exit 1
fi
log_info "Docker instalado: $(docker --version)"

# Verificar docker compose
if ! docker compose version &> /dev/null; then
    log_error "Docker Compose no está instalado"
    exit 1
fi
log_info "Docker Compose instalado: $(docker compose version)"

# Verificar PostgreSQL (debe estar corriendo como contenedor)
if ! docker ps | grep -q postgres; then
    log_error "PostgreSQL no está corriendo como contenedor Docker"
    log_warn "Este script asume que PostgreSQL 16 ya está corriendo en el homelab"
    exit 1
fi
log_info "PostgreSQL corriendo"

# Verificar Redis (debe estar corriendo como contenedor)
if ! docker ps | grep -q redis; then
    log_error "Redis no está corriendo como contenedor Docker"
    log_warn "Este script asume que Redis 7 ya está corriendo en el homelab"
    exit 1
fi
log_info "Redis corriendo"

echo ""

# ──────────────────────────────────────────────
# 2. Crear directorio de trabajo
# ──────────────────────────────────────────────
echo "2️⃣  Creando directorio de trabajo..."

BRUJULA_DIR="/data/brujula"

if [ ! -d "$BRUJULA_DIR" ]; then
    sudo mkdir -p "$BRUJULA_DIR"
    sudo chown $USER:$USER "$BRUJULA_DIR"
    log_info "Directorio $BRUJULA_DIR creado"
else
    log_info "Directorio $BRUJULA_DIR ya existe"
fi

echo ""

# ──────────────────────────────────────────────
# 3. Crear base de datos y usuario en PostgreSQL
# ──────────────────────────────────────────────
echo "3️⃣  Configurando PostgreSQL..."

read -p "¿Ya creaste la base de datos brujula_db en PostgreSQL? (s/n): " db_exists

if [ "$db_exists" != "s" ]; then
    log_warn "Creando base de datos y usuario en PostgreSQL..."
    echo ""
    echo "Ejecuta estos comandos en tu contenedor de PostgreSQL:"
    echo ""
    echo "  docker exec -it <nombre_contenedor_postgres> psql -U <tu_usuario_admin>"
    echo ""
    echo "  CREATE USER brujula WITH PASSWORD 'tu_password_seguro';"
    echo "  CREATE DATABASE brujula_db OWNER brujula;"
    echo "  GRANT ALL PRIVILEGES ON DATABASE brujula_db TO brujula;"
    echo "  \\q"
    echo ""
    read -p "Presiona Enter cuando hayas creado la base de datos..."
fi

log_info "PostgreSQL configurado"
echo ""

# ──────────────────────────────────────────────
# 4. Configurar Redis DB number
# ──────────────────────────────────────────────
echo "4️⃣  Configurando Redis..."

log_info "Redis usará DB número 1 (configurado en .env)"
log_warn "Asegúrate de que el password de Redis en .env coincida con el de tu Redis"
echo ""

# ──────────────────────────────────────────────
# 5. Descargar docker-compose.homelab.yml
# ──────────────────────────────────────────────
echo "5️⃣  Descargando archivos de configuración..."

cd "$BRUJULA_DIR"

# Verificar si estamos en un repo git
if [ ! -d ".git" ]; then
    log_warn "Clonando repositorio..."
    read -p "URL del repositorio (o presiona Enter para usar GitHub): " repo_url
    
    if [ -z "$repo_url" ]; then
        repo_url="https://github.com/harold2tg/brujuladeltrader.git"
    fi
    
    git clone "$repo_url" .
    log_info "Repositorio clonado"
else
    log_info "Repositorio ya existe, haciendo pull..."
    git pull
fi

echo ""

# ──────────────────────────────────────────────
# 6. Configurar .env
# ──────────────────────────────────────────────
echo "6️⃣  Configurando variables de entorno..."

if [ ! -f ".env" ]; then
    cp .env.homelab.example .env
    log_info ".env creado desde .env.homelab.example"
    log_warn "⚠️  IMPORTANTE: Editá .env y completá las variables"
    echo ""
    echo "Variables críticas a configurar:"
    echo "  - POSTGRES_PASSWORD"
    echo "  - REDIS_PASSWORD"
    echo "  - JWT_SECRET_KEY"
    echo "  - APP_SECRET_KEY"
    echo "  - ENCRYPTION_KEY"
    echo "  - ANTHROPIC_API_KEY"
    echo "  - CTRADER_CLIENT_ID"
    echo "  - CTRADER_CLIENT_SECRET"
    echo ""
    echo "Podés generar secrets con:"
    echo "  openssl rand -hex 32"
    echo ""
    read -p "Presiona Enter cuando hayas configurado .env..."
else
    log_info ".env ya existe"
fi

echo ""

# ──────────────────────────────────────────────
# 7. Configurar Nginx Proxy Manager
# ──────────────────────────────────────────────
echo "7️⃣  Configurando Nginx Proxy Manager..."

log_warn "Configurar proxy hosts en Nginx Proxy Manager:"
echo ""
echo "  1. Abrí Nginx Proxy Manager (puerto 81)"
echo "  2. Crear Proxy Host para brujula.homelab:"
echo "     - Domain Names: brujula.homelab"
echo "     - Scheme: http"
echo "     - Forward Hostname/IP: localhost"
echo "     - Forward Port: 3000"
echo "     - SSL: Habilitar (Let's Encrypt o certificado personalizado)"
echo ""
echo "  3. Crear Proxy Host para api.brujula.homelab:"
echo "     - Domain Names: api.brujula.homelab"
echo "     - Scheme: http"
echo "     - Forward Hostname/IP: localhost"
echo "     - Forward Port: 8000"
echo "     - SSL: Habilitar"
echo ""
echo "  4. En Custom Locations, agregar:"
echo "     - Location: /"
echo "     - Forward Hostname: localhost"
echo "     - Forward Port: 8000"
echo ""
read -p "Presiona Enter cuando hayas configurado Nginx Proxy Manager..."

echo ""

# ──────────────────────────────────────────────
# 8. Configurar GitHub Secrets
# ──────────────────────────────────────────────
echo "8️⃣  Configurando GitHub Secrets..."

log_warn "Agregar estos secrets en GitHub (Settings → Secrets and variables → Actions):"
echo ""
echo "  TAILSCALE_CLIENT_ID: OAuth Client ID de Tailscale"
echo "  TAILSCALE_CLIENT_SECRET: OAuth Client Secret de Tailscale"
echo "  HOMELAB_SSH_KEY: Clave SSH privada para acceder al homelab"
echo "  HOMELAB_SSH_USER: Usuario SSH (ej: ubuntu)"
echo "  HOMELAB_TAILSCALE_IP: IP de Tailscale del homelab (ej: 100.x.y.z)"
echo "  NEXT_PUBLIC_API_URL: https://api.brujula.homelab"
echo ""
echo "Para generar la clave SSH:"
echo "  ssh-keygen -t ed25519 -C 'github-actions-homelab'"
echo "  cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys"
echo "  cat ~/.ssh/id_ed25519  # Copiar esto a HOMELAB_SSH_KEY"
echo ""
read -p "Presiona Enter cuando hayas configurado los secrets..."

echo ""

# ──────────────────────────────────────────────
# 9. Primera ejecución
# ──────────────────────────────────────────────
echo "9️⃣  Primera ejecución..."

read -p "¿Querés iniciar los servicios ahora? (s/n): " start_now

if [ "$start_now" = "s" ]; then
    log_info "Iniciando servicios..."
    docker compose -f docker-compose.homelab.yml pull
    docker compose -f docker-compose.homelab.yml up -d
    
    echo ""
    log_info "Esperando 10 segundos para healthchecks..."
    sleep 10
    
    echo ""
    log_info "Estado de los servicios:"
    docker compose -f docker-compose.homelab.yml ps
else
    log_warn "Para iniciar manualmente:"
    echo "  cd $BRUJULA_DIR"
    echo "  docker compose -f docker-compose.homelab.yml up -d"
fi

echo ""

# ──────────────────────────────────────────────
# 10. Configurar backups
# ──────────────────────────────────────────────
echo "🔟  Configurando backups..."

log_warn "Agregar backup de brujula al script de backup diario del homelab:"
echo ""
echo "  # Backup de brujula_db"
echo "  docker exec <postgres_container> pg_dump -U brujula brujula_db | gzip > /backups/brujula_db_\$(date +%Y%m%d).sql.gz"
echo ""
echo "  # Backup de uploads"
echo "  tar -czf /backups/brujula_uploads_\$(date +%Y%m%d).tar.gz /data/brujula/uploads/"
echo ""

echo ""
echo "=============================================="
echo -e "${GREEN}✅ Setup completado!${NC}"
echo "=============================================="
echo ""
echo "Próximos pasos:"
echo "  1. Verificar que los servicios estén corriendo:"
echo "     docker compose -f docker-compose.homelab.yml ps"
echo ""
echo "  2. Verificar logs:"
echo "     docker compose -f docker-compose.homelab.yml logs -f"
echo ""
echo "  3. Ejecutar migraciones de base de datos:"
echo "     docker compose -f docker-compose.homelab.yml exec api alembic upgrade head"
echo ""
echo "  4. Probar acceso:"
echo "     curl http://localhost:8000/health"
echo "     curl http://localhost:3000"
echo ""
echo "  5. Configurar Tailscale para acceso remoto (si aplica)"
echo ""
echo "Documentación completa: HOMELAB_DEPLOYMENT.md"
echo ""
