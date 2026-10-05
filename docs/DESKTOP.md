# Distribución de escritorio en línea

El cliente Electron abre la interfaz React alojada junto a Django bajo el mismo origen HTTPS.
Las cookies de sesión HttpOnly y CSRF conservan su comportamiento web. No hay claves de BD ni
credenciales de proveedores en el instalador. El equipo usuario necesita conexión al servidor;
no necesita Python, Node, Redis, PostgreSQL ni Docker.

## Construcción y prueba

- Desde `desktop`: `npm ci`, `npm test`, `npm run dist`.
- El instalador Windows se genera en `desktop/release/`. En el primer arranque se configura el
  origen HTTPS del servidor, por ejemplo `https://horizonte.example.com`.
- La dirección queda en `server.json` en la carpeta de datos de usuario Electron. Cambiarla desde
  el menú Servidor borra el almacenamiento del origen anterior para separar sesiones.
- Solo en desarrollo (`npm start`) se permite HTTP de localhost para probar contra Django que
  sirve el build React en el puerto 8000. Los binarios empaquetados exigen HTTPS.
- Si falla la navegación, el aviso ofrece reintentar, configurar servidor o cerrarlo. Explica
  la posible demora tras una suspensión del servicio gratuito. No reintenta automáticamente
  ni evita que el proveedor suspenda el servicio. Respuestas HTTP de error que carguen una
  página del proveedor todavía requieren revisión y reintento desde el menú Servidor.
- El cliente remoto no expone APIs de Node ni puente IPC; su proceso renderizado usa sandbox y
  bloqueo de navegación a otros orígenes. El formulario local de configuración usa un puente
  mínimo validado en el proceso principal.
- Ambas ventanas deniegan consultas y solicitudes de permisos, y permisos de dispositivos.
  La prueba de arranque consulta ubicación/cámara/micrófono en Chromium y exige `denied`
  en configuración. Falta verificar el recorrido remoto completo y APIs de dispositivos.
  Electron requiere combinar handlers de consulta y solicitud:
  [documentación de sesión](https://www.electronjs.org/docs/latest/api/session#sessetpermissioncheckhandlerhandler).

## Infraestructura pendiente de autorización y despliegue

**Configuración vigente de pruebas:** presupuesto 0 USD. Seguir `HOSTING_FREE.md` y `render.yaml`:
web y cola persistente en un servicio Render Free, PostgreSQL Supabase Free. El esquema Celery/Redis
descrito a continuación sigue disponible como alternativa, pero no se contratará para estas pruebas.

Hace falta servicio Linux Python para Django/Gunicorn, worker Celery, PostgreSQL y broker compatible
con Redis. Supabase puede suministrar PostgreSQL (con puerto/SSL configurables), pero por sí solo no
aloja este backend y worker. Firebase implicaría reemplazar parte de la persistencia y no es necesario.

El build remoto ejecuta `bash scripts/build-hosted.sh`. En la configuración gratuita el inicio
ejecuta `python scripts/start-hosted.py`: prepara el esquema y migraciones y supervisa Gunicorn
y `run_background`, con `BACKGROUND_MODE=database`. No requiere Redis.

En la alternativa Celery, el web ejecuta
`gunicorn --chdir backend config.wsgi:application --bind 0.0.0.0:$PORT` y el worker
`celery --workdir backend -A config.celery:app worker --loglevel=info`.
Aplicar `python backend/manage.py migrate` como paso de release antes del arranque del web.
El build React queda en `frontend/dist`, servido por WhiteNoise; `/` no requiere sesión.
`/api/health/` comprueba la BD; no comprueba la salud del worker ni certifica el recorrido funcional.

Variables: `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY` propio, `DJANGO_ALLOWED_HOSTS`,
`DJANGO_CSRF_TRUSTED_ORIGINS`, `FRONTEND_URL` y `DJANGO_TRUST_PROXY=1` solo detrás de un proxy
que sobrescriba la cabecera de protocolo; `POSTGRES_HOST/PORT/DB/USER/PASSWORD/SSLMODE`,
`CELERY_BROKER_URL` solo para la alternativa Celery. En Render Free el correo usa API HTTPS:
`RESEND_API_KEY`, `DEFAULT_FROM_EMAIL`, `EMAIL_BACKEND=config.email.EmailBackend`.
No guardar estos secretos en Git ni en Electron.

## Criterio de aceptación aún por verificar

- Instalar en Windows limpio, configurar servidor HTTPS y visitar Inicio sin sesión.
- Registro/acceso, importación CSV/XML procesada por worker y resultados en dashboard.
- Recarga, cierre/reapertura, logout, rechazo de otro tenant, servidor caído y cambio de origen.
- Actualización del instalador, firma/distribución y recuperación de datos del servicio remoto.

Preparar un instalador no cierra los pendientes del modelo predictivo y del alcance académico;
consultar `ROADMAP_ENTREGABLES.md`. El objetivo completo sigue en ejecución.

Recorrido de uso y aceptación: [USER_MANUAL.md](USER_MANUAL.md).
