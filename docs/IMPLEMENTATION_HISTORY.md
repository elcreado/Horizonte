# Historial de cortes de implementación

Registro conservado el 4 de octubre de 2026. Los pendientes de cada corte describen ese momento; para el estado vigente consultar IMPLEMENTATION_STATUS.md.

# Estado del alcance — 2 de octubre de 2026

## Corte de distribución — 4 de octubre de 2026

Gate CI PostgreSQL 16 añadido para la suite y concurrencia. Nueva prueba: 16 solicitudes
simultáneas crean un contador y admiten exactamente 10, usando conexiones independientes y
timeouts. Todavía no ejecutada en PostgreSQL/GitHub. SQLite: 147 pruebas, 144 aprobadas,
3 omitidas (las concurrentes PostgreSQL); Ruff y formato aprobados. El runner efímero no
requiere Docker en el equipo del usuario; no se habilita facturación de minutos de CI.

Límites persistentes en BD implementados para login/registro y recuperación/reset: HMAC de
identidad, ventanas fijas, bloqueo transaccional y comando `purge_rate_limits` para vencidos.
Pruebas confirman continuidad tras vaciar caché/cambiar cliente y renovación tras vencimiento.
146 pruebas: 144 aprobadas, 2 omitidas; Ruff/migraciones aprobados. Ensayo concurrente PostgreSQL
y configuración IP del proxy siguen pendientes.

Modelo de amenazas redactado en `THREAT_MODEL.md` contra controles actuales, con riesgos y
validaciones pendientes explícitos. Corregido límite de login: también aplica a sesiones ya
autenticadas; prueba de 11.º intento rechazado sin ejecutar autenticación. Persistencia global
de límites y auditoría ASVS siguen pendientes. 146 pruebas: 144 aprobadas, 2 omitidas; Ruff aprobado.

Integridad de cuantiles guardados ampliada: entradas idénticas deduplican; cambiar un movimiento
de hace 200 días cambia digest/evidencia y crea una nueva ejecución, sin modificar la anterior.
Una segunda cuenta con solo 90 días completos impide cuantiles sin bloquear el saldo puntual.
Suite de 144 pruebas: 142 aprobadas y 2 omitidas; Ruff aprobado. QA visual no ejecutada: el
control del navegador falla al iniciar por sandbox Windows `apply deny-read ACLs`, confirmado
tras reiniciar la sesión de control; no se atribuye aprobación visual al build.

Visualización de cuantiles: componente compartido de gráfico con banda P10–P90 experimental,
saldo puntual y mediana P50; tabla y gráfico en ejecuciones guardadas, compatibles con versiones
anteriores sin cuantiles. Valores ausentes se muestran como guion; no se inventan ceros.
Build TypeScript/Vite aprobado. Revisión visual en navegador y calibración siguen pendientes.

Cuantiles conectados al híbrido actual (`hybrid_weekly_v2`): cobertura 270 días por cuenta,
API/tabla diaria P10/P50/P90 experimental y evidencia completa de la serie en ejecuciones
guardadas. Sin cobertura, permanece saldo puntual. 144 pruebas: 142 aprobadas, 2 omitidas;
Ruff y build aprobados. Falta QA de navegador, gráfico de intervalos y calibración validada.

Desglose probabilístico por los cinco perfiles implementado y regenerado: cobertura 90 días
0,7031 estacional, 0,7092 volátil y 0,7975 comercio. Se conserva el agregado y se comprueba
que los grupos reproducen conteos y cobertura ponderada. No equivale a calibración; faltan
integración con aplicación y mejora validada. 143 pruebas: 141 aprobadas, 2 omitidas.

Evaluación probabilística rolling-origin ejecutada sobre 100 empresas: cobertura puntual
0,7807/0,7726/0,7544 para 30/60/90 días, frente a 0,8 nominal. Reporte reproducible en
`PROBABILITY_RESULTS.md`, con pinball/amplitud y ventanas insuficientes explícitas. No se
declara calibración ni eficacia real; API/UI y desglose por perfil pendientes. 143 pruebas:
141 aprobadas, 2 omitidas; Ruff y formato aprobados.

