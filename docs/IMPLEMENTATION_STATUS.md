# Estado vigente del entregable — 5 de octubre de 2026

**La primera versión todavía no está completa.** Esta matriz conserva el alcance de README/SPECS.
Los cortes anteriores están en [IMPLEMENTATION_HISTORY.md](IMPLEMENTATION_HISTORY.md); sus
pendientes históricos no sustituyen este estado vigente.

## Corte verificado del 5 de octubre

- Evaluación emparejada de intervalos completada: [INTERVAL_RESULTS.md](INTERVAL_RESULTS.md).
  Corrección temporal aumenta cobertura agregada a 0,8269/0,8296/0,8101, pero amplía
  intervalos y no resuelve todos los perfiles (volátil a 90 días: 0,6701). Candidato offline,
  sin garantía de cobertura ni probabilidades de déficit. Corpus independiente pendiente.
  Suite local vigente: 195 pruebas, 190 aprobadas y 5 omitidas; Ruff aprobado.

- Render Free `horizonte-demo` está publicado en https://horizonte-demo.onrender.com,
  conectado a PostgreSQL de Supabase mediante Session pooler con TLS. Inicio y API de salud
  respondieron 200. Sesión, importación CSV, Mock Bank y confirmación XML comprobados por HTTP.
  No se necesita Docker para consumir este servicio desde el instalador.
- Instalador actual: `desktop/release/hosted/Horizonte Setup 0.1.0.exe`, con URL alojada
  precargada y editable. Binario de configuración verificado; instalación limpia, sesión remota
  dentro de Electron y desinstalación siguen pendientes. No está firmado.
- CI publicada en https://github.com/elcreado/Horizonte/actions/runs/37325123856:
  backend, backend-postgres, frontend y desktop aprobados. Corregido el uso de TestCase
  en pruebas que invocan el worker y limpian conexiones PostgreSQL.
- Comparación ARIMA de 100 empresas ×24 meses terminada: [ARIMA_RESULTS.md](ARIMA_RESULTS.md).
  No supera al híbrido en MAE ni recall de déficit en los tres horizontes. Sigue fuera de
  producción; respaldo SES explícito y sin exclusión de ventanas fallidas. Faltan calibración
  de intervalos, corpus independiente, evaluación de clasificación y usabilidad.
- Frontend carga pantallas y gráficas bajo demanda; build inicial reducido y módulos remotos
  disponibles por HTTP. Renderizado visual y recuperación de servicio dormido sin verificar.
- OpenAPI incorpora los contratos de umbrales y del conector Mock Bank. La documentación
  completa de errores y de operaciones restantes sigue pendiente.
- Pruebas externas pendientes: entrega real de recuperación por correo (proveedor/remitente),
  respaldo y restauración PostgreSQL, Windows limpio, carga/p95 y revisión visual/accesibilidad.

Las entradas de distribución inferiores conservan cortes históricos: sus afirmaciones de
ausencia de credenciales, servicio remoto o instalador alojado quedan sustituidas por este corte.

## Distribución y comprobaciones actuales

- OpenAPI de reglas GET/DELETE completado para campos exitosos, paginación, roles y
  eliminación auditada 204 sin cuerpo ni reclasificación de movimientos anteriores.
  Suite vigente: 184 pruebas, 179 aprobadas y 5 omitidas; Ruff aprobado.

- Intento de QA navegador del 5 de octubre falló al iniciar herramienta por sandbox Windows
  (`apply deny-read ACLs`), sin resultados visuales. Recorrido verificable de sesión, cuentas,
  trabajos y reactivación redactado en QA_CONNECTIVITY.md; casos aún pendientes de ejecución.

- Comprobación inicial de sesión distingue 403 (sin sesión) de errores de red/servidor:
  conserva estado ante fallos y ofrece reintento en rutas de aplicación. Inicio público sigue
  disponible; validación básica de respuesta y cancelación al desmontar. Build aprobado;
  recorrido visual de reactivación pendiente.

