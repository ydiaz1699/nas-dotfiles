---
id: "iobroker"
name: "ioBroker"
description: "Plataforma de automatización IoT y domótica con adapters extensibles"
aliases:
  - iobroker
  - io-broker
  - domótica
  - automatización
image: "buanet/iobroker:v11.1.0"
category: "domótica"
port_internal: 8081
port_default: 8181
protocol: "http"
needs_proxy: false
needs_db: false
db_type: "persistencia local JSONL (inicial)"
volumes:
  - "./data:/opt/iobroker"
env_required: []
env_optional:
  - "SETUID=1000"
  - "SETGID=1000"
  - "PERMISSION_CHECK=true"
  - "IOB_ADMINPORT=8081"
healthcheck: '["CMD", "/bin/bash", "-c", "/opt/scripts/healthcheck.sh"]'
backup_critical: true
backup_paths:
  - "./data"
protected: true
docs_url: "docs/services/iobroker-guide.md"
notes: "Instancia única stateful: la configuración, adapters, estados y credenciales viven en ./data. Acceso LAN en :8181. Conectado a iot_net para resolver emqx:1883. La escalabilidad inicial es vertical; no ejecutar réplicas con el mismo bind mount. La imagen está fijada en v11.1.0 y se actualiza solo con backup previo."
networks:
  - iot_net
ports:
  http: 8181
resources:
  cpus_limit: "1"
  memory_limit: "1G"
  cpus_reservation: "0.25"
  memory_reservation: "256M"
security_extra:
  security_opt:
    - "no-new-privileges:true"
---

# ioBroker

Consulta [`docs/services/iobroker-guide.md`](../../../../docs/services/iobroker-guide.md) para instalación, MQTT, backups, recuperación y actualización.
