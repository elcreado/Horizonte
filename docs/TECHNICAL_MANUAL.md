# Manual técnico vigente

Revisión: **18 de octubre de 2026**. Arquitectura inspeccionada en código; estado remoto
histórico del 5 de octubre, sin recertificar disponibilidad hoy. [Brechas](ESTADO_Y_PENDIENTES.md).

## Componentes

- React/TypeScript/Vite: build `frontend/dist`; Django/WhiteNoise sirve HTML y estáticos.
  `/api/` comparte origen en el alojamiento. Desarrollo Vite usa proxy hacia Django.
- Django/DRF: sesión HttpOnly + CSRF; autenticación/membresía y roles por empresa.
  Inicio, registro y acceso públicos no hacen públicas las finanzas.
- PostgreSQL: dominio, sesiones, auditoría, cola y pronósticos guardados. COP y corte
  compatible para consolidación; importes Decimal, cadenas en JSON.
- `BACKGROUND_MODE=database`: cola `BackgroundTask` y comando `run_background`.
  Celery/Redis sigue como alternativa de desarrollo; no es requisito del usuario final.
- Electron/NSIS: cliente Windows x64 en línea. No contiene Python, backend ni claves de BD;
  exige HTTPS empaquetado, Node oculto, sandbox y permisos denegados. No ofrece modo offline.

## Entorno local Docker — 18 de octubre de 2026

`docker compose up --build -d --wait` inicia PostgreSQL 16, Redis 7, migraciones,
Django en 8000, Celery y Vite en 5173. El proxy usa `API_PROXY_TARGET=http://backend:8000`
solo dentro del contenedor; fuera de Docker conserva localhost. `BACKGROUND_MODE=celery`
y `DJANGO_LOCAL_WORKER=0` evitan iniciar además el worker de cola BD.

El volumen `postgres_data` conserva su nombre y credenciales locales. No se carga
`.env.hosted`, no se cambia la configuración remota ni se copia SQLite a PostgreSQL.
Los Dockerfiles instalan las dependencias versionadas; `.dockerignore` excluye entornos,
secretos, bases SQLite y artefactos locales. Ver [arranque y pruebas](TESTING.md).

## Alojamiento y configuración

- Render Free: build `bash scripts/build-hosted.sh`, inicio `python scripts/start-hosted.py`.
  Supervisor inicializa esquema/migraciones y ejecuta Gunicorn y worker BD separados.
- Supabase: PostgreSQL Session pooler con TLS, esquema privado de aplicación `horizonte`.
- Variables: `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY`, `POSTGRES_HOST/PORT/DB/USER/PASSWORD`,
  `POSTGRES_SSLMODE`, `POSTGRES_SCHEMA`, `FRONTEND_URL` y configuración de proxy/orígenes.
  No usar SQLite efímero como sustituto silencioso de BD remota.
- `.env.hosted` es privado e ignorado; Django no lo carga automáticamente. No imprimir
  credenciales ni copiarlas a React/Electron. Gestionarlas en el servidor.
- Correo HTTPS preparado con `EMAIL_BACKEND=config.email.EmailBackend`, `RESEND_API_KEY`
  y `DEFAULT_FROM_EMAIL`; falta verificar entrega real. No usar mocks como prueba de recepción.
- Condiciones y pasos: [operación gratuita](operations/HOSTING_FREE.md). No crear recursos
  pagados ni llamadas de keepalive. La suspensión detiene también el procesamiento de cola.

## Trabajos e integridad

- En modo BD, trabajo de dominio y mensaje se crean atómicamente; fallos de cola devuelven
  error genérico y no deben dejar trabajos huérfanos.
- Lease de quince minutos, reintentos limitados a tres; argumentos se eliminan al terminar.
  Los reintentos necesitan idempotencia; no prometer entrega exactamente una vez del correo.
- Worker revalida rol/consentimiento. Revisar logs y lease antes de cambiar estados manualmente.
- [Cola](operations/BACKGROUND_WORKER.md), [diagnóstico](operations/QUEUE_DIAGNOSTICS.md).

## Pruebas y distribución