- Formulario CSV/XLSX reintenta la consulta inicial de cuentas hasta obtener respuesta;
  luego evita repetir esa consulta en cada sondeo de trabajos. Error de cuentas separado
  de errores de operación y eliminado al recuperar; respeta cancelación del componente.
  Build frontend aprobado; prueba visual de arranque en frío sigue pendiente.

- Consulta periódica de CSV/XML separa avisos de conexión de errores de carga/confirmación:
  una consulta exitosa elimina solo su aviso anterior; respuestas canceladas no actualizan estado.
  Build frontend aprobado; ensayo visual de caída/recuperación sigue pendiente.

- OpenAPI de vínculo XML GET/POST documentado: candidatas paginadas compatibles, ID positivo,
  permisos/auditoría, respuesta de factura e idempotencia del vínculo. Suite: 184 pruebas,
  179 aprobadas y 5 omitidas; Ruff aprobado. Esquemas completos de error y API restante pendientes.

- OpenAPI completa campos exitosos de factura para listado y confirmación: CUFE/identidad,
  partes/NIT, importes, fechas y obligación/pendiente/cancelación; salida compartida 200/201.
  Listado paginado y capacidad por rol documentados. Suite: 184 pruebas, 179 aprobadas y
  5 omitidas; Ruff aprobado. Vínculo manual y errores completos siguen pendientes.

- Entrada OpenAPI de confirmación XML documentada con restricciones de fecha/pendiente,
  mínimo decimal derivado del serializador y distinción 200 existente/201 nueva obligación.
  Esquema completo de salida marcado pendiente. Suite: 184 pruebas, 179 aprobadas y 5 omitidas;
  Ruff aprobado. Contratos de listado/vínculo y errores completos aún pendientes.

- Mensajes de interfaz corregidos para pruebas de escritorio: sin empresas dirige al alta
  y acceso por propietario; trabajos pendientes explican reactivación del servicio sin pedir
  arrancar workers. Pie ya no afirma datos sintéticos/solo lectura para toda la aplicación.
  Build frontend aprobado; persiste aviso de tamaño del bundle. QA de estos mensajes pendiente.

- Contratos OpenAPI de carga XML GET/POST añadidos: multipart, límites/codificación,
  encolado 202 y consulta de trabajos, separados de validación y confirmación de obligación.
  Suite vigente: 184 pruebas, 179 aprobadas y 5 omitidas; deriva del inventario aprobada.

- Contrato OpenAPI de consulta administrativa documentado con campos/paginación y requisito
  explícito de superusuario activo staff; inventario regenerado y pruebas de deriva aprobadas.
  Suite: 184 pruebas, 179 aprobadas y 5 omitidas. Conexión PostgreSQL todavía ausente en
  `.env.hosted` al verificar el 5 de octubre; las claves API Supabase no la sustituyen.

- Corte de despliegue del 5 de octubre: Render conectado y repositorio remoto Horizonte presente.
  `.env.hosted` existe con claves API Supabase, pero sin conexión PostgreSQL de Session pooler.
  Pendiente elegir workspace y aportar conexión antes de crear el servicio Free. No se han
  publicado ni validado servicios en este corte.

- Vista React de consulta administrativa conectada en `#/platform`, con capacidad de sesión,
  tabla paginada, actualización, errores y cancelación. Última verificación: 184 pruebas,
  179 aprobadas y 5 omitidas; build frontend aprobado. Falta QA y provisión de administrador.

- Consulta administrativa GET `/api/platform/users/` implementada, paginada y reservada a
  superusuarios activos staff; rechazos de usuarios de empresa/staff/inactivos probados.
  No incluye hash/contraseña. Interfaz y operaciones administrativas auditadas siguen pendientes.
  Suite vigente: 184 pruebas, 179 aprobadas y 5 omitidas; inventario 48 rutas/61 operaciones.