Primera estimación de cuantiles implementada en `empirical_quantiles.py`: distribución empírica
de errores acumulados de Seasonal Naive en ventanas históricas anteriores al corte; mínimo
20 orígenes, compromisos futuros puntuales, rechazo de historial insuficiente. No conectada a
API/UI/reporte ni calibrada fuera de muestra. 142 pruebas: 140 aprobadas y 2 omitidas.

Métricas probabilísticas implementadas: pinball P10/P50/P90, CDF empírica, cobertura puntual y
amplitud; rechazo de valores no finitos y cuantiles cruzados comprobado. Ver
`PROBABILITY_EVALUATION.md`. No están conectadas a un modelo ni al reporte sintético; generación,
calibración y UI de cuantiles siguen pendientes. 138 pruebas: 136 aprobadas, 2 omitidas.

Configuración de producción: se rechaza el fallback SQLite si falta `POSTGRES_HOST` y se valida
el origen HTTPS de recuperación; Render puede proporcionar su URL externa. Desarrollo sin BD
externa sigue disponible. 134 pruebas ejecutadas: 132 aprobadas y 2 omitidas; Ruff aprobado.

Actualización de fiabilidad: trabajos CSV/XLSX, XML y Mock Bank se guardan junto con su mensaje
de cola en una transacción en modo `database`. Los reintentos agotados terminan el trabajo
financiero pendiente y borran el contenido de la importación; la actualización exige conservar
la propiedad del lease. Rollback por fallo de inserción y recuperación terminal comprobados.
130 pruebas SQLite ejecutadas: 128 aprobadas, 2 omitidas; Ruff y formato aprobados.
Correo Resend HTTPS implementado con pruebas simuladas; entrega real y credenciales pendientes.
Manual de usuario y recorrido de aceptación redactados en `USER_MANUAL.md`, con acciones
externas explícitas y limitaciones del escritorio en línea. Revisión contra controles/rutas
actuales realizada; ejecución del recorrido con usuarios y servidor remoto pendiente.
Manual técnico de despliegue/cola/incidentes/restauración redactado en `TECHNICAL_MANUAL.md`.
El backup existente sigue siendo local y requiere Docker; el backup remoto sin Docker sigue
pendiente. CI ampliada con pruebas Node del escritorio; ejecución de GitHub Actions no verificada.

Actualización del híbrido: `hybrid_weekly` estima recurrencias confirmadas vigentes, excluye su
historial del residual y separa los flujos recurrentes. Obligaciones vinculadas o referencias
gestionadas prevalecen; ambigüedades requieren revisión. API, historial y UI implementados, con
pruebas de confirmación, cancelación, pagos parciales, patrones invalidados y ausencia de fuga
temporal en evaluación. 123 pruebas SQLite ejecutadas (2 omitidas); Ruff y build aprobados.
Comparación sintética actualizada en `RESEARCH_RESULTS.md`; cuantiles siguen pendientes.

Actualización de evaluación: dataset reproducible de 100 empresas ×24 meses (73.100 días-empresa),
cinco perfiles y 40 empresas con episodios de déficit; baseline rolling-origin 30/60/90 con métricas
de saldo y nuevo déficit. Ver `RESEARCH_RESULTS.md`. Se excluyen del clasificador de nuevo déficit
los cortes ya negativos; no se atribuye DLDE cero a eventos ausentes. 119 pruebas ejecutadas con
SQLite, 2 omitidas; Ruff aprobado. ARIMA/Prophet, cuantiles/calibración y eficacia real siguen pendientes.

