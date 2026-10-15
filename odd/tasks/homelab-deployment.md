# Homelab Deployment — GitHub → Homelab via Tailscale

**Status**: in_progress
**Created**: 2026-01-14
**Branch**: feat/homelab-deploy (a crear desde developer)
**Base**: developer

## Objetivo
Implementar deployment automático desde GitHub al homelab (Ubuntu 24.04, IP 10.0.0.245, Tailscale) reutilizando PostgreSQL 16 y Redis 7 compartidos.

## Decisiones de diseño
- **Dominio**: brujula.homelab (web) + api.brujula.homelab (API)
- **Deploy trigger**: Auto en push a main, manual con botón para otros branches
- **Ambiente**: Solo producción en homelab
- **Estrategia**: GHCR + Tailscale SSH (sin buildear en homelab)
- **Base de datos**: BD separada `brujula_db` en PostgreSQL 16 compartido
- **Redis**: DB número separado en Redis 7 compartido
- **Storage**: /data/brujula/ en SSD 240GB
- **Reverse proxy**: Nginx Proxy Manager (existente)

## Arquitectura

```
GitHub Actions → GHCR → Tailscale SSH → Homelab
                                              ↓
                                    docker-compose.homelab.yml
                                    (api + worker + web)
                                              ↓
                              PostgreSQL 16 + Redis 7 (compartidos)
                                              ↓
                              Nginx Proxy Manager → brujula.homelab
```

## Tareas

### T1: Crear docker-compose.homelab.yml ✅ COMPLETADO
**Archivo**: `docker-compose.homelab.yml`
**Descripción**: Compose override para homelab que usa servicios compartidos
**Detalles**:
- Solo servicios: api, worker, web (sin db, redis, nginx, certbot)
- Conectar a red Docker existente del homelab
- Usar `extra_hosts: ["host.docker.internal:host-gateway"]` para acceder a PG/Redis
- Variables de entorno específicas para homelab
- Volúmenes en /data/brujula/

### T2: Crear .env.homelab.example ⚠️ BLOQUEADO
**Archivo**: `.env.homelab.example`
**Descripción**: Template de variables de entorno para homelab
**Detalles**:
- DATABASE_URL apuntando a host.docker.internal:5432
- REDIS_URL apuntando a host.docker.internal:6379
- NEXT_PUBLIC_API_URL = https://api.brujula.homelab
- Variables de seguridad (JWT_SECRET, etc.)
- APP_ENV = production
- **Nota**: Archivo bloqueado por política de seguridad, usar template en HOMELAB_DEPLOYMENT.md

### T3: Crear GitHub workflows ✅ COMPLETADO
**Archivos**: `.github/workflows/deploy-homelab.yml`, `.github/workflows/ci-cd.yml`
**Descripción**: Workflows de CI/CD y deployment al homelab
**Detalles**:
- CI/CD: Tests + Build en push a main/developer
- Deploy-homelab: Trigger manual o automático en main
- Usa Tailscale para SSH seguro
- Pull de imágenes desde GHCR

### T4: Crear script de setup para homelab ✅ COMPLETADO
**Archivo**: `scripts/setup-homelab.sh`
**Descripción**: Script para inicializar el homelab (ejecutar una vez)
**Detalles**:
- Crear directorio /data/brujula/
- Crear BD brujula_db + user en PostgreSQL
- Configurar DB número en Redis
- Descargar docker-compose.homelab.yml
- Crear .env desde .env.homelab.example
- Instrucciones para configurar Nginx Proxy Manager
- Instrucciones para generar claves SSH y configurar GitHub secrets

### T5: Crear documentación de deployment ✅ COMPLETADO
**Archivo**: `HOMELAB_DEPLOYMENT.md`
**Descripción**: Documentación completa del proceso de deployment
**Detalles**:
- Requisitos del homelab
- Setup inicial (una vez)
- Proceso de deployment (automático y manual)
- Troubleshooting
- Rollback procedure
- Monitoring y logs
- Backups

### T6: Crear rama feat/homelab-deploy y commit inicial ✅ COMPLETADO
**Acción**: Crear rama desde developer
**Detalles**:
- git checkout developer
- git checkout -b feat/homelab-deploy
- Rama creada y lista para commits

## Orden de implementación

1. **T6** → Crear rama y prepararla
2. **T1** → docker-compose.homelab.yml (base del deployment)
3. **T2** → .env.homelab.example (variables necesarias)
4. **T3** → GitHub workflow (automatización)
5. **T4** → Script de setup (facilita inicialización)
6. **T5** → Documentación (guía completa)

## Consideraciones técnicas

### Red Docker en homelab
- PostgreSQL y Redis están en contenedores Docker existentes
- Los contenedores de brujula necesitan acceder a ellos
- Opción: `extra_hosts` con `host.docker.internal` → accede a puertos expuestos del host
- Alternativa: conectar a la red Docker existente donde están PG/Redis

### GHCR (GitHub Container Registry)
- Imágenes: `ghcr.io/harold2tg/brujula-api:tag` y `ghcr.io/harold2tg/brujula-web:tag`
- Tags: `latest` para main, `dev-{sha}` para otros branches
- Autenticación: `GITHUB_TOKEN` en workflow

### Tailscale SSH
- Usar `tailscale/github-action@v2` con authkey reusable
- SSH al homelab via IP de Tailscale (no IP local 10.0.0.245)
- Clave SSH en GitHub secrets

### Nginx Proxy Manager
- Configurar proxy hosts:
  - brujula.homelab → localhost:3000 (web container)
  - api.brujula.homelab → localhost:8000 (api container)
- SSL automático con Let's Encrypt (si hay dominio público) o certificados auto-firmados

### Backups
- Extender script de backup existente del homelab para incluir:
  - /data/brujula/ (uploads)
  - Dump de brujula_db desde PostgreSQL 16

## Dependencias externas
- Tailscale authkey (reusable)
- Clave SSH para el homelab
- PostgreSQL 16 y Redis 7 ya corriendo en homelab
- Nginx Proxy Manager ya configurado

## Métricas de éxito
- ✅ Push a main despliega automáticamente en < 5 minutos
- ✅ `brujula.homelab` y `api.brujula.homelab` accesibles desde red local
- ✅ API conectada a PostgreSQL 16 y Redis 7 compartidos
- ✅ Rollback manual posible (cambiar tag en docker-compose)
- ✅ Documentación clara para setup y troubleshooting