- Diagnóstico `platform_admin_status` añadido y ejecutado localmente: no existe superusuario
  activo con acceso staff. No hay UI administrativa configurada; gestión de plataforma sigue
  pendiente. Procedimiento de provisión y límites documentados en PLATFORM_ADMIN.md.

- Importación CSV real → corrección HTTP de comercio → nueva importación con alias normalizado:
  nombre revisado se conserva, ambos movimientos enlazan el mismo comercio y descripciones
  originales permanecen intactas en consulta HTTP. Suite vigente: 183 pruebas, 178 aprobadas
  y 5 omitidas. No demuestra corpus bancario real ni gestión ampliada de alias.

- OpenAPI ampliado con movimientos GET y corrección de categoría PATCH: campos, paginación,
  rol, opciones por signo y regla recordada documentados. Sin filtros adicionales actuales.
  Inventario regenerado; suite vigente: 182 pruebas, 177 aprobadas y 5 omitidas; Ruff aprobado.

- Ensayo de cola con cuatro workers concurrentes y doce mensajes añadido a la suite
  PostgreSQL: verifica reclamación única, finalización y eliminación de argumentos.
  No ejecutado localmente por falta de PostgreSQL; CI configurada para incluirlo, sin ejecución
  remota demostrada. Suite local: 182 pruebas, 177 aprobadas y 5 omitidas; migraciones sin
  cambios pendientes y Ruff aprobado. `.env.hosted` sigue ausente al comprobar el despliegue.

- Contratos OpenAPI de comercios GET y nombre PATCH completados para campos exitosos,
  paginación/capacidad por rol, límites y errores descritos. Inventario regenerado y suite
  de deriva aprobada. Suite vigente: 181 pruebas, 177 aprobadas y 4 omitidas; Ruff aprobado.
  Contratos restantes y cuerpos completos de error siguen pendientes.

- Edición de nombres de comercios conectada a React: guardar/cancelar, mensajes, CSRF,
  botones según capacidad owner/accountant y cancelación de peticiones al desmontar.
  Listado añade `can_edit`, con prueba por rol. Suite general: 181 pruebas, 177 aprobadas y
  4 omitidas; cambios posteriores verificados por suite del módulo y build frontend.
  QA visual/teclado y gestión de alias siguen pendientes; aviso de bundle grande persiste.

- API PATCH de nombre visible de comercio implementada con propietario/contador, aislamiento,
  auditoría idempotente y conservación de alias/resolución futura. Interfaz de edición y gestión
  de alias todavía pendientes. Suite vigente: 181 pruebas, 177 aprobadas y 4 omitidas.
  Inventario actualizado: 47 rutas y 60 operaciones; contrato detallado de esta API pendiente.

- Recuperación comprobada por HTTP con CSRF → cola BD → comando worker → correo en memoria
  → reset con token de un solo uso. Fallo de inserción devuelve 503 genérico para usuario
  existente/inexistente sin mensaje huérfano ni correo. Suite vigente: 179 pruebas,
  175 aprobadas y 4 omitidas. No prueba proveedor HTTPS ni entrega al destinatario real.

- Instalador más reciente: `desktop/release/permissions/Horizonte Setup 0.1.0.exe`.
  Ambas ventanas deniegan consultas/solicitudes de permisos y permisos de dispositivos.
  Prueba del binario confirma geolocation/camera/microphone `denied` en configuración,
  Node oculto y rechazo HTTP externo. Build NSIS y tres pruebas de endpoints aprobados.
  No equivale a instalación limpia ni prueba de permisos en la aplicación remota.

- Consulta de cuentas devuelve saldo como cadena decimal, evitando conversión float en JSON;
  contrato OpenAPI incluye campos, cobertura y conexión anulables. Prueba HTTP local aprobada;
  importe máximo reservado para PostgreSQL. Suite vigente: 177 pruebas, 173 aprobadas y
  4 omitidas; Ruff y build frontend aprobados (persiste aviso de tamaño del bundle).

