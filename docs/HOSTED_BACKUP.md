# Respaldo alojado sin Docker

Por decisión del usuario, no se activa respaldo diario alojado. Se conserva el respaldo
manual y la verificación de restauración; no existe la tarea `Horizonte Hosted Backup`.
El script histórico para Docker permanece disponible pero no fue activado en este trabajo.

`scripts/hosted_backup.py` usa clientes nativos `pg_dump` y `pg_restore`. No necesita servidor
PostgreSQL local ni Docker. Necesita instalar clientes compatibles con la versión del servidor,
credenciales de lectura/esquema y acceso de red al Session pooler.

## Comprobación del 5 de octubre de 2026

Respaldo real del esquema `horizonte` de Supabase completado con clientes PostgreSQL 18,
tras autorización explícita para guardar sus datos localmente sin cifrar. Archivo de 238.147 bytes
en `.local-backups/horizonte-20261005T150254Z-eefff7b7.dump`, ignorado por Git.
El cliente `pg_restore --list` comprobó la legibilidad del archivo custom.
SHA-256: `eb9ecd8c438a21f2d6512f29633e0a57071a6c5b2863e07a3d73bb84a81be76c`.
Manifiesto JSON adjunto: `archive_list_verified=true`, `restore_verified=false`, `encrypted=false`.
No se modificó la base alojada. Restauración estructural posteriormente verificada con
`scripts/verify_local_restore.py`: clúster PostgreSQL 18 temporal en `.local-backups`, acceso
solo por localhost con contraseña aleatoria, 32 tablas restauradas en una transacción y cero
restricciones pendientes de validación. Conteos por tabla y checksum están en el manifiesto
local `.restore.json`; el clúster quedó apagado. No ejecuta workers ni correos.
El recorrido funcional Django también fue comprobado en una nueva restauración: migraciones
vigentes, sesión con CSRF y cuenta QA existente, consultas de cuentas/movimientos/histórico/
facturas/obligaciones y dashboard de 30/60/90 días, cierre de sesión y rechazo posterior.
El resultado se registra en `functional` del manifiesto `.restore.json`. Es un Client Django,
sin navegador ni workers; no demuestra UI Electron ni entrega de correo.
El respaldo automático sigue pendiente; este ensayo no demuestra RNF-08 completo.

```powershell
.venv\Scripts\python.exe scripts/verify_local_restore.py .local-backups/horizonte-20261005T150254Z-eefff7b7.dump --pg-bin "C:\Program Files\PostgreSQL\18\bin"
```

Para incluir el recorrido funcional de la cuenta QA, añadir
`--qa-account .local-logs/remote-qa-account.json`. Este archivo contiene credenciales privadas
y queda fuera de Git. La herramienta no las imprime; solo conecta al clúster temporal local.

```powershell
.venv\Scripts\python.exe scripts/hosted_backup.py --env-file .env.hosted --pg-bin "C:\Program Files\PostgreSQL\18\bin"
```

La ruta es un ejemplo; usar la instalación real compatible. También se pueden proporcionar las
variables mediante el entorno y omitir `--env-file`, o usar clientes en PATH y omitir `--pg-bin`.
El lector del archivo admite pares literales `POSTGRES_*=valor` y comillas exteriores simples o
dobles; no ejecuta el archivo ni expande variables. No admite comentarios al final de un valor.

- Requiere host, BD, usuario y contraseña; SSL require/verify-ca/verify-full. Esquema exacto
  validado, por defecto `horizonte`. No permite comodines para ampliar silenciosamente el dump.
- No hereda variables `PG*` del equipo: servicio, hostaddr, opciones o certificados ajenos
  no deben cambiar la conexión elegida. Puerto entre 1 y 65535; `POSTGRES_DB` debe ser nombre,
  no URI/cadena de conexión. Certificado raíz opcional mediante `POSTGRES_SSLROOTCERT`;
  para verify-ca/verify-full preparar la confianza requerida por el cliente PostgreSQL.
  Referencia: [variables de libpq](https://www.postgresql.org/docs/current/libpq-envars.html).
- Ejecuta dump custom del esquema con datos, sin propietarios ni ACL, y luego `pg_restore --list`.
  Archivo parcial no se promociona si falla. Genera nombre único en `.local-backups/`, ignorado por Git.
- La contraseña se transmite al proceso mediante entorno, no argumentos ni logs. El entorno del
  proceso sigue siendo sensible; no compartir diagnósticos que lo impriman.
- Manifiesto JSON: fecha, tamaño, SHA-256, esquema y límites explícitos `restore_verified=false`
  y `encrypted=false`. No incluye host, usuario ni contraseña.
- Validar el índice demuestra legibilidad del archivo, no integridad funcional de una restauración.
- Seleccionar un esquema no incluye automáticamente roles, objetos de otros esquemas, configuración
  de Supabase, servicios externos o archivos de la aplicación. Revisar dependencias antes de restaurar.
- El archivo contiene información privada y **no está cifrado**. Controlar permisos, cifrar la copia
  externa y definir retención antes de respaldar datos reales. La herramienta no implementa ese circuito.

Pendiente: comprobar interfaz de usuario sobre la restauración, cifrar/retener
copias y automatizar su ejecución. La verificación crea un clúster nuevo y nunca sobrescribe
una base existente. Los archivos del clúster apagado permanecen en `.local-backups`, ignorados
por Git, y contienen la misma información privada que el respaldo autorizado.

Contrato y fallos comprobados con procesos simulados; no se atribuye prueba PostgreSQL real a esos mocks.
Opciones contrastadas con [pg_dump oficial](https://www.postgresql.org/docs/current/app-pgdump.html)
y [pg_restore oficial](https://www.postgresql.org/docs/current/app-pgrestore.html).
