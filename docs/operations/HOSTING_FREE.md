# Alojamiento de pruebas: presupuesto inicial 0 USD

Revisión documental: **15 de octubre de 2026**. La arquitectura fue desplegada y probada
el 5 de octubre; no se recertifica aquí disponibilidad remota a la fecha de revisión.

- Servicio: `horizonte-demo`, Render Free; repositorio Horizonte, rama `codex/v1-hosted`.
- URL: https://horizonte-demo.onrender.com.
- [Panel](https://dashboard.render.com/web/srv-db1qp6u0tbcc73c34ht0).
- PostgreSQL Supabase Session pooler con TLS; esquema de aplicación privado `horizonte`.
- React servido por Django/WhiteNoise, sesión y API bajo el mismo origen HTTPS.
- Un supervisor inicia Gunicorn y cola PostgreSQL: no necesita Redis ni worker de pago.
- Cliente Windows consume el servidor; no instalar Docker en el equipo del usuario.

## Operación y límites

- Aceptar suspensión por inactividad y espera al reactivar. Mientras duerme no procesa jobs.
- No hay keepalive ni cron de llamadas. No habilitar servicios/planes de pago sin autorización.
- Auto-deploy se dejó desactivado en la configuración histórica: comprobar el estado real
  antes de desplegar para no duplicar una publicación automática.
- Build: `bash scripts/build-hosted.sh`; start: `python scripts/start-hosted.py`.
- Variables y cuidados de secretos: [manual técnico](../TECHNICAL_MANUAL.md).
- Recuperación real por correo pendiente de proveedor/remitente y recepción comprobada.
- Respaldo [manual](HOSTED_BACKUP.md), nunca diario automático.
- La política gratuita puede cambiar; verificar condiciones del proveedor antes de crear
  recursos nuevos. Este documento no garantiza permanencia ni disponibilidad del 99 %.

## Verificación tras un despliegue

- Revisar CI y el despliegue concreto hasta estado terminal; no reiniciarlo por un timeout de consulta.
- Comprobar Inicio/estáticos, salud, sesión y un flujo de importación con datos de prueba.
- Consultar trabajo hasta completado y cerrar sesión. No deducir éxito del worker de un HTTP 200.
- Revisar [aceptación de escritorio](../acceptance/DESKTOP_ACCEPTANCE.md) y
  [conectividad](../acceptance/QA_CONNECTIVITY.md).

El historial de creación, variables incompletas, despliegues fallidos y recuperaciones se
conserva en [archivo del 5 de octubre](../archive/2026-10-05/HOSTING_FREE.md).
