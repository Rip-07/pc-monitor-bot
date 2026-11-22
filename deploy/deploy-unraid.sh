#!/bin/sh

set -eu

CONTAINER_NAME="${CONTAINER_NAME:-computer-monitor-bot}"
IMAGE_NAME="${IMAGE_NAME:-computer-monitor-bot}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

FULL_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"

echo "Starting deploy for ${CONTAINER_NAME}"
echo "Image: ${FULL_IMAGE}"

echo "Checking required variables..."

if [ -z "${BOT_TOKEN:-}" ]; then
    echo "ERROR: TELEGRAM_BOT_TOKEN is empty"
    exit 1
fi

if [ -z "${API_URL:-}" ]; then
    echo "ERROR: API_URL is empty"
    exit 1
fi

if [ -z "${API_KEY:-}" ]; then
    echo "ERROR: API_KEY is empty"
    exit 1
fi

if [ -z "${CHECK_INTERVAL:-}" ]; then
    echo "ERROR: CHECK_INTERVAL is empty"
    exit 1
fi

if [ -z "${CHAT_ID:-}" ]; then
    echo "ERROR: CHAT_ID is empty"
    exit 1
fi

if [ -z "${AUTHORIZED_USER_ID:-}" ]; then
    echo "ERROR: AUTHORIZED_USER_ID is empty"
    exit 1
fi

echo "Stopping old container if exists..."
docker stop "${CONTAINER_NAME}" 2>/dev/null || true
docker rm "${CONTAINER_NAME}" 2>/dev/null || true

echo "Starting new container..."
docker run -d \
    --name "${CONTAINER_NAME}" \
    --restart unless-stopped \
    -e BOT_TOKEN="${BOT_TOKEN}" \
    -e API_URL="${API_URL}" \
    -e API_KEY="${API_KEY}" \
    -e CHECK_INTERVAL="${CHECK_INTERVAL}" \
    -e CHAT_ID="${CHAT_ID}" \
    -e AUTHORIZED_USER_ID="${AUTHORIZED_USER_ID}" \
    -e COMPUTERS="${COMPUTERS:-main_pc}" \
    --log-driver json-file \
    --log-opt max-size=10m \
    --log-opt max-file=3 \
    "${FULL_IMAGE}"

echo "Waiting for container..."
sleep 5

if docker ps --format '{{.Names}}' | grep -qx "${CONTAINER_NAME}"; then
    echo "Container started successfully"
    docker logs --tail 30 "${CONTAINER_NAME}" || true
else
    echo "ERROR: container failed to start"
    docker logs "${CONTAINER_NAME}" || true
    exit 1
fi

echo "Cleaning unused Docker images..."
docker image prune -f

echo "Deploy completed successfully"