Cliente Electron y NSIS Windows generados; arranque aislado del ejecutable comprobado, formulario
de servidor HTTPS, aislamiento de Node y rechazo de HTTP externo. Django sirve el build React en
el mismo origen con WhiteNoise y headers de producción. Cola PostgreSQL opcional con leases y
reintentos, HTTP CSV sin broker y rol revalidado comprobados. 117 pruebas SQLite aprobadas, 2 omitidas.
Render Free + Supabase Free preparados; **no desplegados**. Pendientes credenciales, prueba remota,
entrega real de correo HTTPS, instalador en equipo limpio y completar los requisitos predictivos/documentales
enumerados abajo. Este corte no declara la primera versión completa.

Objetivo activo: implementar lo que falta en la aplicación. Esta matriz conserva el alcance
de README/SPECS; no redefine el MVP alrededor de las funciones existentes.

## Requisitos funcionales

| Requisito | Evidencia actual | Pendiente para completar |
|---|---|---|
| RF-01 autenticación | Sesión, logout, CSRF, Argon2 y prueba HTTP con Origin | Prueba de SMTP externo pendiente; registro, recuperación, UI de cuenta y alta inicial implementados |
| RF-02 empresas/roles | Modelos Company/CompanyMember y controles de lectura/escritura por tenant | Administración de plataforma pendiente; empresas adicionales, nombre y membresías owner/accountant/viewer implementados |
| RF-03 fuentes bancarias | Cuentas manuales y CSV/XLSX; contrato de adaptador, fuente Mock sintética con consentimiento local, sincronización asíncrona idempotente, revocación y reconexión auditadas sobre la misma cuenta | Sandbox bancario externo, credenciales/cifrado y sincronización incremental reales |
| RF-04 CSV/XLSX | CSV/XLSX 2 MB/10.000 filas con jobs, rechazo atómico y duplicados | CSV 10.000 filas optimizado: 0,645 s inicial / 0,221 s repetición; XLSX 1,444 s inicial / 1,066 s repetición e integridad concurrente verificadas; pendiente recorrido HTTP/cola y carga sostenida |
| RF-05 facturación | XML Invoice y AttachedDocument, CUFE único, emisor/receptor, revisión de pendiente y obligación vinculada | Ampliar corpus UBL y casos tributarios; vínculo manual↔XML implementado; no certifica DIAN |
| RF-06 normalización | Descripción original conservada, nombre explícito y entidad Merchant por empresa con alias por fuente; importación CSV/XLSX y sincronización enlazan comercios, historial anterior migrado | Identificación de comercios sin etiqueta explícita, gestión de alias y corpus bancario amplio |
| RF-07 categorías | Reglas por tokens y categorías por signo | Clasificador TF-IDF/ML y medición de cobertura/precisión |
| RF-08 correcciones | Edición, regla por empresa, trazabilidad, prueba de futura importación | Listado paginado y eliminación auditada implementados; revisión UX ampliada pendiente |
| RF-09 recurrencias | Candidatos semanales/mensuales con evidencia y corte; confirmación/rechazo/reapertura persistidos y auditados | Calendario 30/60/90 y vinculación/creación por fecha implementados; desvinculación auditada implementada; pendiente gestión ampliada de cambios y evaluación con corpus real |
| RF-10 híbrido 30/60/90 | Escenario contractual y referencia experimental Naive/Seasonal Naive/SES conectada con residual y obligaciones; ejecuciones guardadas con entradas, resultado, historial paginado y deduplicación | Comparación con modelos avanzados y validación real |
| RF-11 cuantiles | No se presentan cuantiles ficticios | P10/P50/P90, intervalos y validación de cobertura |
| RF-12 alertas | Déficit, mínimo y umbral configurable por propietario, días bajo umbral y brecha máxima | Historial manual e idempotente implementado; pendientes riesgo probabilístico, factores y evaluación automática |
| RF-13 dashboard | Saldo, cobros/pagos del horizonte y escenario | Evaluar experiencia con nuevos usuarios y conectar forecast real |
| RF-14 gráficos | Línea futura, histórico mensual ingresos/egresos, tabla por categorías, obligaciones, movimientos y calendario de recurrencias | Intervalos probabilísticos y QA visual ampliado |
| RF-15 cold start | Cobertura observable y declaración auditada de 90 días por cuenta; referencia experimental bloqueada si falta | Selección validada de modelo y confianza calibrada pendientes |
| RF-16 async | CSV y XML con Celery/Redis y estado consultable | Sincronización de cuentas/facturas por proveedor, recuperación robusta de jobs |

