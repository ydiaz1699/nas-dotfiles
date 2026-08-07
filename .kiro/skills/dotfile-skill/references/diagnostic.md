# Recetas de diagnóstico

Orden de investigación cuando un servicio falla. Seguir paso a paso,
detenerse cuando se identifique la causa raíz.

---

## Servicio caído (no arranca / exit code ≠ 0)

```bash
svc ps <svc>                # ver estado + exit code
svc logs <svc>              # últimos logs (buscar ERROR/FATAL)
svc config <svc>            # verificar compose resuelto (typos, paths)
svc depends <svc>           # ¿dependencia caída?
```

Causas comunes:
- Volumen/config referenciado no existe → crear con `mkdir -p`
- Puerto ya en uso → `svc port-map` para ver conflictos
- Variable de entorno faltante → `svc env <svc>`
- Imagen no encontrada → `svc pull <svc>`

---

## OOM (Out of Memory)

Síntomas: exit code 137, "Killed" en logs, `OOMKilled: true` en inspect.

```bash
svc logs <svc>              # buscar "Killed" o "out of memory"
svc stats <svc>             # ver uso actual de RAM
docker inspect <container> --format='{{.State.OOMKilled}}'
svc doctor                  # ver memoria global del host
```

Solución:
1. Aumentar `deploy.resources.limits.memory` en compose.yml
2. Si el host está lleno → identificar consumidor con `svc stats` de todos
3. Considerar agregar swap si no hay: `free -h`

---

## Crash loop (reinicio continuo)

Síntomas: restart count alto en `svc health`, uptime muy bajo.

```bash
svc health                  # ver restart count
svc logs <svc> -n 100      # buscar patrón repetido en logs
svc top <svc>               # ¿proceso principal vivo?
docker inspect <container> --format='{{.RestartCount}}'
```

Solución:
1. Leer logs del último crash (buscar stack trace)
2. Si es config inválida → `svc config <svc>` + revisar archivos en `config/`
3. Si es dependencia externa (DB, API) → verificar que esté arriba
4. Temporalmente: `svc stop <svc>` para detener el loop mientras investigas

---

## Conflicto de puerto

Síntomas: "address already in use" en logs, servicio no arranca.

```bash
svc port-map                # ver todos los puertos asignados
ports                       # ss -tulnp (incluye procesos no-Docker)
svc logs <svc>              # confirmar el error "bind: address already in use"
```

Solución:
1. Identificar quién usa el puerto → `ss -tulnp | grep <puerto>`
2. Si es otro servicio Docker → cambiar puerto en compose.yml de uno de los dos
3. Si es proceso del host → detenerlo o moverlo
4. Rango seguro para nuevos puertos: 8100-8999

---

## Servicio lento / alto consumo

```bash
svc stats <svc>             # CPU y RAM en vivo
svc top <svc>               # procesos internos (¿algo comiendo CPU?)
svc logs <svc> --since 5m   # errores recientes
nas                         # dashboard general (¿host saturado?)
disk                        # ¿disco lleno?
```

Solución:
1. Si CPU > 100% → posible leak/loop en el servicio, revisar logs
2. Si RAM crece sin parar → memory leak, considerar `svc restart <svc>`
3. Si disco > 90% → limpiar logs viejos, `docker system prune`
4. Si todo el host está lento → `svc doctor` para panorama completo

---

## Healthcheck fallando (unhealthy)

```bash
svc health                  # ver cuál está unhealthy
svc logs <svc>              # ¿el servicio funciona internamente?
svc exec <svc> curl -f http://localhost:<port>/health
docker inspect <container> --format='{{.State.Health}}'
```

Solución:
1. Si el servicio responde internamente → el healthcheck está mal configurado
2. Si no responde → el servicio está colgado, `svc restart <svc>`
3. Verificar que el `test` del healthcheck usa el puerto correcto

---

## Red / conectividad entre servicios

```bash
svc net                     # mapa de redes y contenedores
svc exec <svc_a> ping <svc_b>
svc exec <svc_a> curl http://<svc_b>:<port>
dnet                        # docker network ls
```

Solución:
1. Verificar que ambos servicios están en la misma red
2. Usar `container_name` como hostname (no IP)
3. Si cambiaste red → `svc down <svc> && svc up <svc>` (restart no recrea red)

---

## Orden general de diagnóstico (cualquier problema)

```
1. svc health          → panorama global
2. svc ps <svc>        → ¿está corriendo? ¿exit code?
3. svc logs <svc>      → ¿qué dice el servicio?
4. svc doctor          → ¿problema del host? (disco, RAM, puertos)
5. svc stats <svc>     → ¿recursos del contenedor?
6. svc config <svc>    → ¿compose correcto?
7. svc depends <svc>   → ¿dependencia caída?
```
