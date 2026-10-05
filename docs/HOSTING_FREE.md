# Pruebas alojadas con presupuesto 0 USD

## Estado remoto vigente

**Actualización 7c51bdc aceptada:** CI `37325123856` terminó `success`; despliegue Render
`dep-db1r8lid0e5s7391p47g` está `live`. Inicio devuelve 200 con `Cache-Control: no-store`;
el HTML referencia el nuevo paquete inicial. JS/CSS iniciales, módulos diferidos y paquete
de gráficos responden 200; `/api/health/` devuelve 200 y `status: ok`. La disponibilidad de
estos archivos no demuestra por sí sola su ejecución visual en navegador o Electron.

**Factura XML remota:** documento UBL sintético adaptado al NIT de la empresa QA,
aceptado 202 y procesado `completed`. Antes de confirmar no tenía obligación. Confirmación
201 creó una obligación pendiente de 119000,00 COP con vencimiento 15 de octubre;
repetir la confirmación devolvió 200 y el mismo ID de obligación, sin duplicarla.
No se ha verificado firma ni validación DIAN ni corpus de facturas reales.

**Mock Bank remoto:** consentimiento 201, sincronización solicitada 202 y terminada
`completed` (cero movimientos nuevos en esa segunda ejecución), revocación 200 y nueva
sincronización rechazada 409. No equivale a conexión bancaria externa. La automatización
visual sigue sin iniciar: error de sandbox Windows `apply deny-read ACLs`.

**Prueba HTTP real completada:** registro sintético 201, CSRF rechazado al escribir sin token,
CSV aceptado 202 y procesado `completed` con un movimiento, consulta de movimientos y dashboard
200. Una segunda prueba verifica cookie de sesión Secure/HttpOnly, logout 204, consulta sin
sesión 403 y nuevo login 200. Se guardaron credenciales QA únicamente en `.local-logs`, ignorado
por Git. Estas pruebas usan HTTP con cookies; no acreditan experiencia visual ni instalador.

**Arranque comprobado:** los registros remotos muestran migraciones aplicadas y Gunicorn
escuchando en el puerto 10000. Consulta HTTP pública `/` devuelve 200 HTML y `/api/auth/me/`
devuelve 403 sin sesión. La primera consulta de salud agotó el tiempo durante el arranque;
se repite posteriormente. Estos resultados no prueban registro, importación ni cliente de escritorio.

**Actualización de conexión:** `.env.hosted` ya contiene los cinco valores PostgreSQL.
Consulta `SELECT 1` autenticada y TLS activo verificados desde este equipo. Variables cargadas
en Render mediante actualización parcial, conservando la clave Django. A las 14:05 UTC había
un despliegue compilando (`dep-db1qt8942hec73du0tbg`) y otro solicitado en cola
(`dep-db1qta79nhgc739lm7g0`). La actualización de variables inició uno por sí misma;
no volver a solicitar despliegues mientras estos estén activos. Aún no se acredita servicio live,
migraciones terminadas ni prueba funcional remota.

- El usuario autorizó el espacio **Horizonte** y habilitó el repositorio público.
- Rama `codex/v1-hosted` publicada en GitHub, commit `5a626cf`.
- Servicio **horizonte-demo** creado en el workspace Horizonte el 5 de octubre de 2026,
  plan de ejecución **Free**, región Virginia, despliegue automático desactivado.