- Respaldo alojado aislado de variables libpq heredadas (servicio, hostaddr, opciones y
  certificados); puerto validado y nombre de BD rechaza cadenas de conexión que cambien destino.
  Certificado raíz opcional explícito `POSTGRES_SSLROOTCERT`. Suite vigente: 175 pruebas,
  172 aprobadas y 3 omitidas; Ruff aprobado. Respaldo/restauración remotos siguen sin ensayo.

- OpenAPI de importación bancaria GET/POST: multipart, respuesta asíncrona 202, estados/
  formatos del modelo, listado limitado a 20 y restricciones/errores documentados.
  Suite vigente: 174 pruebas, 171 aprobadas y 3 omitidas; Ruff aprobado. API restante y
  esquemas de error completos siguen pendientes.

- Recuperación de leases: prueba de intercalación controlada confirma que el resultado tardío
  de un intento antiguo no sobrescribe finalización ni reintento del nuevo propietario.
  No sustituye concurrencia real PostgreSQL. Suite vigente: 173 pruebas, 170 aprobadas y
  3 omitidas; Ruff aprobado.

- Instalador actualizado en `desktop/release/recovery/Horizonte Setup 0.1.0.exe`:
  aviso de fallo con reintento/configuración/cierre y descarte de errores de ventanas obsoletas.
  Compilación NSIS aprobada y sintaxis/3 pruebas de endpoints aprobadas. Prueba de arranque
  del binario actualizado verifica configuración, Node oculto y rechazo de HTTP externo.
  No prueba el diálogo de recuperación, instalación limpia ni servidor remoto.

- Worker de cola BD: comando `run_background --once` procesa como máximo una tarea disponible;
  prueba con importador CSV real e idempotencia, sin Redis. Rechaza configuración Celery y usa
  espera interrumpible al apagar. Suite vigente: 172 pruebas, 169 aprobadas y 3 omitidas.
  Ensayo remoto Linux/PostgreSQL sigue pendiente.

- Supervisor alojado: apagado durante inicio evita crear más hijos; fallo de un hijo o inicio
  parcial limpia el restante; procesos que exceden el plazo de terminación se fuerzan a salir.
  Restaura manejadores de señales. Cuatro pruebas simuladas de ciclo de vida; no validado aún
  en Render. Suite vigente: 170 pruebas, 167 aprobadas y 3 omitidas; Ruff y formato aprobados.

- Contratos OpenAPI de saldo y cobertura bancaria: entradas, respuesta 200, fechas anulables,
  permisos y errores 400/403/404/409 documentados; cuerpos de error todavía pendientes.
  Suite vigente: 166 pruebas, 163 aprobadas y 3 omitidas; Ruff aprobado.

- OpenAPI ampliado con campos y respuestas exitosas de CSRF/me/login/logout/recuperación/reset,
  registro, perfil GET/PATCH y creación de empresa. Longitudes, patrones, fechas, obligatoriedad
  y precisión decimal derivados de serializadores; contraseñas marcadas como solo escritura.
  Contratos financieros y errores detallados siguen pendientes. Suite vigente: 165 pruebas,
  162 aprobadas y 3 omitidas; Ruff y formato aprobados.

- Inventario OpenAPI parcial generado desde Django: 46 rutas/59 operaciones, sesión/acceso
  público, parámetros y CSRF; pruebas de deriva e IDs únicos. Esquemas detallados pendientes.
  Suite: 163 pruebas, 160 aprobadas y 3 omitidas; Ruff aprobado. Ver API_DOCUMENTATION.md.

- Fallo al insertar un mensaje de cola persistente: respuesta HTTP 503 sanitizada y rollback
  del trabajo; CSV/XML verificados sin registros huérfanos. Suite actual: 161 pruebas,
  158 aprobadas y 3 omitidas; Ruff y formato aprobados.

- Respaldo nativo alojado preparado en `scripts/hosted_backup.py`, sin Docker, con SSL, archivo
  custom, índice y SHA-256. Pruebas simuladas de secreto/error/archivo; no ejecutado contra
  PostgreSQL remoto ni restaurado/cifrado. Ver HOSTED_BACKUP.md. Suite: 160 pruebas,
  157 aprobadas y 3 omitidas; Ruff aprobado.

