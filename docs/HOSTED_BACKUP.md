# Respaldo alojado sin Docker

`scripts/hosted_backup.py` usa clientes nativos `pg_dump` y `pg_restore`. No necesita servidor
PostgreSQL local ni Docker. Necesita instalar clientes compatibles con la versión del servidor,
credenciales de lectura/esquema y acceso de red al Session pooler. No están disponibles en el
entorno actual; ninguna copia de Supabase ni restauración real ha sido ejecutada.

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

Pendiente: obtener clientes/credenciales, ejecutar backup real, restaurar en un destino aislado
autorizado y comprobar migraciones, conteos, integridad y recorrido de usuario. El script solo
respalda: no ofrece un comando que sobrescriba una base existente.

Contrato y fallos comprobados con procesos simulados; no se atribuye prueba PostgreSQL real a esos mocks.
Opciones contrastadas con [pg_dump oficial](https://www.postgresql.org/docs/current/app-pgdump.html)
y [pg_restore oficial](https://www.postgresql.org/docs/current/app-pgrestore.html).
