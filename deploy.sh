#!/bin/bash
# ──────────────────────────────────────────────
# La Brújula del Trader — Deploy Script
# ──────────────────────────────────────────────
# Usage: ./deploy.sh [command]
# Commands: init, deploy, update, logs, status, ssl, backup

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Helpers
log() { echo -e "${BLUE}[$(date +'%H:%M:%S')]${NC} $1"; }
success() { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

# ──────────────────────────────────────────────
# Check requirements
# ──────────────────────────────────────────────
check_requirements() {
    command -v docker >/dev/null 2>&1 || error "Docker not installed"
    command -v docker compose >/dev/null 2>&1 || error "Docker Compose not installed"
    [ -f .env ] || error ".env file not found. Copy .env.prod.example to .env"
}

# ──────────────────────────────────────────────
# Init: First time setup
# ──────────────────────────────────────────────
cmd_init() {
    log "Initializing La Brújula del Trader..."
    
    # Check .env
    if [ ! -f .env ]; then
        warn ".env not found. Creating from template..."
        cp .env.prod.example .env
        warn "⚠️  Edit .env with your production values before continuing!"
        exit 1
    fi
    
    # Create SSL directory
    mkdir -p nginx/ssl
    
    # Generate self-signed cert (temporary)
    if [ ! -f nginx/ssl/cert.pem ]; then
        log "Generating temporary self-signed SSL certificate..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/key.pem \
            -out nginx/ssl/cert.pem \
            -subj "/C=CO/ST=Bogota/L=Bogota/O=La Brujula del Trader/CN=brujula.app"
        success "Self-signed certificate created"
    fi
    
    # Build images
    log "Building Docker images..."
    docker compose -f docker-compose.prod.yml build
    
    # Start services
    log "Starting services..."
    docker compose -f docker-compose.prod.yml up -d
    
    # Wait for DB
    log "Waiting for PostgreSQL..."
    sleep 10
    
    # Run migrations
    log "Running database migrations..."
    docker compose -f docker-compose.prod.yml exec -T api alembic upgrade head
    
    success "Initialization complete!"
    log "Next steps:"
    echo "  1. Edit .env with production values"
    echo "  2. Run: ./deploy.sh ssl (to get real SSL certificate)"
    echo "  3. Run: ./deploy.sh deploy"
}

# ──────────────────────────────────────────────
# Deploy: Full deployment
# ──────────────────────────────────────────────
cmd_deploy() {
    log "Deploying La Brújula del Trader..."
    
    check_requirements
    
    # Pull latest changes
    log "Pulling latest changes..."
    git pull origin main
    
    # Build images
    log "Building Docker images..."
    docker compose -f docker-compose.prod.yml build --no-cache
    
    # Stop old containers
    log "Stopping old containers..."
    docker compose -f docker-compose.prod.yml down
    
    # Start services
    log "Starting services..."
    docker compose -f docker-compose.prod.yml up -d
    
    # Wait for DB
    log "Waiting for PostgreSQL..."
    sleep 10
    
    # Run migrations
    log "Running database migrations..."
    docker compose -f docker-compose.prod.yml exec -T api alembic upgrade head
    
    # Clean old images
    log "Cleaning old images..."
    docker image prune -f
    
    # Show status
    docker compose -f docker-compose.prod.yml ps
    
    success "Deployment complete! 🚀"
    log "Services:"
    echo "  - API:  https://api.brujula.app"
    echo "  - Web:  https://brujula.app"
}

# ──────────────────────────────────────────────
# Update: Quick update (no rebuild)
# ──────────────────────────────────────────────
cmd_update() {
    log "Updating La Brújula del Trader..."
    
    check_requirements
    
    git pull origin main
    
    docker compose -f docker-compose.prod.yml up -d --build
    
    docker compose -f docker-compose.prod.yml exec -T api alembic upgrade head
    
    success "Update complete!"
}

# ──────────────────────────────────────────────
# SSL: Get real certificate
# ──────────────────────────────────────────────
cmd_ssl() {
    log "Setting up SSL certificate..."
    
    # Stop nginx
    docker compose -f docker-compose.prod.yml stop nginx
    
    # Get certificate
    docker compose -f docker-compose.prod.yml run --rm certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        -d brujula.app \
        -d www.brujula.app \
        -d api.brujula.app \
        --email admin@brujula.app \
        --agree-tos \
        --no-eff-email
    
    # Restart nginx
    docker compose -f docker-compose.prod.yml start nginx
    
    success "SSL certificate installed!"
}

# ──────────────────────────────────────────────
# Logs: View logs
# ──────────────────────────────────────────────
cmd_logs() {
    docker compose -f docker-compose.prod.yml logs -f --tail=100 "${1:-}"
}

# ──────────────────────────────────────────────
# Status: Show status
# ──────────────────────────────────────────────
cmd_status() {
    docker compose -f docker-compose.prod.yml ps
}

# ──────────────────────────────────────────────
# Backup: Backup database
# ──────────────────────────────────────────────
cmd_backup() {
    log "Creating database backup..."
    
    BACKUP_DIR="./backups"
    mkdir -p "$BACKUP_DIR"
    
    BACKUP_FILE="$BACKUP_DIR/brujula_$(date +%Y%m%d_%H%M%S).sql.gz"
    
    docker compose -f docker-compose.prod.yml exec -T db \
        pg_dump -U "${POSTGRES_USER:-brujula}" "${POSTGRES_DB:-brujula_db}" | gzip > "$BACKUP_FILE"
    
    success "Backup created: $BACKUP_FILE"
}

# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────
case "${1:-help}" in
    init)    cmd_init ;;
    deploy)  cmd_deploy ;;
    update)  cmd_update ;;
    ssl)     cmd_ssl ;;
    logs)    cmd_logs "${2:-}" ;;
    status)  cmd_status ;;
    backup)  cmd_backup ;;
    *)
        echo "Usage: ./deploy.sh [command]"
        echo ""
        echo "Commands:"
        echo "  init     First time setup"
        echo "  deploy   Full deployment"
        echo "  update   Quick update (no rebuild)"
        echo "  ssl      Get SSL certificate"
        echo "  logs     View logs (optional: logs api|web|nginx)"
        echo "  status   Show service status"
        echo "  backup   Backup database"
        ;;
esac