- Comando `research_classification` para corpus CSV etiquetado: corte temporal de revisiones,
  grupos separados, empresa/dirección únicas, hash y métricas sin descripciones en salida.
  Pruebas de etiquetas tardías y fuga por grupos/empresa aprobadas. Suite: 157 pruebas,
  154 aprobadas y 3 omitidas; Ruff aprobado. Corpus representativo sigue pendiente.

- Evaluador selectivo del clasificador implementado: cobertura/acierto, confusión y métricas por
  categoría, abstenciones explícitas y rechazo de solapamiento de texto entrenamiento/prueba.
  Corpus representativo y medición de eficacia pendientes. Suite: 155 pruebas, 152 aprobadas,
  3 omitidas; Ruff aprobado. No se atribuye precisión real a ejemplos unitarios.

- UI de sugerencias TF-IDF incorporada a clasificación manual: consulta, abstención, selección
  explícita y guardado separado. Prueba ampliada con empresa ajena real: sus etiquetas no
  entrenan el modelo propio y sus movimientos no son consultables. Suite: 152 pruebas,
  149 aprobadas y 3 omitidas; Ruff y build aprobados. QA visual sigue pendiente.

- Clasificador TF-IDF/centroides experimental con sugerencias autenticadas, entrenado solo con
  etiquetas manuales por empresa/dirección; sin aplicación automática. Falta UI y evaluación.
  Última suite ampliada: 151 pruebas, 148 aprobadas, 3 omitidas; Ruff aprobado.

- Cliente Electron y NSIS Windows generados; arranque aislado de configuración comprobado.
  Instalación/actualización/desinstalación en Windows limpio y recorrido HTTPS remoto pendientes.
- Render Free + Supabase Free preparados, no desplegados. Presupuesto 0 USD, suspensión aceptada;
  `.env.hosted` sigue ausente. No se han creado ni contratado servicios.
- Cola BD sin Redis y correo HTTPS implementados. Recuperación de jobs probada en SQLite;
  entrega de correo y cortes reales de procesos remotos pendientes.
- Última suite local: 147 pruebas, 144 aprobadas y 3 omitidas que requieren PostgreSQL.
  Ruff y formato aprobados; build frontend y tres pruebas Node de escritorio aprobados en cortes recientes.
- CI contiene backend SQLite/PostgreSQL, frontend y contrato de escritorio; ejecución en GitHub
  no verificada. PostgreSQL local no disponible en esta revisión.
- Cuantiles conectados a API/gráfico/tabla/historial. Cobertura sintética 30/60/90: 78,07/77,26/75,44 %;
  inferior al 80 % nominal. Experimental, sin calibración ni eficacia real demostradas.
- QA visual sigue pendiente: control del navegador falla al iniciar por sandbox Windows
  `apply deny-read ACLs`, incluso tras reiniciar su sesión. No confundir build con QA visual.

Objetivo activo: implementar lo que falta en la aplicación. Esta matriz conserva el alcance
de README/SPECS; no redefine el MVP alrededor de las funciones existentes.

## Requisitos funcionales

