# Redes avanzadas — macvlan / systemd-networkd

> **Estado:** Pendiente de contenido
> **Contexto:** Migración de ifupdown a systemd-networkd con shim macvlan
> para exponer contenedores Docker con IP propia en la LAN.

---

## Propósito

Algunos servicios necesitan una IP real en la LAN del host (no NAT):
- AdGuard Home → IP fija para usarse como DNS (puerto 53)
- Pi-hole → mismo caso
- Cualquier servicio que necesite ser "visible" como dispositivo independiente

La solución: red macvlan en Docker + shim en el host para comunicación
bidireccional (host ↔ contenedor macvlan).

---

## Contenido pendiente

Cuando se complete, este documento incluirá:

1. **Pre-requisitos** — qué verificar antes de migrar
2. **Migración ifupdown → systemd-networkd** — paso a paso
3. **ConfigureWithoutCarrier** — por qué es necesario y qué hace
4. **Crear red macvlan en Docker** — compose.yml con subnet/gateway/ip_range
5. **Shim del host** — interfaz virtual para comunicación host ↔ macvlan
6. **Compose con IP fija** — ejemplo con AdGuard
7. **Orden de apagado** — cómo evitar pérdida de red al deshabilitar ifupdown
8. **Recuperación** — qué hacer si se pierde acceso SSH
9. **Verificación** — tests para confirmar que todo funciona

---

## Relación con el catálogo

Si un servicio usa macvlan (ej. AdGuard), su ficha en
`agent/catalog/services/adguard/ficha.md` debe incluir en `notes:`:

```yaml
notes: >
  Red macvlan con IP fija 192.168.0.201.
  Requiere shim en el host ANTES de levantar el contenedor.
  Ver references/networking.md en la skill para la migración completa
  de systemd-networkd.
```

---

## TODO

- [ ] Pegar contenido de la guía de migración (de otra conversación)
- [ ] Agregar ejemplo de compose con macvlan
- [ ] Documentar recuperación si se pierde SSH
