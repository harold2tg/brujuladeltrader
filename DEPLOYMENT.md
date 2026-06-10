# La Brújula del Trader — Guía de Ejecución

> **Última actualización:** Junio 2026

Esta guía explica cómo ejecutar el proyecto en **desarrollo local** y en **producción** con dos opciones de deployment.

---

## Tabla de Contenidos

1. [Resumen Rápido](#resumen-rápido)
2. [Prerrequisitos](#prerrequisitos)
3. [Desarrollo Local](#desarrollo-local)
4. [Producción — Opción A: Docker Compose (VPS)](#producción--opción-a-docker-compose-vps)
5. [Producción — Opción B: Terraform (GCP)](#producción--opción-b-terraform-gcp)
6. [Comparación de Costos](#comparación-de-costos)
7. [Problemas Comunes](#problemas-comunes)

---

## Resumen Rápido

| Entorno | Comando | Costo | Dificultad |
|---------|---------|-------|------------|
| **Desarrollo** | `docker compose -f docker-compose.dev.yml up` | $0 | ⭐ Fácil |
| **Producción (VPS)** | `./deploy.sh deploy` | ~$10-20/mes | ⭐⭐ Media |
| **Producción (GCP)** | `terraform apply` | ~$90/mes | ⭐⭐⭐ Alta |

---

## Prerrequisitos

### Para Desarrollo Local

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v24+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.20+)
- Git
- Editor de código (VS Code recomendado)

### Para Producción (VPS)

- Un VPS con Ubuntu 22.04+ (DigitalOcean, Hetzner, Linode, etc.)
- Mínimo 2GB RAM, 2 vCPU, 50GB disco
- Dominio apuntado al VPS (brujula.app, api.brujula.app)
- Acceso SSH al VPS

### Para Producción (GCP)

- Cuenta en Google Cloud Platform
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) instalado
- Proyecto GCP habilitado con billing
- Dominio apuntado a GCP

---

## Desarrollo Local

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/brujuladeltrader.git
cd brujuladeltrader
```

### 2. Configurar variables de entorno

**Backend:**
```bash
cd Bakend-bdt
cp .env.example .env
# Editar .env con tus valores (los defaults funcionan para dev)
```

**Frontend:**
```bash
cd frontend-bdt
cp .env.local.example .env.local
```

### 3. Iniciar servicios

**Backend (API + Worker + DB + Redis):**
```bash
cd Bakend-bdt
docker compose -f docker-compose.dev.yml up -d
```

**Frontend:**
```bash
cd frontend-bdt
docker compose -f docker-compose.dev.yml up -d
```

### 4. Ejecutar migraciones

```bash
cd Bakend-bdt
docker compose -f docker-compose.dev.yml exec api alembic upgrade head
```

### 5. Verificar

| Servicio | URL | Descripción |
|----------|-----|-------------|
| API | http://localhost:8000 | FastAPI con Swagger |
| API Docs | http://localhost:8000/docs | Documentación interactiva |
| Web | http://localhost:3000 | Frontend Next.js |
| PostgreSQL | localhost:5432 | Base de datos |
| Redis | localhost:6379 | Caché |

### Comandos Útiles

```bash
# Ver logs del backend
docker compose -f docker-compose.dev.yml logs -f api

# Ver logs del frontend
docker compose -f docker-compose.dev.yml logs -f web

# Ejecutar tests
docker compose -f docker-compose.dev.yml run --rm test pytest tests/ -v

# Abrir consola de la DB
docker compose -f docker-compose.dev.yml exec db psql -U brujula -d brujula_db

# Detener todo
docker compose -f docker-compose.dev.yml down

# Detener y eliminar volúmenes (reset completo)
docker compose -f docker-compose.dev.yml down -v
```

---

## Producción — Opción A: Docker Compose (VPS)

### Costo Estimado: ~$10-20/mes

| Recurso | Costo |
|---------|-------|
| VPS (2GB RAM, 2 vCPU) | ~$10-15/mes |
| Dominio | ~$10/año |
| **Total** | **~$10-20/mes** |

### Arquitectura

```
                    Internet
                       │
                  ┌────┴────┐
                  │  Nginx  │ ← SSL + Reverse Proxy
                  │  :80/443│
                  └────┬────┘
                       │
            ┌──────────┼──────────┐
            │                     │
       ┌────┴────┐          ┌────┴────┐
       │   API   │          │   Web   │
       │ FastAPI │          │ Next.js │
       │  :8000  │          │  :3000  │
       └────┬────┘          └─────────┘
            │
       ┌────┴────┐
       │ Worker  │
       │ Celery  │
       └────┬────┘
            │
   ┌────────┼────────┐
   │                  │
┌──┴──┐          ┌───┴───┐
│ DB  │          │ Redis │
│ PG  │          │       │
└─────┘          └───────┘
```

### Paso a Paso

#### 1. Preparar el VPS

```bash
# Conectar al VPS
ssh root@tu-ip

# Actualizar sistema
apt update && apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com | sh

# Instalar Docker Compose
apt install docker-compose-plugin -y

# Instalar Git
apt install git -y
```

#### 2. Clonar el repositorio

```bash
cd /opt
git clone https://github.com/tu-usuario/brujuladeltrader.git
cd brujuladeltrader
```

#### 3. Configurar variables de entorno

```bash
cp .env.prod.example .env
nano .env  # Editar con tus valores
```

**Valores mínimos a cambiar:**
- `APP_SECRET_KEY` → Generar con: `openssl rand -hex 32`
- `JWT_SECRET_KEY` → Generar con: `openssl rand -hex 32`
- `ENCRYPTION_KEY` → Generar con: `python3 -c "import secrets; print(secrets.token_hex(32))"`
- `POSTGRES_PASSWORD` → Contraseña fuerte
- `REDIS_PASSWORD` → Contraseña fuerte

#### 4. Configurar DNS

En tu proveedor de DNS, crea los siguientes registros:

| Tipo | Nombre | Valor |
|------|--------|-------|
| A | `brujula.app` | `IP_DEL_VPS` |
| A | `www.brujula.app` | `IP_DEL_VPS` |
| A | `api.brujula.app` | `IP_DEL_VPS` |

#### 5. Ejecutar deploy

```bash
# Primera vez
./deploy.sh init

# Obtener SSL real
./deploy.sh ssl

# Deploy completo
./deploy.sh deploy
```

#### 6. Verificar

```bash
# Ver estado
./deploy.sh status

# Ver logs
./deploy.sh logs

# Ver logs de un servicio específico
./deploy.sh logs api
```

### Comandos de Mantenimiento

```bash
# Actualizar (sin rebuild)
./deploy.sh update

# Backup de la base de datos
./deploy.sh backup

# Ver logs en tiempo real
./deploy.sh logs api
./deploy.sh logs web
./deploy.sh logs nginx
```

### Backups Automáticos

Agregar al crontab del VPS:

```bash
crontab -e
```

Agregar esta línea (backup diario a las 2 AM):

```bash
0 2 * * * /opt/brujuladeltrader/deploy.sh backup >> /var/log/brujula-backup.log 2>&1
```

---

## Producción — Opción B: Terraform (GCP)

### Costo Estimado: ~$90/mes

| Servicio | Costo Mensual |
|----------|---------------|
| Cloud Run (API + Web) | ~$13 |
| Compute Engine (Worker) | ~$7 |
| Cloud SQL (PostgreSQL) | ~$15 |
| Memorystore (Redis) | ~$18 |
| Load Balancer | ~$18 |
| VPC Connector | ~$18 |
| Storage + Registry | ~$1 |
| **Total** | **~$90/mes** |

### Arquitectura

```
                         Internet
                            │
                   Cloud Load Balancer
                    (HTTPS + SSL managed)
                            │
                ┌───────────┴───────────┐
                │                       │
          Serverless NEG          Serverless NEG
                │                       │
         Cloud Run (API)         Cloud Run (Web)
          FastAPI :8000           Next.js :3000
                │                       │
                └───────────┬───────────┘
                            │
                  Serverless VPC Connector
                            │
              ┌─────────────┼─────────────┐
              │             │             │
         Cloud SQL     Memorystore   Compute Engine
        PostgreSQL 15     Redis 7      Celery Worker
         (private IP)   (private IP)    e2-micro
```

### Paso a Paso

#### 1. Configurar Google Cloud

```bash
# Instalar gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Seleccionar proyecto
gcloud config set project TU_PROYECTO_ID

# Habilitar APIs necesarias
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  compute.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com
```

#### 2. Crear bucket para Terraform state

```bash
gsutil mb -l us-central1 gs://brujula-terraform-state
```

#### 3. Configurar GitHub Secrets

En tu repositorio de GitHub, ir a Settings → Secrets and variables → Actions, y crear:

| Secret | Descripción |
|--------|-------------|
| `GCP_PROJECT_ID` | ID del proyecto GCP |
| `GCP_SA_KEY` | JSON de la service account de GCP |

Para crear la service account:

```bash
# Crear service account
gcloud iam service-accounts create terraform-sa \
  --display-name="Terraform Service Account"

# Dar permisos
gcloud projects add-iam-policy-binding TU_PROYECTO_ID \
  --member="serviceAccount:terraform-sa@TU_PROYECTO_ID.iam.gserviceaccount.com" \
  --role="roles/editor"

# Crear key
gcloud iam service-accounts keys create key.json \
  --iam-account=terraform-sa@TU_PROYECTO_ID.iam.gserviceaccount.com
```

#### 4. Ejecutar Terraform

```bash
cd infra/terraform

# Inicializar
terraform init

# Ver plan
terraform plan -var="project_id=TU_PROYECTO_ID" -var="env=prod"

# Aplicar
terraform apply -var="project_id=TU_PROYECTO_ID" -var="env=prod"
```

#### 5. Configurar secrets

```bash
cd ../../

# Poblar secrets en Secret Manager
./infra/scripts/setup-secrets.sh
```

#### 6. Migrar base de datos

```bash
# Migrar datos desde VPS
./infra/scripts/migrate-db.sh
```

#### 7. Configurar DNS

En Cloud DNS, crear registros:

| Tipo | Nombre | Valor |
|------|--------|-------|
| A | `brujula.app` | `IP_DEL_LOAD_BALANCER` |
| A | `api.brujula.app` | `IP_DEL_LOAD_BALANCER` |

#### 8. Deploy de containers

```bash
# Build y push de imágenes
gcloud builds submit --tag us-central1-docker.pkg.dev/TU_PROYECTO_ID/brujula/api:latest Bakend-bdt/
gcloud builds submit --tag us-central1-docker.pkg.dev/TU_PROYECTO_ID/brujula/web:latest frontend-bdt/

# Aplicar Terraform (deploy Cloud Run)
cd infra/terraform
terraform apply -var="project_id=TU_PROYECTO_ID" -var="env=prod"
```

### CI/CD Automático

El workflow de GitHub Actions despliega automáticamente:
- En `push` a `main`: Build → Artifact Registry → Cloud Run
- En PR: Terraform plan (solo muestra cambios)

### Comandos Útiles

```bash
# Ver logs de Cloud Run
gcloud run services logs read brujula-api-prod --region us-central1 --limit 100

# Ver servicios
gcloud run services list --region us-central1

# Rollback (revertir DNS a VPS)
./infra/scripts/rollback.sh
```

---

## Comparación de Costos

### Mensual

| Concepto | Docker Compose (VPS) | GCP (Cloud Run) |
|----------|---------------------|-----------------|
| Computo | ~$10-15 | ~$20 |
| Base de datos | Incluido | ~$15 |
| Redis | Incluido | ~$18 |
| Load Balancer | Incluido | ~$18 |
| SSL | Gratis (Let's Encrypt) | Gratis (managed) |
| Storage | Incluido | ~$1 |
| **Total** | **~$10-20/mes** | **~$90/mes** |

### Anual

| Opción | Costo Anual |
|--------|-------------|
| Docker Compose (VPS) | ~$120-240 |
| GCP (Cloud Run) | ~$1,080 |

### Cuando Crece

| Usuarios Concurrentes | Docker Compose | GCP |
|-----------------------|----------------|-----|
| 1-10 | ✅ Perfecto | ✅ Funciona |
| 10-50 | ⚠️ Puede necesitar upgrade | ✅ Auto-scales |
| 50-100 | ❌ Necesita upgrade serio | ✅ Auto-scales |
| 100+ | ❌ No escala | ✅ Escala automáticamente |

### Mi Recomendación

| Etapa | Recomendación |
|-------|---------------|
| **MVP / Desarrollo** | Docker Compose ($10-20/mes) |
| **Primeros usuarios** | Docker Compose ($10-20/mes) |
| **Crecimiento** | Migrar a GCP (~$90/mes) |
| **Escala** | GCP con optimizaciones |

---

## Problemas Comunes

### Docker Compose

**Problema:** `Cannot connect to the Docker daemon`
```bash
# Solución: Iniciar Docker
sudo systemctl start docker
```

**Problema:** `Port already in use`
```bash
# Solución: Ver qué usa el puerto
lsof -i :8000
# Matar el proceso o cambiar el puerto en docker-compose.yml
```

**Problema:** `database connection failed`
```bash
# Solución: Verificar que PostgreSQL está corriendo
docker compose -f docker-compose.dev.yml ps
# Reiniciar
docker compose -f docker-compose.dev.yml restart db
```

### GCP / Terraform

**Problema:** `Permission denied on project`
```bash
# Solución: Verificar permisos de la service account
gcloud projects get-iam-policy TU_PROYECTO_ID
```

**Problema:** `Cloud SQL connection refused`
```bash
# Solución: Verificar que Cloud SQL tiene IP privada
gcloud sql instances describe brujula-prod
```

**Problema:** `Cloud Run timeout`
```bash
# Solución: Aumentar timeout en Terraform
# En modules/cloud-run/main.tf, cambiar timeout a 600
```

---

## Estructura del Proyecto

```
brujuladeltrader/
├── Bakend-bdt/              # Backend FastAPI
├── frontend-bdt/            # Frontend Next.js
├── movil-bdt/               # App móvil (futuro)
├── infra/                   # Terraform (GCP)
│   └── terraform/
├── nginx/                   # Config Nginx (Docker)
├── docker-compose.dev.yml   # Desarrollo
├── docker-compose.prod.yml  # Producción (Docker)
├── deploy.sh                # Script de deploy
├── .env.prod.example        # Template variables
└── README.md                # Esta guía
```

---

## Soporte

Si tenés problemas:

1. Revisá esta guía
2. Revisá los logs: `./deploy.sh logs` o `docker compose logs`
3. Revisá la documentación de [Docker](https://docs.docker.com/) o [GCP](https://cloud.google.com/docs)
4. Abrí un issue en GitHub

---

**Hecho con ❤️ para La Brújula del Trader**