| Requisito | Evidencia actual | Pendiente para completar |
|---|---|---|
| RF-01 autenticación | Sesión, logout, CSRF, Argon2 y prueba HTTP con Origin | Entrega real de correo HTTPS pendiente; registro, recuperación, UI de cuenta y alta inicial implementados |
| RF-02 empresas/roles | Modelos Company/CompanyMember y controles de lectura/escritura por tenant | Administración de plataforma pendiente; empresas adicionales, nombre y membresías owner/accountant/viewer implementados |
| RF-03 fuentes bancarias | Cuentas manuales y CSV/XLSX; contrato de adaptador, fuente Mock sintética con consentimiento local, sincronización asíncrona idempotente, revocación y reconexión auditadas sobre la misma cuenta | Sandbox bancario externo, credenciales/cifrado y sincronización incremental reales |
| RF-04 CSV/XLSX | CSV/XLSX 2 MB/10.000 filas con jobs, rechazo atómico y duplicados | CSV 10.000 filas optimizado: 0,645 s inicial / 0,221 s repetición; XLSX 1,444 s inicial / 1,066 s repetición e integridad concurrente verificadas; pendiente recorrido HTTP/cola y carga sostenida |
| RF-05 facturación | XML Invoice y AttachedDocument, CUFE único, emisor/receptor, revisión de pendiente y obligación vinculada | Ampliar corpus UBL y casos tributarios; vínculo manual↔XML implementado; no certifica DIAN |
| RF-06 normalización | Descripción original conservada, nombre explícito y entidad Merchant por empresa con alias por fuente; importación CSV/XLSX y sincronización enlazan comercios, historial anterior migrado | Identificación de comercios sin etiqueta explícita, gestión de alias y corpus bancario amplio |
| RF-07 categorías | Reglas por tokens/signo y TF-IDF experimental por empresa/dirección; API y UI de sugerencias con revisión explícita | Medición de cobertura/precisión fuera de muestra y QA; ver CLASSIFICATION_MODEL.md |
| RF-08 correcciones | Edición, regla por empresa, trazabilidad, prueba de futura importación | Listado paginado y eliminación auditada implementados; revisión UX ampliada pendiente |
| RF-09 recurrencias | Candidatos semanales/mensuales con evidencia y corte; confirmación/rechazo/reapertura persistidos y auditados | Calendario 30/60/90 y vinculación/creación por fecha implementados; desvinculación auditada implementada; pendiente gestión ampliada de cambios y evaluación con corpus real |
| RF-10 híbrido 30/60/90 | Escenario contractual, Naive/Seasonal Naive/SES e híbrido semanal con recurrencias confirmadas vigentes; ejecuciones guardadas con entradas, resultado, historial paginado y deduplicación | Comparación con modelos avanzados y validación real |
| RF-11 cuantiles | P10/P50/P90 empíricos experimentales con 270 días completos; API, banda, tabla e historial; evaluación sintética por horizonte/perfil | Calibración validada y evaluación real; no se declara cobertura nominal garantizada |
| RF-12 alertas | Déficit, mínimo y umbral configurable por propietario, días bajo umbral y brecha máxima | Historial manual e idempotente implementado; pendientes riesgo probabilístico, factores y evaluación automática |
| RF-13 dashboard | Saldo, cobros/pagos del horizonte y escenario | Evaluar experiencia con nuevos usuarios y conectar forecast real |
| RF-14 gráficos | Línea futura, histórico mensual ingresos/egresos, tabla por categorías, obligaciones, movimientos y calendario de recurrencias | Banda experimental implementada; QA visual/teclado ampliado pendiente |
| RF-15 cold start | Cobertura observable y declaración auditada de 90 días por cuenta; referencia experimental bloqueada si falta | Selección validada de modelo y confianza calibrada pendientes |
| RF-16 async | CSV/XLSX, XML y Mock Bank; Celery o cola BD sin Redis, creación atómica, leases/reintentos y cierre terminal probados | Cortes reales Linux/PostgreSQL, carga y proveedores externos |

## Requisitos no funcionales y seguridad