- Servicio: `srv-db1qp6u0tbcc73c34ht0`; despliegue inicial: `dep-db1qp7e0tbcc73c34kg0`.
- [Panel del servicio](https://dashboard.render.com/web/srv-db1qp6u0tbcc73c34ht0).
- URL asignada: https://horizonte-demo.onrender.com. **No acredita aplicación operativa**:
  faltan las variables PostgreSQL de Supabase y no se ha verificado arranque ni recorrido remoto.
- Se configuró una clave Django aleatoria en Render, sin publicarla en Git.
- Despliegue inicial consultado: terminó en `build_failed` a las 13:57:11 UTC del
  5 de octubre. Los registros muestran que Django rechazó la configuración por falta de
  `POSTGRES_HOST`. No se ha reintentado sin los datos de PostgreSQL ni se ha habilitado SQLite.
- Comprobación local posterior: host de Session pooler con DNS resoluble, usuario con referencia
  de proyecto y puerto 5432 presentes. Solo falta `POSTGRES_PASSWORD`. No se ha abierto una
  conexión autenticada ni trasladado estos datos incompletos a Render.
- Los apartados siguientes sobre falta de publicación/creación registran el estado anterior;
  quedan resueltos. La conexión PostgreSQL y la aceptación remota siguen pendientes.

Actualizado el 5 de octubre de 2026. No hay servicios creados. `.env.hosted` contiene claves API
de Supabase, pero faltan los datos de conexión PostgreSQL que utiliza Django. Existe el remoto
GitHub `elcreado/Horizonte`. Se verificó su HEAD remoto: todavía no contiene `render.yaml`,
`scripts/build-hosted.sh` ni `scripts/start-hosted.py`. Es necesario publicar el código preparado
antes de crear el servicio; el repositorio existente por sí solo no acredita un despliegue viable.
La revisión local no detectó modelos sin migraciones. `.gitattributes` fija finales LF para los
scripts bash; el script de compilación se normalizó para evitar errores CRLF en Linux.
Estas comprobaciones no sustituyen una compilación y arranque reales en Render.
La rama local `codex/v1-hosted` contiene el commit `3db1efb` con el código preparado.
El intento de publicación fue rechazado por la revisión automática porque la autorización no
identificaba explícitamente GitHub `elcreado/Horizonte` como destino de publicación del código
y documentación. No se publicó esta rama; queda pendiente la autorización directa del usuario.

- Render Free: una web Python sirve Django/React y un proceso separado consume la cola en BD.
  No se crea worker de pago ni Redis. Las tareas permanecen en PostgreSQL cuando el servicio se
  suspende; una ejecución interrumpida se recupera tras vencer su lease de 15 minutos.
  Trabajo y mensaje se guardan atómicamente; tras tres intentos agotados, las importaciones y
  sincronizaciones pendientes terminan como fallidas para permitir una nueva solicitud. El
  contenido del archivo se elimina al terminar. Pruebas SQLite verifican rollback y recuperación;
  falta ensayar los cortes reales del proceso en el despliegue PostgreSQL.
- Supabase Free: PostgreSQL mediante Session pooler, puerto 5432, SSL requerido. Las tablas Django
  usan el esquema `horizonte`, que debe mantenerse fuera de los esquemas expuestos por la Data API
  de Supabase. El cliente usa Django; no necesita anon key ni service-role key.
- No se habilitan upgrades ni servicios de pago. Revisar que las cuentas estén en Free y sin
  facturación automática antes del despliegue. Render puede suspender servicios al agotarse cuotas;
  la BD Supabase gratuita también tiene límites y puede pausarse por inactividad.
- Se acepta el arranque en frío de Render. No se ha configurado un cron de llamadas. Las tareas se
  procesan mientras el servicio está despierto, por ejemplo al usar la aplicación de escritorio.

## Decisión con límite estricto de 0 USD

- Mantener `plan: free` en `render.yaml`. No crear un Cron Job de Render: tiene un cargo mínimo
  de 1 USD al mes, aunque su ejecución sea breve.
- Render suspende la web tras 15 minutos sin tráfico; una solicitud posterior la reactiva y puede
  tardar aproximadamente un minuto. Aceptar esa espera para esta primera instancia.
- Las 750 horas gratuitas mensuales son compartidas por todo el workspace. Mantener una web
  despierta mediante llamadas periódicas consume esa cuota y puede afectar otros servicios.
  No se ha instalado un monitor externo ni se garantiza disponibilidad continua.
- Antes del despliegue, comprobar el consumo del workspace elegido y que no exista un método
  de pago que permita cargos por excesos de transferencia o compilación. Alcanzar cuotas debe
  detener el servicio o las compilaciones, sin contratar capacidad adicional.
- Seleccionar el workspace: están disponibles `tiktok-chat-tts` y `Tiktok-Monorepo-WEB`.
  La elección del usuario y los datos del Session pooler están pendientes.

Fuentes verificadas el 5 de octubre de 2026: [límites Free de Render](https://render.com/docs/free)
y [facturación de Cron Jobs](https://render.com/docs/cronjobs).

## Datos que debe preparar el usuario

Puedes comprobar los campos pendientes sin mostrar secretos con
`.venv\Scripts\python.exe scripts/check-hosted-config.py`. Comprueba presencia, puerto y SSL;
no acredita conexión remota, permisos ni migraciones. Devuelve código 1 si faltan datos.

1. Crear o usar cuentas **Free** de Render y Supabase.
2. Crear un proyecto Supabase para datos sintéticos. En **Connect → Session pooler**, copiar host,
   puerto, usuario y nombre de BD. La contraseña es la del proyecto, no una clave API.
3. Guardar esos valores en `.env.hosted` en la raíz del proyecto (archivo ignorado por Git):

```dotenv
POSTGRES_HOST=host-del-session-pooler
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres.referencia-del-proyecto
POSTGRES_PASSWORD=contraseña-de-la-base
POSTGRES_SSLMODE=require
POSTGRES_SCHEMA=horizonte
BACKGROUND_MODE=database
# Para crear/configurar el servicio mediante API, si eliges esa vía:
# RENDER_API_KEY=token-del-panel-Render
```

4. Avisar cuando el archivo esté listo. No pegar contraseñas ni tokens en el chat. Django no carga
   este archivo automáticamente; los scripts de configuración deben leerlo sin imprimir secretos.
5. Dar acceso al repositorio desde Render o facilitar el repositorio que alojará este código. El
   blueprint `render.yaml` describe únicamente un servicio web Free; el despliegue aún no está probado.

En producción, Django exige `POSTGRES_HOST` y un origen HTTPS para `FRONTEND_URL` (o
`RENDER_EXTERNAL_URL` proporcionada por Render). No arranca con SQLite efímero ni enlaces de
recuperación hacia localhost. Para dominio propio indicar el origen completo sin rutas.

## Correo y aceptación

Render gratuito bloquea los puertos SMTP habituales. Para recuperación real se necesita un proveedor
de correo con API HTTPS gratuita y sus credenciales. Ya está implementado el backend de Resend con
pruebas simuladas; no se ha enviado correo real ni configurado una cuenta. El correo de desarrollo
no representa entrega real a usuarios.

- Crear una cuenta Resend Free y mantener desactivados los excesos de pago y cualquier upgrade.
- Guardar `RESEND_API_KEY` y `DEFAULT_FROM_EMAIL` en `.env.hosted`; en Render configurar además
  `EMAIL_BACKEND=config.email.EmailBackend`. No compartir la clave en el chat.
- Para destinatarios generales se requiere un remitente de dominio verificado. Si no dispones de
  dominio, mantener la recuperación como prueba limitada del proveedor hasta verificar esa
  configuración; no comprar un dominio con el presupuesto de 0 USD.
- La aceptación por API no garantiza llegada a bandeja de entrada. Falta comprobar entrega,
  caducidad del enlace y cambio de contraseña desde el servicio remoto.
- La cola puede reintentar tras un fallo; un corte después del envío puede producir un correo
  duplicado. Nunca registra la respuesta del proveedor ni el enlace privado.

Referencia de configuración: [API de correo Resend](https://resend.com/docs/api-reference/emails/send-email)
y [plan gratuito y política de excesos](https://resend.com/pricing).

Se comprobará en el entorno remoto: esquema/migraciones, Inicio sin sesión, registro/login/CSRF,
CSV/XLSX, XML, Mock Bank, obligaciones, cola interrumpida y reanudada, empresas aisladas, cliente de
escritorio, persistencia tras suspensión y restauración de datos. El instalador por sí solo no prueba
este recorrido ni la precisión del modelo.

Fuentes: [Render Free](https://render.com/docs/free), [Supabase Free](https://supabase.com/pricing)
y [conexiones PostgreSQL de Supabase](https://supabase.com/docs/guides/database/connecting-to-postgres).
