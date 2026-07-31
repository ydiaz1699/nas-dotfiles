#!/bin/bash
# Levanta servicios críticos en orden con health checks
source "$NAS_DOTFILES/shell/init.sh"

echo "▲ Levantando datasql..."
cd /docker/datasql
svc up datasql

echo "⏳ Esperando postgres healthy..."
until [ "$(docker inspect --format='{{.State.Health.Status}}' datapostgres)" = "healthy" ]; do
  echo "  postgres no listo, esperando 5s..."; sleep 5
done
echo "✔ Postgres listo"

echo "▲ Levantando homeassistant..."
cd /docker/homeassistant
svc up homeassistant

echo "▲ Levantando n8n..."
cd /docker/n8n
# Esperar que postgres acepte conexiones TCP antes de n8n
until nc -z 127.0.0.1 5432; do
  echo "  esperando puerto postgres..."; sleep 3
done
svc up n8n

echo "✔ Todo levantado"
