# Manual técnico de Horizonte

Revisión: 4 de octubre de 2026. Configuración objetivo: escritorio Windows conectado a Django
en Render Free y PostgreSQL en Supabase Free; presupuesto 0 USD. Preparado en código, todavía
sin despliegue remoto verificado. Consultar `IMPLEMENTATION_STATUS.md` para el alcance pendiente.

## Componentes y límites

- React/TypeScript genera `frontend/dist`. Django sirve `/` y WhiteNoise los archivos del build.
  Las llamadas `/api/` comparten origen; no se necesita guardar tokens ni claves en el cliente.
- Django/DRF autentica con sesiones, cookies HttpOnly y CSRF. Los endpoints financieros requieren
  autenticación y membresía por empresa. Inicio y los flujos de acceso son públicos.
- PostgreSQL conserva datos financieros, sesiones, trabajos y ejecuciones de pronóstico.
  `Decimal` y cadenas preservan los importes; las fechas de negocio son ISO y la zona es Bogotá.
- `BACKGROUND_MODE=database` utiliza `BackgroundTask` y el comando `run_background`. La alternativa
  `celery` conserva Celery/Redis; no forma parte del despliegue gratuito preparado.
- Electron carga el origen HTTPS con aislamiento de Node y sandbox. No aloja Django ni trabaja
  sin conexión. No modificar el cliente para introducir credenciales de PostgreSQL.

## Preparar un despliegue

- Crear cuentas Free, un proyecto Supabase de prueba y un repositorio que Render pueda leer.
  No habilitar upgrades ni excesos de pago. Ver las instrucciones de `HOSTING_FREE.md`.
- Configurar `POSTGRES_HOST`, `POSTGRES_PORT=5432`, `POSTGRES_DB`, `POSTGRES_USER`,
  `POSTGRES_PASSWORD`, `POSTGRES_SSLMODE=require` y `POSTGRES_SCHEMA=horizonte` con los datos
  del Session pooler. Mantener `horizonte` fuera de los esquemas expuestos de la Data API.
- Configurar `DJANGO_DEBUG=0` y una `DJANGO_SECRET_KEY` propia. El proceso falla si se intenta
  usar la clave predeterminada de desarrollo en producción.
- Producción también rechaza la ausencia de `POSTGRES_HOST`, evitando guardar datos en SQLite
  efímero por un error de configuración. `FRONTEND_URL` (o la URL externa de Render) debe ser
  un origen HTTPS sin credenciales, ruta, query o fragmento; localhost se rechaza para evitar
  enlaces de recuperación dirigidos al equipo del usuario.
- `render.yaml` prepara un único servicio web Free. El build ejecuta
  `bash scripts/build-hosted.sh`; el inicio ejecuta `python scripts/start-hosted.py`.
- El supervisor primero ejecuta `initialize_schema` y `migrate --noinput`; después inicia
  Gunicorn (un worker, dos threads) y `run_background` en procesos separados. Si uno termina
  inesperadamente, detiene el otro y sale con error para permitir recuperación del servicio.
- Render proporciona el hostname y URL externa, utilizados por la configuración. Para un
  dominio propio configurar `DJANGO_ALLOWED_HOSTS` y `FRONTEND_URL`; autorizar orígenes CSRF
  únicamente si el flujo los necesita. No usar comodines para resolver errores de acceso.
- `DJANGO_TRUST_PROXY=1` solo detrás de un proxy que sobrescriba la cabecera de protocolo.
  Producción activa cookies Secure, redirección HTTPS y CSP. Validar login/CSRF en el origen real.
- Para correo usar `EMAIL_BACKEND=config.email.EmailBackend`, `RESEND_API_KEY` y
  `DEFAULT_FROM_EMAIL`. La implementación usa HTTPS, timeout de diez segundos y mensajes de texto.
  La aceptación de la API no demuestra entrega; falta probar con un destinatario autorizado.
- `.env.hosted` es almacenamiento local ignorado por Git; Django no lo lee automáticamente.
  Copiar valores al gestor de variables del alojamiento sin imprimir ni publicar secretos.
- No ejecutar `seed_demo` en producción: el comando se restringe a desarrollo. Registrar una
  cuenta de prueba desde la aplicación y cargar archivos sintéticos para la aceptación remota.

## Cola y recuperación de tareas

- CSV/XLSX, XML y Mock Bank crean trabajo y mensaje atómicamente en modo `database`. El worker
  revalida permisos y consentimiento; aceptar el HTTP no garantiza terminar la operación.
- Si falla el guardado del mensaje de cola, se revierte el trabajo y la API responde 503 sin
  detalles privados de la BD. Las pruebas HTTP CSV/XML comprueban que no quedan huérfanos.
  Reintentar cuando el servicio esté disponible; una respuesta de aceptación sigue requiriendo
  consultar el estado final del trabajo.
- La cola reclama un mensaje con lease de quince minutos. Una interrupción permite reclamarlo
  tras expirar. Reintenta hasta tres veces; los fallos normales esperan treinta segundos por
  número de intento. El proceso consulta cada diez segundos cuando no hay trabajo.
- Al terminar se borran argumentos del mensaje. Una importación terminada elimina su contenido.
  Si los reintentos se agotan, el trabajo financiero pendiente se marca fallido para permitir
  solicitarlo de nuevo. No editar estados a mano para forzar una segunda ejecución.
- La cola es de entrega con posibles repeticiones. Las tareas financieras tienen controles de
  idempotencia; un corte tras enviar correo puede producir mensajes duplicados.
- Mientras Render está suspendido no se procesan tareas. Se acepta el arranque en frío y no hay
  cron de llamadas configurado. Las pruebas de interrupción reales en Linux/PostgreSQL siguen pendientes.

## Comprobaciones de operación