| Requisito | Estado |
|---|---|
| RNF-01 secretos | Sin tokens bancarios; variables de entorno y demo local. Cifrado de tokens/gestor externo pendiente. |
| RNF-02 disponibilidad | Sin experimento de disponibilidad del 99%. |
| RNF-03 rendimiento | Sin medición p95 del dashboard y carga objetivo. |
| RNF-04 asincronía | Cargas CSV/XML fuera de HTTP; verificación con worker real. |
| RNF-05 workers horizontales | Locks/idempotencia en implementación; pruebas concurrentes de importación verificadas en un corte anterior, nuevo límite persistente aún sin ensayo PostgreSQL; despliegue Linux y carga con workers reales pendientes. |
| RNF-06 trazabilidad | ImportJob, InvoiceImport, ClassificationChange y AuditLog financiero. Consulta paginada por propietario/contador implementada. Falta auditoría transversal de conexiones/accesos. |
| RNF-07 aislamiento | Pruebas tenant/rol en módulos actuales. Toda nueva API requiere ampliarlas. |
| RNF-08 recuperación | Backup local diario a las 02:00 mediante tarea de Windows, archivo PostgreSQL con SHA-256 y restauración aislada verificados (34 migraciones, 2 empresas, 65 movimientos en el ensayo). Pendientes copia externa cifrada, retención/monitorización operativa y simulacro de recuperación de producción. |
| RNF-09 portabilidad | Compose de PostgreSQL/Redis; scripts Windows. Imágenes de app/proxy, CI completa y despliegue pendientes. |
| RNF-10 accesibilidad | Formularios etiquetados, mensajes, CSS responsive; no se ha completado QA visual/teclado automatizado. |

Seguridad implementada: CSP de producción, validaciones de configuración y límites persistentes
en BD con ventanas fijas. Modelo de amenazas redactado. Pendientes: concurrencia de límites,
IP del proxy, TLS remoto, ASVS, cifrado/retención, OAuth/PKCE de proveedores y recuperación remota.

## Entregables y evaluación

- Aplicación React, backend Django, PostgreSQL, migraciones y pruebas: en desarrollo.
- Pipeline: CSV/XML y reglas; faltan proveedores, normalización completa y modelo.
- Dataset 100 empresas ×24 meses y rolling-origin Naive/Seasonal Naive/SES: generados y reproducibles; motor híbrido completo y comparación ARIMA/Prophet pendientes.
- MAE/RMSE/sMAPE de saldo, DLDE y precisión-recall-F1 sintéticos: medidos en `RESEARCH_RESULTS.md`; pinball/cobertura/amplitud sintéticos medidos en PROBABILITY_RESULTS.md; calibración y validación real pendientes.
- Manual de usuario: redactado, pendiente validación con usuarios (`USER_MANUAL.md`).
- Manual técnico: redactado, pendiente ensayo del despliegue (`TECHNICAL_MANUAL.md`).
- Modelo de amenazas: redactado (`THREAT_MODEL.md`), pendiente validación remota/ASVS.
- OpenAPI: inventario de rutas/métodos/autenticación implementado; cuerpos, validaciones,
  respuestas específicas y ejemplos pendientes (`API_DOCUMENTATION.md`).
- Docker Compose: solo infraestructura actual; CI YAML existe, ejecución remota y despliegue no verificados.
- Anteproyecto/documento de tesis y revisión bibliográfica: entregables académicos del documento original, no demostrados por el código.
- Usabilidad con empresarios y datos reales anonimizados requieren participantes/autorización; no se han realizado.

## Próximos pasos para cerrar la versión

- Completar clasificación ML, evaluación avanzada, calibración/alertas probabilísticas y OpenAPI según alcance.
- Ensayar carga, archivos adversariales, límites concurrentes y restauración remota sin Docker.
- Publicar en las cuentas Free con credenciales y acceso al repositorio; verificar sesiones/CSRF y cola.
- Comprobar entrega de correo a un destinatario propio autorizado y recuperación completa.
- Probar instalador en Windows limpio y recorrido de USER_MANUAL.md, incluyendo Inicio sin sesión.
- Completar QA visual/accesibilidad, usabilidad y evaluación con datos autorizados.
- Revisar todos los requisitos de esta matriz antes de declarar V1 terminada.

## Acciones externas necesarias

- Render/Supabase Free, conexión Session pooler y repositorio accesible: HOSTING_FREE.md.
- Credencial de correo HTTPS y remitente permitido para pruebas reales.
- Windows limpio y servidor HTTPS operativo para aceptar el instalador; el usuario final no necesita Docker.
- Sandbox bancario, participantes y datos autorizados para las pruebas reales; Mock y dataset sintético no los sustituyen.
- Almacenamiento seguro y entorno PostgreSQL aislado para restauración remota.