- Ejecutar comandos de [TESTING.md](TESTING.md) con BD aislada; CI PostgreSQL usa instancia efímera.
- `npm --prefix desktop ci`, `npm --prefix desktop test`, `npm --prefix desktop run dist`.
  [Binario actual y checksum](desktop/DESKTOP_RELEASE.md); nuevas compilaciones pueden cambiar huella.
- [Aceptación Windows](acceptance/DESKTOP_ACCEPTANCE.md): instalación, sesión, importaciones,
  cierres/reaperturas, recuperación de red y desinstalación. Build no sustituye ese recorrido.
- `/api/health/` prueba BD con `SELECT 1`; no acredita worker, correo ni UI.
- Diagnósticos deben registrar operación/hora/ID sin contraseñas, facturas ni tokens.
- [Seguridad](security/THREAT_MODEL.md) y [administración](operations/PLATFORM_ADMIN.md).

## Respaldo y documentación

- Respaldo manual: `scripts/hosted_backup.py`, clientes PostgreSQL compatibles y autorización
  para destino/datos. Restauración con `verify_local_restore.py` en clúster aislado.
- Hubo ensayo real de copia y restauración; cifrado, retención y copia externa siguen pendientes.
  [Evidencia y procedimiento](operations/HOSTED_BACKUP.md). No programar respaldo diario.
- [API](API_DOCUMENTATION.md), [OpenAPI parcial](openapi-inventory.json),
  [investigación](research/README.md). Reportes nuevos se guardan en `docs/research/`.
- El manual anterior, con pasos de preparación ya superados, queda en
  [archivo](archive/2026-10-05/TECHNICAL_MANUAL.md).


## V1 manual: migración y cálculo inicial

Aplicar `python backend/manage.py migrate` antes de iniciar esta rama. `banking.0011_manualentry` crea recibos de solicitud con UUID único por empresa y vínculo uno a uno al movimiento. No altera los datos históricos ni el saldo. El servicio bloquea membresía, empresa y cuenta; creación, recibo, auditoría y retirada de cobertura ocurren dentro de una transacción.

`manual_average` calcula con Decimal el promedio del residual de todo el historial registrado hasta el corte, confirmado completo y con mínimo siete días, redondeado a centavos, y lo repite 30/60/90 días. Suma compromisos futuros desde el saldo declarado; no vuelve a sumar el historial. No se presenta como modelo validado. Las reglas de los métodos anteriores se conservan.

El frontend conserva el UUID y los datos del envío ante respuesta incierta mientras el formulario permanece montado. Tras confirmación crea una solicitud nueva. Una recarga descarta ese recibo local: comprobar historial antes de volver a capturar si la respuesta se perdió. Secciones del dashboard usan claves React distintas por componente/empresa para impedir duplicados al refrescar.


## Cola automática de desarrollo y compromisos mensuales

`manage.py runserver` usa `BACKGROUND_MODE=database` si no se especificó otro modo. El comando local de accounts levanta un subprocess `run_background` solo con DEBUG y cola de BD; no ejecuta importaciones dentro de HTTP. La autorecarga inicia el worker dentro del proceso servidor y lo detiene al cerrar. `DJANGO_LOCAL_WORKER=0` permite gestionar el worker por separado. El alojamiento conserva su supervisor independiente.

Aplicar migración forecast 0007. `MonthlySchedule` persiste la regla y `MonthlyOccurrence` vincula fecha/obligación única. Consultas financieras amplían vencimientos con bloqueo por empresa; no recrean obligaciones canceladas o conciliadas. Meses sin día 29–31 usan el último día. Se generan hasta doce meses al crear y se mantiene una ventana futura acotada al consultar; la regla sin fecha final continúa activa. No ejecuta pagos.

El Resumen ahora estima flujo variable desde todo el historial disponible, descontando importes conciliados; mínimo siete días en el denominador. No requiere declaración de completitud y muestra el supuesto de días vacíos, a diferencia del pronóstico avanzado que mantiene su cobertura explícita. Saldos declarados incluyen historial hasta el corte; solo el flujo posterior incrementa/reduce caja disponible. Las alertas guardadas congelan esta trayectoria como summary_v2.