- Login/registro y recuperación/reset usan contadores persistentes en `RateLimitBucket`, con
  identidad HMAC y ventanas fijas. No dependen de Redis/caché local y sobreviven reinicios.
  `python backend/manage.py purge_rate_limits` elimina solo ventanas vencidas; ejecutar como
  mantenimiento administrativo periódico. No imprime IP ni usuarios. Concurrencia PostgreSQL
  e identificación IP del proxy quedan pendientes de prueba. No es un bloqueo global por
  cuenta objetivo ni protección antiabuso integral.

- Consultar `/api/health/`: comprueba la conexión con BD mediante `SELECT 1`. Una respuesta sana
  no certifica la cola, el correo, las migraciones completas ni el recorrido del usuario.
- Abrir `/` sin sesión, registrar/acceder y cargar un archivo pequeño; comprobar que llega a
  completado. Esta comprobación sí atraviesa web, sesión, BD y worker.
- Si una carga queda pendiente, comprobar logs del supervisor y worker y si el servicio está
  dormido. Tras una interrupción respetar el lease antes de concluir que no se recupera.
- Si falla el acceso a BD, revisar pooler, SSL, credenciales, disponibilidad del proyecto y
  existencia/permisos del esquema. No cambiar a `public` como solución sin revisar la exposición.
- Si faltan archivos de frontend, reconstruir. El endpoint de Inicio devuelve 503 cuando falta
  `index.html`; un health sano no demuestra que el build esté disponible.
- Si fallan cookies/login, revisar origen HTTPS y configuración del proxy. No desactivar CSRF,
  `webSecurity` o Secure cookies para resolver un problema de despliegue.
- Registrar incidentes con hora, operación e ID del trabajo; excluir claves, contraseñas, archivos
  financieros y enlaces de recuperación. Los logs del proveedor pueden tener su propia retención.

## Respaldos y restauración

Respaldo alojado sin Docker preparado: `scripts/hosted_backup.py`; instrucciones y límites en
`HOSTED_BACKUP.md`. Requiere clientes PostgreSQL nativos compatibles y credenciales. Su contrato
se probó con mocks; copia/restauración remotas y cifrado aún pendientes.

El respaldo existente `scripts/db-backup.py` utiliza **Docker Compose local** y herramientas de
PostgreSQL 16 para la BD `liquidity`. `--restore-check` restaura en una BD temporal y consulta
conteos de migraciones, empresas y movimientos; nunca restaura sobre la BD activa. Se comprobó
en el entorno local anterior. No respalda Supabase y no elimina la dependencia de Docker para
esa herramienta administrativa; el cliente de escritorio sí prescinde de Docker.

- Antes de una migración remota, obtener un respaldo del esquema de aplicación usando herramientas
  PostgreSQL compatibles con el servidor y credenciales administrativas de acceso limitado.
- Mantener archivo, fecha, tamaño y checksum; almacenar una copia externa cifrada y controlar
  retención. Este circuito remoto no está implementado ni ensayado aún.
- Restaurar primero en una BD/proyecto aislado autorizado, comprobar conteos e integridad y
  ejecutar el recorrido de aceptación. No atribuir éxito a la mera existencia de un dump.
- No restaurar sobre producción ni revertir migraciones destructivas sin un plan de recuperación
  revisado. Un rollback de código no revierte automáticamente los datos.
- La política de backups del proveedor gratuito no se considera prueba de recuperación de la
  aplicación. El simulacro remoto es requisito pendiente del entregable.

## Validación y distribución

Desde la raíz, con el entorno Python preparado:

```powershell
.venv\Scripts\ruff.exe check backend
.venv\Scripts\ruff.exe format --check backend
.venv\Scripts\python.exe backend/manage.py makemigrations --check --dry-run
.venv\Scripts\python.exe backend/manage.py test backend/tests
npm --prefix frontend run build
npm --prefix desktop test
```

La suite normal usa SQLite si no se proporciona PostgreSQL. Las pruebas concurrentes específicas
se omiten allí; pasar esta suite no demuestra concurrencia ni despliegue PostgreSQL. La CI actual
valida backend, frontend y el contrato de dirección del escritorio; la ejecución remota y la
distribución completa siguen sin verificarse. La CI no instala ni abre Electron.
Existe un job adicional con PostgreSQL 16 efímero en el runner para ejecutar también las pruebas
concurrentes de importación y límites. No usa la BD Supabase ni credenciales reales. No ha sido
ejecutado en GitHub; su configuración no es evidencia de aprobación. No activar consumo facturado
de minutos de Actions con el presupuesto de 0 USD.

- Construir el escritorio con `npm --prefix desktop ci` y `npm --prefix desktop run dist`.
- El instalador NSIS generado se conserva en `desktop/release/verified/`; no está firmado.
  Su arranque aislado se comprobó; instalación/actualización/desinstalación y sesión remota en
  equipo limpio permanecen pendientes.
- Ejecutar el recorrido de `USER_MANUAL.md`, registrar versión y evidencias, y revisar la matriz
  del alcance. No publicar como V1 terminada mientras queden requisitos explícitos sin evidencia.

## Dependencias externas aún necesarias

- Credenciales Supabase, cuenta Render y acceso al repositorio para desplegar y probar HTTPS.
- Proveedor de correo y remitente autorizado para entrega real.
- Equipo Windows limpio para validar el ciclo del instalador.
- Entorno PostgreSQL aislado y copia segura para ensayo de recuperación remota.
- Sandbox bancario y participantes/datos autorizados para integración y evaluación reales.

La aplicación no garantiza disponibilidad 99 % sobre servicios gratuitos ni precisión predictiva
calibrada: ambos requieren evidencia y siguen pendientes en `IMPLEMENTATION_STATUS.md`.