Manual de uso: USER_MANUAL.md. Operación: TECHNICAL_MANUAL.md. Riesgos: THREAT_MODEL.md.
# Avance del 5 de octubre de 2026: alias de comercios

## Carga del cliente y evidencia remota

- CI `37324872869` del commit `6fe6ff5` terminó correctamente en sus cuatro jobs,
  incluido PostgreSQL. Se resolvió el cierre de conexión provocado por ejecutar el comando
  worker desde la transacción envolvente de `TestCase`; ambas clases usan `TransactionTestCase`.
  El fallo de seis errores indicado en notas posteriores pertenece al corte anterior.

- Pantallas de historial, facturas, obligaciones, movimientos, comercios, proyección experimental
  y gráfico principal usan carga diferida. Inicio no precarga el paquete de gráficos según el
  HTML compilado. Se ofrece un mensaje de carga y recuperación mediante recarga si una pantalla falla.
- Compilación TypeScript/Vite aprobada: código inicial de aplicación 59,41 kB; vendor 197,04 kB;
  gráficos 365,76 kB. No se ha medido el tiempo real de renderizado en navegador.
- Render/Supabase activos; se probaron por HTTP registro/sesión/CSRF, CSV, Mock Bank y factura XML.
  Una importación de 10.000 filas completó el recorrido en 12 segundos observados; ver
  `HOSTING_FREE.md` e `IMPORT_BENCHMARK.md` para límites de la medición.
- CI PostgreSQL sigue fallando con seis errores cuyo traceback aún no está disponible.
  Los resultados HTTP no sustituyen la suite ni demuestran cierre de todos los RF/RNF.
- Instalador actualizado en `desktop/release/hosted/`; QA visual y Windows limpio pendientes.

- API `GET/POST /api/companies/{company_id}/merchant-aliases/`: consulta paginada y
  asignación de etiquetas normalizadas de `manual_upload` o `mock` a un comercio de la empresa.
- Solo propietario o contador puede asignar; cada cambio efectivo queda en auditoría.
  Repetir la misma asignación no duplica el registro de auditoría.
- La asignación afecta futuras importaciones. No fusiona comercios ni modifica movimientos
  anteriores o descripciones originales.
- Verificación: suite Django de 185 pruebas, 180 aprobadas y 5 omitidas por depender de
  PostgreSQL; Ruff sin incidencias. Incluye importación CSV antes y después de reasignar.
- La pantalla de comercios permite seleccionar un comercio de la página y asignarle una etiqueta
  CSV/XLSX o Mock Bank. Explica el reemplazo de una asignación anterior y su efecto solo futuro.
  TypeScript y compilación Vite aprobados; persiste el aviso de tamaño del paquete principal.
- La interfaz incluye listado paginado de etiquetas por fuente y comercio asignado, recuperación
  ante errores y actualización tras asignar una etiqueta. Compilación TypeScript/Vite aprobada.
- Contrato de alias documentado: cuerpo, fuentes permitidas, paginación y respuestas 200/201,
  permisos y validación. Inventario exportado y comprobado contra las rutas actuales.
- Prueba adicional de aislamiento aprobada: rechaza un comercio real de otra empresa,
  restringe la consulta por membresía y mantiene resoluciones independientes para CSV/XLSX,
  Mock Bank y otra empresa. Suite focalizada: 13 pruebas aprobadas (incluye fixtures de importación).
- Protección CSRF verificada con sesión Django real: la escritura sin token devuelve 403 y
  no crea alias; con cookie y token válidos crea una asignación y una auditoría. Módulo: 14
  pruebas aprobadas. No representa todavía la validación de cookies HTTPS en Render.
- Pendiente: prueba visual
  y concurrencia real en PostgreSQL. El inventario de API sigue siendo parcial.
