#!/bin/bash
# Detiene servicios críticos en orden y reinicia el NAS
echo "▼ Bajando homeassistant..."
cd /docker/homeassistant && svc down homeassistant

echo "▼ Bajando n8n..."
cd /docker/n8n && svc down n8n

echo "▼ Bajando datasql..."
cd /docker/datasql && svc down datasql

echo "✔ Todo bajado"
reboot
