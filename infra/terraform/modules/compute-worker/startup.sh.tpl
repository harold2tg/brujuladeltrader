#!/bin/bash
set -euo pipefail

echo "=== Brujula Worker — Starting ==="

# Install Docker
apt-get update
apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

curl -fsSL https://download.docker.com/linux/debian/gpg | \
    gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
    https://download.docker.com/linux/debian $(lsb_release -cs) stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io jq

# Start Docker
systemctl enable docker
systemctl start docker

# Build env vars from JSON
DOCKER_ENV_ARGS=""
while IFS="=" read -r key value; do
    DOCKER_ENV_ARGS="$DOCKER_ENV_ARGS -e $key=$value"
done < <(echo '${env_vars_json}' | jq -r 'to_entries[] | "\(.key)=\(.value)"')

# Pull and run the worker container
docker pull ${docker_image}

docker run -d \
    --name brujula-worker \
    --restart unless-stopped \
    --network host \
    $DOCKER_ENV_ARGS \
    -e DATABASE_URL="postgresql://brujula@//cloudsql/${cloud_sql_connection}" \
    -e REDIS_URL="redis://:${redis_password}@${redis_host}:${redis_port}/0" \
    -e STORAGE_TYPE="gcs" \
    ${docker_image} \
    celery -A app.worker worker --loglevel=info --concurrency=2

echo "=== Brujula Worker — Started ==="
