# Guía: Cómo funciona HashiCorp Vault con Kubernetes 🔐

> **Basada exclusivamente en el video de KodeKloud:**
> *"How does your Kubernetes cluster work with HashiCorp Vault?"* ([YouTube Short H5NR9Ocqhvc](https://www.youtube.com/shorts/H5NR9Ocqhvc)).

---

## 1. El Problema que Resuelve

En Kubernetes por defecto, los secretos suelen guardarse como objetos `Secret` de Kubernetes, los cuales:
* Solo están codificados en **Base64** (no cifrados por defecto en la configuración básica).
* Viven en `etcd`.
* Obligan a exponer credenciales en manifiestos YAML o variables de entorno estáticas que quedan visibles en inspecciones y logs.

El video de KodeKloud explica la arquitectura estándar para que un clúster de Kubernetes consuma secretos directamente desde **HashiCorp Vault** sin exponer contraseñas en manifiestos y sin que la aplicación tenga que programar código específico para conectarse a Vault.

---

## 2. Los Componentes de la Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            KUBERNETES CLUSTER                               │
│                                                                             │
│   ┌─────────────────────────────────┐       ┌───────────────────────────┐   │
│   │        API Server (k8s)         │       │   Vault Agent Injector    │   │
│   │   (TokenReview API Validator)   │       │ (Mutating Webhook Pod)    │   │
│   └────────────────▲────────────────┘       └─────────────┬─────────────┘   │
│                    │                                      │                 │
│         2. Valida  │ Token JWT                            │ 3. Inyecta      │
│                    │                                      ▼                 │
│   ┌────────────────┴────────────────────────────────────────────────────┐   │
│   │ POD DE LA APLICACIÓN                                                │   │
│   │                                                                     │   │
│   │   ┌────────────────────────┐         ┌──────────────────────────┐   │   │
│   │   │     Init Container     │         │    Sidecar Container     │   │   │
│   │   │  (Descarga el secreto  │         │   (Vault Agent: renueva  │   │   │
│   │   │   antes de arrancar)   │         │    token y rota claves)  │   │   │
│   │   └───────────┬────────────┘         └────────────┬─────────────┘   │   │
│   │               │                                   │                 │
│   │               ▼ Escribe                           ▼ Actualiza       │
│   │       ┌───────────────────────────────────────────────────┐         │   │
│   │       │ Volumen Compartido en Memoria RAM (tmpfs / memory) │         │   │
│   │       │          Ruta: /vault/secrets/database            │         │   │
│   │       └─────────────────────────▲─────────────────────────┘         │   │
│   │                                 │ Lee                               │   │
│   │                   ┌─────────────┴─────────────┐                     │   │
│   │                   │    Contenedor Principal   │                     │   │
│   │                   │      (Tu Aplicación)      │                     │   │
│   │                   └───────────────────────────┘                     │   │
│   └─────────────────────────────────▲───────────────────────────────────┘   │
│                                     │                                       │
└─────────────────────────────────────┼───────────────────────────────────────┘
                                      │ 1. Autentica con JWT
                                      ▼
                        ┌───────────────────────────┐
                        │      HASHICORP VAULT      │
                        │    (Servidor Central)     │
                        │  - Motor de Secretos      │
                        │  - Políticas RBAC (HCL)   │
                        └───────────────────────────┘
```

1. **HashiCorp Vault Server:** Servidor central donde residen los secretos cifrados y las políticas de acceso.
2. **Kubernetes ServiceAccount:** Identidad propia que se le asigna al Pod de Kubernetes (proporciona un token JWT firmado por el cluster).
3. **TokenReview API:** Endpoint de Kubernetes que permite a Vault validar si un token JWT pertenece legítimamente a un Pod activo.
4. **Vault Agent Injector:** Controlador de Kubernetes (Webhook de admisión mutador) que detecta si un Pod necesita secretos y le añade contenedores automáticamente.
5. **Init Container (de Vault):** Se ejecuta antes que la aplicación; obtiene el secreto y lo escribe en el volumen temporal.
6. **Sidecar Container (Vault Agent):** Se ejecuta en segundo plano junto a la aplicación para renovar el token y mantener el secreto actualizado si cambia.
7. **Volumen compartido en memoria RAM (`tmpfs`):** Espacio volátil donde se deposita el secreto; nunca toca el disco.

---

## 3. Flujo Paso a Paso (Cómo Funciona en Tiempo de Ejecución)

### Paso 1: Autenticación del Pod mediante ServiceAccount
Cuando el Pod arranca en Kubernetes, monta automáticamente su token JWT de `ServiceAccount`. El agente de Vault utiliza ese token para solicitar autenticación contra HashiCorp Vault mediante el método de autenticación de Kubernetes (`auth/kubernetes`).

### Paso 2: Verificación con la TokenReview API
Vault recibe el token JWT del Pod, pero no confía a ciegas en él. Vault contacta al **API Server de Kubernetes** a través de la **TokenReview API** y pregunta:
> *"¿Este token pertenece a un Pod real, en este Namespace, con esta ServiceAccount?"*

Kubernetes valida la firma y responde afirmativamente.

### Paso 3: Asignación de Políticas en Vault
Vault mapea la `ServiceAccount` y el `Namespace` del Pod con una **política de acceso** definida en Vault. Si el Pod tiene permiso, Vault le emite un token de cliente con acceso únicamente a las rutas de secretos que le corresponden.

### Paso 4: Inyección automática mediante Webhook
Cuando el manifiesto del Pod incluye anotaciones (`annotations`) de Vault, el **Vault Agent Injector** intercepta la creación del Pod e inyecta dos contenedores auxiliares:
1. **Init Container:**
   * Arranca primero.
   * Se autentica en Vault.
   * Descarga el secreto solicitado.
   * Escribe el secreto en un volumen compartido montado en memoria RAM (`tmpfs`).
   * Termina su ejecución exitosamente.
2. **Sidecar Container (Vault Agent):**
   * Arranca junto al contenedor principal de la aplicación.
   * Mantiene viva la sesión de Vault (token renewal).
   * Si el secreto cambia o expira en Vault, lo vuelve a descargar y sobreescribe el archivo en memoria (rotación dinámica).

### Paso 5: La Aplicación consume el Secreto de Forma Transparente
El contenedor principal de la aplicación arranca y simplemente lee el archivo con la credencial desde `/vault/secrets/` (en memoria RAM):
* **Cero dependencias:** La aplicación no necesita tener SDKs ni librerías de HashiCorp Vault.
* **Cero secretos en disco:** El secreto reside en memoria volátil (`tmpfs`), desapareciendo si el Pod se apaga.
* **Cero secretos en Git:** El manifiesto de Kubernetes no contiene contraseñas.

---

## 4. Ejemplo Práctico en Manifiesto de Kubernetes

En Kubernetes, todo este mecanismo se activa decorando el Deployment con **anotaciones**:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mi-aplicacion
  namespace: produccion
spec:
  replicas: 1
  template:
    metadata:
      annotations:
        # 1. Le indica al webhook inyectar el Vault Agent
        vault.hashicorp.com/agent-inject: "true"
        
        # 2. El rol configurado en Vault para esta app
        vault.hashicorp.com/role: "app-role"
        
        # 3. La ruta del secreto en Vault y el nombre del archivo de destino
        vault.hashicorp.com/agent-inject-secret-database-config.txt: "secret/data/db"
    spec:
      serviceAccountName: app-service-account
      containers:
        - name: app
          image: mi-app:1.0
          # La app simplemente lee el archivo inyectado en RAM:
          command: ["sh", "-c", "cat /vault/secrets/database-config.txt && iniciar-app"]
```

---

## 5. Ventajas Principales Destacadas en el Video

| Aspecto | Sin Vault en Kubernetes | Con HashiCorp Vault + Kubernetes |
| :--- | :--- | :--- |
| **Almacenamiento** | Objeto Secret en `etcd` (base64). | Cifrado centralizado en Vault. |
| **Exposición en Manifiestos** | Contraseñas o referencias directas en YAML. | Solo anotaciones que indican qué rol y ruta leer. |
| **Consumo en la App** | Requiere variables de entorno o SDKs. | Lectura transparente desde un archivo en memoria (`tmpfs`). |
| **Rotación de Claves** | Manual: requiere recrear pods o secrets. | Automática: el Sidecar actualiza el archivo en caliente. |
| **Auditoría** | Difícil saber qué pod accedió a qué clave. | Registro de auditoría centralizado en Vault con cada petición. |
