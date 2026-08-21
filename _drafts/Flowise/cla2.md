Sí, exactamente — el compose usa `REDIS_HOST: dataredis`, que es el contenedor Redis compartido del stack `datasql` (el mismo que dejamos definido en la skill, con IP en `db_net`).

**¿Por qué está bien compartirlo y no genera conflictos?**

- Redis no es como Postgres (que tiene DBs separadas por nombre). Acá lo que separa los datos de Flowise del resto es el **prefijo de las keys**, que se arma con `QUEUE_NAME: flowise-queue`. Todas las keys que use Flowise van a llevar ese prefijo (`flowise-queue:*`), así que no pisa datos de otros servicios que también usen `dataredis`.
- Es el mismo patrón que ya usa la skill `datasql` para otros servicios (n8n, etc.) — todos comparten el mismo Redis, cada uno con su propio namespace.
- La contraseña (`REDIS_PASSWORD`) es la misma que está en `$dkco/datasql/.env`, no hay que crear una nueva.

**Único cuidado:** si en algún momento tenés muchísimos flujos con colas muy pesadas, ese Redis compartido se vuelve un recurso común — pero para tu escala (algunos flujos corriendo por día) no representa ningún problema, y es justamente el diseño que la skill `datasql` espera (un solo Redis central para todos los servicios del NAS).

Entonces no hace falta nada especial de tu parte, solo asegurate de que en el `.env` de flowise pongas el mismo valor de `REDIS_PASSWORD` que está en `$dkco/datasql/.env`:

```bash
grep ^REDIS_PASSWORD $dkco/datasql/.env
```

y lo copiás tal cual al `.env` de `flowise`. ¿Sigo con el compose completo (main + 1 worker) ya confirmado?