## Requisitos no funcionales y seguridad

| Requisito | Estado |
|---|---|
| RNF-01 secretos | Sin tokens bancarios; variables de entorno y demo local. Cifrado de tokens/gestor externo pendiente. |
| RNF-02 disponibilidad | Sin experimento de disponibilidad del 99%. |
| RNF-03 rendimiento | Sin medición p95 del dashboard y carga objetivo. |
| RNF-04 asincronía | Cargas CSV/XML fuera de HTTP; verificación con worker real. |
| RNF-05 workers horizontales | Locks/idempotencia en implementación; integridad concurrente PostgreSQL probada; despliegue Linux y carga con workers reales pendientes. |
| RNF-06 trazabilidad | ImportJob, InvoiceImport, ClassificationChange y AuditLog financiero. Consulta paginada por propietario/contador implementada. Falta auditoría transversal de conexiones/accesos. |
| RNF-07 aislamiento | Pruebas tenant/rol en módulos actuales. Toda nueva API requiere ampliarlas. |
| RNF-08 recuperación | Backup local diario a las 02:00 mediante tarea de Windows, archivo PostgreSQL con SHA-256 y restauración aislada verificados (34 migraciones, 2 empresas, 65 movimientos en el ensayo). Pendientes copia externa cifrada, retención/monitorización operativa y simulacro de recuperación de producción. |
| RNF-09 portabilidad | Compose de PostgreSQL/Redis; scripts Windows. Imágenes de app/proxy, CI completa y despliegue pendientes. |
| RNF-10 accesibilidad | Formularios etiquetados, mensajes, CSS responsive; no se ha completado QA visual/teclado automatizado. |

Pendientes de seguridad: CSP y hardening completo, rate limiting consistente, OAuth/PKCE según proveedor,
TLS de despliegue, threat model, evaluación ASVS, cifrado, pruebas de fallos/recuperación y concurrentes.

## Entregables y evaluación

- Aplicación React, backend Django, PostgreSQL, migraciones y pruebas: en desarrollo.
- Pipeline: CSV/XML y reglas; faltan proveedores, normalización completa y modelo.
- Dataset 100 empresas ×24 meses y rolling-origin Naive/Seasonal Naive/SES: generados y reproducibles; motor híbrido completo y comparación ARIMA/Prophet pendientes.
- MAE/RMSE/sMAPE de saldo, DLDE y precisión-recall-F1 sintéticos: medidos en `RESEARCH_RESULTS.md`; pinball, cobertura de intervalos y validación real pendientes.
- Manual de usuario: redactado, pendiente validación con usuarios (`USER_MANUAL.md`).
- Manual técnico: redactado, pendiente ensayo del despliegue (`TECHNICAL_MANUAL.md`).
- Modelo de amenazas: redactado (`THREAT_MODEL.md`), pendiente validación remota/ASVS.
- OpenAPI: pendiente.
- Docker Compose: solo infraestructura actual; CI YAML existe, ejecución remota y despliegue no verificados.
- Anteproyecto/documento de tesis y revisión bibliográfica: entregables académicos del documento original, no demostrados por el código.
- Usabilidad con empresarios y datos reales anonimizados requieren participantes/autorización; no se han realizado.

## Evidencia del corte actual

112 pruebas backend aprobadas sobre PostgreSQL; Ruff y build TypeScript/Vite aprobados.
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
