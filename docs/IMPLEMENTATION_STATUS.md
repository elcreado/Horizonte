# Estado del alcance — 25 de septiembre de 2026

Objetivo activo: implementar lo que falta en la aplicación. Esta matriz conserva el alcance
de README/SPECS; no redefine el MVP alrededor de las funciones existentes.

## Requisitos funcionales

| Requisito | Evidencia actual | Pendiente para completar |
|---|---|---|
| RF-01 autenticación | Sesión, logout, CSRF, Argon2 y prueba HTTP con Origin | Prueba de SMTP externo pendiente; registro, recuperación, UI de cuenta y alta inicial implementados |
| RF-02 empresas/roles | Modelos Company/CompanyMember y controles de lectura/escritura por tenant | Administración de plataforma pendiente; empresas adicionales, nombre y membresías owner/accountant/viewer implementados |
| RF-03 fuentes bancarias | Cuentas/saldo de demo, CSV solo lectura | Adaptadores, consentimiento, conexión/revocación, sincronización Mock y sandbox externo |
| RF-04 CSV/XLSX | CSV/XLSX 2 MB/10.000 filas con jobs, rechazo atómico y duplicados | Prueba de carga en base de datos ≥10.000 y medición |
| RF-05 facturación | XML Invoice y AttachedDocument, CUFE único, emisor/receptor, revisión de pendiente y obligación vinculada | Ampliar corpus UBL y casos tributarios; vínculo manual↔XML implementado; no certifica DIAN |
| RF-06 normalización | Descripción normalizada y comercio explícito persistidos; historial migrado y original conservado | Entidad Merchant y resolución de comercios por proveedor; reglas ampliadas con corpus bancario |
| RF-07 categorías | Reglas por tokens y categorías por signo | Clasificador TF-IDF/ML y medición de cobertura/precisión |
| RF-08 correcciones | Edición, regla por empresa, trazabilidad, prueba de futura importación | Listado paginado y eliminación auditada implementados; revisión UX ampliada pendiente |
| RF-09 recurrencias | Candidatos semanales/mensuales con evidencia y corte; confirmación/rechazo/reapertura persistidos y auditados | Calendario 30/60/90 y vinculación/creación por fecha implementados; desvinculación auditada implementada; pendiente gestión ampliada de cambios y evaluación con corpus real |
| RF-10 híbrido 30/60/90 | Escenario determinístico de obligaciones | Modelo híbrido real y persistencia de ejecuciones |
| RF-11 cuantiles | No se presentan cuantiles ficticios | P10/P50/P90, intervalos y validación de cobertura |
| RF-12 alertas | Primer déficit/mínimo determinístico | Riesgo, ventanas, factores, umbral por empresa, historial de alertas |
| RF-13 dashboard | Saldo, cobros/pagos del horizonte y escenario | Evaluar experiencia con nuevos usuarios y conectar forecast real |
| RF-14 gráficos | Línea futura, histórico mensual ingresos/egresos, tabla por categorías, obligaciones, movimientos y calendario de recurrencias | Intervalos probabilísticos y QA visual ampliado |
| RF-15 cold start | Documentado, sin comportamiento final | Cobertura de historial/calidad y nivel mostrado por modelo |
| RF-16 async | CSV y XML con Celery/Redis y estado consultable | Sincronización de cuentas/facturas por proveedor, recuperación robusta de jobs |

## Requisitos no funcionales y seguridad

| Requisito | Estado |
|---|---|
| RNF-01 secretos | Sin tokens bancarios; variables de entorno y demo local. Cifrado de tokens/gestor externo pendiente. |
| RNF-02 disponibilidad | Sin experimento de disponibilidad del 99%. |
| RNF-03 rendimiento | Sin medición p95 del dashboard y carga objetivo. |
| RNF-04 asincronía | Cargas CSV/XML fuera de HTTP; verificación con worker real. |
| RNF-05 workers horizontales | Locks/idempotencia en implementación; despliegue Linux y prueba concurrente pendientes. |
| RNF-06 trazabilidad | ImportJob, InvoiceImport, ClassificationChange y AuditLog financiero. Falta auditoría transversal de conexiones/accesos. |
| RNF-07 aislamiento | Pruebas tenant/rol en módulos actuales. Toda nueva API requiere ampliarlas. |
| RNF-08 recuperación | Backups automáticos y ensayo de restauración pendientes. |
| RNF-09 portabilidad | Compose de PostgreSQL/Redis; scripts Windows. Imágenes de app/proxy, CI completa y despliegue pendientes. |
| RNF-10 accesibilidad | Formularios etiquetados, mensajes, CSS responsive; no se ha completado QA visual/teclado automatizado. |

Pendientes de seguridad: CSP y hardening completo, rate limiting consistente, OAuth/PKCE según proveedor,
TLS de despliegue, threat model, evaluación ASVS, cifrado, pruebas de fallos/recuperación y concurrentes.

## Entregables y evaluación

- Aplicación React, backend Django, PostgreSQL, migraciones y pruebas: en desarrollo.
- Pipeline: CSV/XML y reglas; faltan proveedores, normalización completa y modelo.
- Motor híbrido, dataset 100 empresas ×24 meses, rolling-origin y comparación Naive/ARIMA/Prophet: pendientes.
- Métricas MAE/RMSE/sMAPE/pinball/DLDE, precisión-recall-F1 y reporte comparativo: pendientes.
- Threat model, manual de usuario final, manual técnico final, OpenAPI: pendientes.
- Docker Compose: solo infraestructura actual; CI YAML existe, ejecución remota y despliegue no verificados.
- Anteproyecto/documento de tesis y revisión bibliográfica: entregables académicos del documento original, no demostrados por el código.
- Usabilidad con empresarios y datos reales anonimizados requieren participantes/autorización; no se han realizado.

## Evidencia del corte actual

84 pruebas backend aprobadas sobre PostgreSQL; Ruff y build TypeScript/Vite aprobados.
HTTP real con Origin/CSRF verificó crear, conciliar, revertir y cancelar una obligación y conservar
el saldo bancario. XML multipart procesado por Celery real y confirmado con pendiente explícito.
Los archivos fuente, migraciones y tests describen el alcance real; estas pruebas no prueban
rendimiento, cobertura de todos los XML DIAN ni exactitud predictiva.

## Dependencias externas aún necesarias

Para demo local basta Docker Desktop + runtimes instalados. Sandbox bancario requiere proveedor,
acceso autorizado y credenciales (no disponibles todavía). Correo real requiere SMTP. Despliegue HTTPS
requiere entorno/dominio/certificado. Se puede seguir construyendo el resto sin esas credenciales.

Último corte: enlace explícito de XML con obligación existente, sin duplicar pendiente; 41 pruebas SQLite/PostgreSQL y build aprobados. El objetivo completo continúa activo.

Último corte: registro público con CSRF, validación de contraseña, creación atómica de propietario/empresa/cuenta manual y sesión; 45 pruebas PostgreSQL y build aprobados.

Último corte: recuperación con token Django, correo local asíncrono, expiración/uso único y revocación de sesiones. 51 pruebas PostgreSQL aprobadas. Falta validar entrega con SMTP externo.

Último corte: pantalla Empresa y equipo, roles/revocación y protección del último propietario activo; 56 pruebas PostgreSQL y build aprobados. El objetivo completo sigue activo.
