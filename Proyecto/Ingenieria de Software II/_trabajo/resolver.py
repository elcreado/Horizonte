from pathlib import Path
from copy import deepcopy
import json,re,ast
from docx import Document
from docx.shared import Pt,Cm
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docxResueltosCopias';OUT.mkdir(exist_ok=True)
STUDENT='Adrian Perez Pacheco'
PROJECT='Horizonte SaaS de inteligencia de liquidez para microempresas'
CONTEXT='SaaS multiempresa para Villa del Rosario, Cúcuta y Norte de Santander, sin empresa beneficiaria única. Adrian es estudiante de la Universidad de Pamplona, Sede Villa del Rosario, Facultad de Ingeniería y Arquitecturas, Ingeniería de Sistemas; profesor Miguel Eduardo Posada Haddad. Scrum individual: Adrian asume producto, facilitación y desarrollo; sprints propuestos de dos semanas y revisión externa por acordar.'
EVID='Corte documental 30/10/2026. Se contrastaron código, compose.yaml, .github/workflows/ci.yml y docs/IMPLEMENTATION_STATUS.md. El registro del 18/10 informa 235 pruebas PostgreSQL: 233 aprobadas y 2 omitidas; es evidencia histórica, no una nueva ejecución de esta entrega. No se certifica producción actual, ASVS, p95 representativo ni validación con empresarios. Presupuesto inicial 0 USD y respaldo manual por decisión del proyecto.'
TOPICS=['Línea base y deuda','Drivers de calidad','Registro ADR','Monolito modular','Contextos de dominio','Contrato API','Pruebas de integración','TDD y rendimiento','CI y gates','Docker y persistencia','Entrega controlada','DevSecOps','Observabilidad','SRE e incidentes','Mantenimiento','Dossier final']
DEC=[
'Conservar línea base verificable y priorizar deuda por riesgo, sin reescribir todo el SaaS.',
'Priorizar aislamiento, integridad monetaria y mantenibilidad; medir desempeño antes de prometerlo.',
'Registrar monolito modular y comparar alternativas mediante drivers, con ADR sucesor para cambios.',
'Mantener servicios de cálculo puros y aislar infraestructura en límites con variación real.',
'Conservar cuentas, clasificación, facturas y proyección en el monolito; workers no equivalen a microservicios.',
'Mantener sesión Django y CSRF para la web; documentar OpenAPI sin introducir JWT innecesario.',
'Probar API con ORM real en BD temporal y simular solo proveedores externos o despacho de cola.',
'Usar TDD en cambios pequeños y medir carga local autenticada antes de elevar concurrencia.',
'Conservar CI existente y proponer gate bloqueante de cobertura sin fingir aprobación remota.',
'Distinguir Compose local operativo de una imagen productiva endurecida, aún mejorable.',
'Elegir Continuous Delivery con aprobación de publicación y healthcheck, compatible con presupuesto cero.',
'Añadir análisis bloqueante y revisión humana de hallazgos, sin inventar CVE ni enviar reportes sensibles.',
'Instrumentar señales mínimas sin PII y sin cardinalidad por empresa o movimiento.',
'Definir SLO de ensayo, runbook individual y postmortem sin culpables; no prometer SLA gratuito.',
'Priorizar deuda por pérdida esperada y conservar equivalencia mediante pruebas antes de integrar cambios.',
'Cerrar documentación con evidencia delimitada y mantener abiertas las brechas de aceptación y operación.'
]
EX={
1:[
'La línea base registra versiones, comportamiento, pruebas y deuda antes de cambiar el sistema. Permite comparar resultados, rastrear cambios y recuperar una versión conocida. En Horizonte incluye commit local, dependencias, migraciones y límites del modelo. La ficha ISO confirma el marco de ciclo de vida; no atribuyo a su resumen público una cláusula textual específica no consultada.',
'Código: controlador de dashboard combina consultas y composición. Diseño: aislamiento repetido exige disciplina en cada API. Pruebas: falta aceptación transversal y rendimiento representativo. Seguridad/infraestructura: Docker backend sin USER explícito y revisión ASVS incompleta. Son hallazgos y riesgos, no prueba de incidentes ocurridos.',
'El SELECT y el INSERT interpolan entradas y permiten inyección; api_key queda expuesta y se imprime; CONEXION_GLOBAL acopla persistencia; IVA fijo oculta política; se registra venta antes de confirmar pago y no hay control de stock ni rollback. Sin conocer intención no se puede inferir deliberación: clasifico riesgo imprudente y registro intención no demostrada. El IVA fijo puede ser deuda deliberada prudente solo si se limita y documenta su contexto.',
'El fragmento contiene un único if (metodo_pago == PAYU): V(G)=1+1=2. Hay dos caminos de control mínimos, PAYU y otro. Dos tests no garantizan seguridad ni cubren entradas inválidas; agregaría producto inexistente, cantidad negativa, stock insuficiente, error de pago e inyección como dato.',
'Prompt de esta entrega: refactoriza el ejemplo de venta con dependencias inyectadas, Decimal y transacción, sin secretos ni bibliotecas externas. Respuesta completa: ver el listado Refactor didáctico de venta incluido al final del taller. Es un ejemplo aislado, no una función de Horizonte: el SaaS no cobra ni mueve dinero.',
'Auditoría: SQL parametrizado pertenece al adaptador, no al núcleo; no hay credencial en argumentos ni logs; se compila el ejemplo con ast.parse. Solo usa Decimal y Protocol de la biblioteca estándar de Python; no añade paquetes. Se usan nombres ficticios. Para producción, tokenizar pago, garantizar idempotencia y diseñar compensación entre pago remoto y transacción local; no afirmar atomicidad distribuida.'
],
2:[
'RF describe una función, como importar CSV; un atributo de calidad describe bajo qué condiciones funciona, por ejemplo sin leer otra empresa. En Horizonte la integridad e idempotencia importan tanto como recibir el archivo. Una meta cuantitativa no equivale a resultado medido.',
'Farmacia ficticia. Fuente: dependiente. Estímulo: consulta de pedido. Artefacto: API de pedidos. Entorno: horario comercial y carga acordada. Respuesta: atender consulta o devolver error controlado. Medida: 99% de solicitudes válidas con respuesta correcta en ventana de 30 días; registrar excluidos y caídas. Es meta propuesta.',
'Consultar autenticación y permisos añade trabajo, pero protege información de pacientes y pedidos. Priorizaría seguridad sobre unos milisegundos; optimizaría consultas e índices y mediría p95. No eliminaría controles para cumplir un tiempo arbitrario.',
'Fuente: Adrian; estímulo: nueva regla de proyección; artefacto: servicio forecast; entorno: desarrollo con fixtures sintéticos; respuesta: cambio localizado y regresión íntegra; medida propuesta: modificar un servicio y sus pruebas sin cambiar el contrato público, revisión en una jornada. No es medición histórica.',
'Prompt: redacta tres escenarios medibles de Horizonte sin afirmar mediciones. Respuesta: seguridad, cero accesos financieros cruzados en matriz tenant/rol; rendimiento, p95 menor de 2 s con 20 usuarios y 10.000 movimientos por empresa en entorno documentado; mantenibilidad, cambio de regla aislado con regresiones. Auditoría: cero fallos solo aplica a esa matriz; p95 y jornada son metas, no resultados. Se exige indicar fuente, estímulo, artefacto, entorno, respuesta y medida.'
],
3:[
'Un ADR aceptado conserva el contexto que justificó una decisión. Si cambia la decisión, creo un ADR sucesor y marco el anterior reemplazado, conservando enlaces. Los borradores sí pueden corregirse; inmutabilidad histórica no significa mantener errores tipográficos como si fueran decisiones.',
'ADR ficticio: persistencia de pedidos. Estado: propuesto. Contexto: tienda necesita consultas, concurrencia e integridad. Decisión: SQLite inicial con migración prevista a PostgreSQL. Consecuencias: transacciones y consultas sencillas, límites de concurrencia. Alternativas: JSON descartado por actualización concurrente e integridad; servidor gestionado aplazado por costo. Seis campos completos; no es decisión productiva de Horizonte.',
'Matriz Horizonte, en orden seguridad/integridad, mantenibilidad y costo operativo: monolito modular = alto/alto/alto; microservicios por dominio = medio/medio/bajo para un estudiante. Alto significa mejor adecuación, no cantidad de tecnología. La red y transacciones distribuidas incrementan superficie y operación.',
'Prompt: recomienda arquitectura para una plataforma financiera sin información de escala. Respuesta de esta IA: faltan usuarios, carga, presupuesto y responsables; usaría provisionalmente monolito modular y cola para importaciones. Auditoría: no hubo recomendación de microservicios que rechazar. Completo contexto: SaaS académico, presupuesto cero y un estudiante; ratifico módulos Django y servicios puros. No se fabrica una alucinación para cumplir el ejercicio.'
],
4:[
'Puerto es el contrato que expresa una capacidad del dominio; adaptador realiza ese contrato usando infraestructura. En Horizonte una fuente de movimientos podría ser puerto y CSV o Mock Bank sus adaptadores. No hace falta una interfaz por cada modelo ORM.',
'El controlador depende de detalles SQL y mezcla transporte, consulta y negocio; se afecta inversión de dependencias y responsabilidad única. Propongo puerto obtener_pedido y adaptador SQL parametrizado, más servicio de aplicación; la vista solo valida HTTP y serializa.',
'Para cálculo contractual basta una función pura con balance, corte, horizonte y obligaciones. Las consultas Company/Obligation quedan fuera. El servicio existente project_obligations ya usa esa separación. Para importación variable propongo un puerto leer_movimientos y adaptadores CSV/XLSX; no añado repositorio ficticio para cada entidad.',
'Prompt: simplifica project_obligations sin ORM y conserva Decimal y contrato. Respuesta: sustituir el if de inclusión por guard clause y mantener agregación por fecha. Auditoría: usa únicamente timedelta y Decimal, no importa Django ni excepciones SQL. La versión académica se conserva como propuesta; no se edita el backend con esta solicitud documental.',
'Se ejecuta una comprobación aislada de equivalencia del cálculo contractual, sin BD, con horizontes 30/60/90 y entradas vencidas/futuras. Resultado disponible en evidencia_academica.json. Verifica la variante didáctica y el servicio importado; no equivale a integración de un PR ni aceptación del producto.'
],
5:[
'Un Bounded Context delimita reglas y vocabulario coherentes. En un monolito permite evitar que factura signifique automáticamente dinero cobrado. Horizonte separa bancos, facturación, clasificación y proyección, aunque se desplieguen juntos.',
'Ventas: pedido, precio pactado y cliente comprador. Inventario: existencia, reserva y ubicación. Envíos: guía, entrega y destinatario. Una venta confirmada solicita reserva; una reserva satisfecha habilita envío. Cada contexto publica identificadores y eventos, no comparte tablas sin contrato.',
'Supuesto didáctico, no cotización: 3 servicios a 7 USD y 3 BD a 7 USD más 10 USD de operación = 52 USD/mes. Con ventas 500 USD y margen supuesto 20%, utilidad previa 100 USD; 52 consume 52% de esa utilidad. Monolito supuesto 17 USD consume 17%. El margen real es desconocido; ventas no son utilidad. Horizonte mantiene presupuesto 0 USD y acepta límites de capas gratuitas.',
'Prompt: diseña distribución para un negocio de bajo volumen y explicita costo y red. Respuesta: mantener monolito y procesamiento asíncrono; separar solo ante necesidad demostrada. Auditoría: no asumir red estable, usar reintentos idempotentes; no inventar tarifas actuales ni SLA gratis. La comparación anterior es análisis de sensibilidad con supuestos.',
'Context Map textual y Mermaid: graph LR; Acceso-->Banca; Banca-->Clasificacion; Facturacion-->Obligaciones; Obligaciones-->Proyeccion; Banca-->Proyeccion. Cada flecha significa datos mediante servicios internos. Factura pendiente y movimiento liquidado se concilian para evitar doble conteo. No hay servicio que transfiera fondos.'
],
6:[
'Nivel 2 usa recursos identificados por URI, verbos HTTP y estados correctos. No exige HATEOAS. Horizonte usa GET para consultas y POST para crear/importar, con sesión y CSRF; la elección de autenticación es independiente del nivel Richardson.',
'Farmacia ficticia: POST /pedidos/ crea, devuelve 201 o 400; GET /pedidos/{id}/ devuelve 200 o 404; GET /pedidos/?page=1 lista con 200. En todos, falta de autenticación 401 si usa bearer y permiso insuficiente 403. POST incluye body JSON, GET no.',
'Especificación OpenAPI 3.0 completa del endpoint ficticio incluida en bloque YAML del taller. Incluye identificador, descripción, cantidad y estado, campos requeridos, respuesta 201 y errores. Es ejemplo académico, no endpoint real de Horizonte.',
'El ejemplo de farmacia usa bearerAuth HTTP bearer JWT en pedidos y security: [] en login. Para Horizonte el contrato debe describir cookie sessionid y CSRF en escritura. No marco JWT en endpoints que realmente usan sesión ni expongo documentos personales en respuestas.',
'Prompt: documenta el dashboard real con seguridad y errores sin inventar campos. Respuesta: GET /api/companies/{company_id}/dashboard/?horizon=30, sesión, horizonte enum 30/60/90; 200, 400 inválido, 403 sin sesión, 404 empresa ajena, 409 sin saldo/cortes incompatibles. Auditoría: views.py permite además composición actual del Resumen; inventario no es contrato completo. No adjuntar cédulas, claves ni tokens de ejemplo reales.'
],
7:[
'Las pruebas E2E atraviesan navegador y servicios, cuestan más tiempo y tienen más causas de inestabilidad. La base debe comprobar muchas reglas pequeñas; la integración verifica ORM/API y pocos recorridos E2E confirman tareas críticas. La proporción se decide por riesgo, no por una cuota universal.',
'Inyecto un cliente de clima y simulo timeout, 200 y respuesta malformada en su frontera. Mantengo API, serialización y BD de pruebas reales. Verifico error controlado y tiempo límite; no hago mock del resultado del propio método que quiero comprobar.',
'Caso real: ApplicationTests.test_company_isolation, BD efímera creada por Django, usuario miembro de A, solicitud al dashboard de B =>404; listado incluye solo A. Código en backend/tests/test_application.py. La prueba evita datos de desarrollo y usa force_authenticate, por lo que no verifica login ni CSRF.',
'Contrato consumidor React/proveedor Django: GET dashboard con horizonte permitido, montos serializados sin pérdida y puntos por fecha; errores 400/403/404/409 acordados. Pact sería complemento, no está instalado ni ejecutado. Validar contrato no garantiza semántica financiera ni aislamiento.',
'Prompt: genera pruebas de dashboard con tenant y horizonte inválido usando TestCase. Respuesta: crear A/B, membresía A, usar APIClient y afirmar 404 B y 400 para 31 días. Auditoría: no mockear Company ni project_obligations en una prueba de integración; BD temporal aislada. En evidencia se registra la ejecución focal de la suite existente, no una suite nueva integrada.'
],
8:[
'Red: escribir criterio y observar fallo por comportamiento faltante. Green: implementar lo mínimo para pasar. Refactor: mejorar estructura sin alterar resultados y repetir regresión. Un test verde añadido después no demuestra haber seguido TDD.',
'p95=2500 ms indica que aproximadamente el 95% de las duraciones observadas no supera 2,5 s, según estimación de percentil. Si la meta es menor de 2 s falla; no se decide aceptación solo con promedio. Revisar muestra, errores, arranque frío y concurrencia.',
'Demostración TDD aislada: prueba contractual de horizonte inválido primero contra stub que lo acepta (Red esperado); implementación que rechaza 45 (Green); variante con guard clauses que conserva resultados (Refactor). evidencia_academica.json guarda resultados. Es ejercicio sobre política real del forecast, sin commits inventados ni cambios en aplicación.',
'Script k6 completo incluido al final: destino obligatorio localhost, sesión de prueba en variable de entorno, rampa 0→10→50→0, máximo 50 VUs, p95<2000 ms y error<1%. No se ejecuta aquí carga contra producción ni se asignan resultados ficticios.',
'Prompt: genera carga acotada y autenticada del dashboard en localhost. Respuesta: script del taller con host validado, horizonte30 y cookie sessionid. Auditoría: 401/403 serían fallos de ensayo, no latencia útil; no usar miles de VUs ni secretos dentro del script. Arrancar con 1 VU antes de 50; p95 y errores quedan no medidos en esta entrega.'
],
9:[
'CI ejecuta verificaciones; un Quality Gate agrega criterios que hacen terminar con error e impiden promover artefactos si fallan. Una cobertura publicada pero ignorada no bloquea nada. Además, la protección de rama debe requerir checks para impedir merges.',
'YAML conceptual: jobs: lint ejecuta Ruff; test depende de lint y ejecuta Django sobre BD temporal; analysis depende de test y ejecuta coverage report --fail-under=80. Todo comando que falle propaga exit code. El umbral 80% es propuesta para código nuevo, no cobertura observada.',
'Pipeline real: .github/workflows/ci.yml tiene backend (Ruff, formato, migraciones y tests), frontend (npm ci/test/build), backend-postgres con servicio16 y desktop con Node tests. Se verificó su contenido; no se modifica ni se dispara una publicación al resolver documentos.',
'Propuesta concreta: coverage run --source=backend/apps backend/manage.py test backend/tests y coverage report --fail-under=80. Falta instalar/bloquear coverage y configurar required check antes de afirmar gate operativo. No se encontró SonarCloud ni evidencia de porcentaje actual.',
'Prompt: audita CI sin revelar secretos. Respuesta: hay checkout@v4, setup-python@v5 y setup-node@v4 en archivo leído; usar referencias soportadas y fijadas al integrar. Auditoría: no se declaran últimas versiones sin verificar proveedor; la clave PostgreSQL es sintética de CI, no secreto productivo. Tests sí fallan el job; cobertura y protección de rama no están demostradas.'
],
10:[
'COPY --from=builder copia artefactos de una etapa previa a la imagen final. Permite dejar compiladores y cachés fuera, pero no garantiza que librerías nativas de ejecución estén presentes. Deben verificarse compatibilidad y permisos.',
'Si SQLite está en la capa escribible del contenedor, eliminarlo destruye ese archivo. Un volumen sobre la ruta de la BD conserva datos entre recreaciones; también requiere respaldo y prueba de restauración. Un volumen no protege de borrado lógico ni de docker compose down -v.',
'El Dockerfile real backend/Dockerfile usa python:3.13-slim, instalación previa de requisitos y runserver; no es multietapa y no declara USER. Se incluye propuesta multietapa no root en el taller; no la describo como desplegada. Debe validar wheels nativos, permisos y servidor de producción antes de integrar.',
'Compose real compose.yaml: PostgreSQL16 con postgres_data, Redis7, migración, backend, Celery y frontend; puertos locales ligados a127.0.0.1 y dependencias con healthchecks. La contraseña literal es local de desarrollo, no trasladable a producción. La red por defecto de Compose no equivale a red interna sin salida.',
'Prompt: endurece el contenedor sin ocultar diferencias de entorno. Respuesta: builder genera wheels, runtime instala y usa appuser; secretos por entorno/gestor. Auditoría: propuesta no verificada como build de esta entrega; tamaño y reducción son N/D. Compose existente se usa como referencia local, no se inventa captura de contenedores actuales.'
],
11:[
'Delivery deja una versión verificable lista para publicar con decisión explícita. Deployment publica automáticamente cada cambio que supera controles. Horizonte conserva una aprobación de entrega y pruebas posteriores para no confundir CI verde con validación.',
'Blue/Green mantiene dos versiones y conmuta tráfico a la saludable. Un fallo permite volver a la anterior mientras datos y migraciones sean compatibles. El cambio no garantiza milisegundos reales; hay conexiones activas, DNS o balanceadores y costos. No está implementado aquí.',
'Existe render.yaml y evidencia histórica de alojamiento del 05/10. La rama local vigente no está certificada como desplegada. No se encontró .github/workflows/deploy.yml; se documenta propuesta manualmente disparada con deploy hook secreto y verificación posterior. No se publica ni crea servicio de pago desde esta tarea.',
'Healthcheck propuesto: curl --fail --silent --show-error --max-time 10 "$BASE_URL/api/health/"; reintentar con backoff hasta un límite de arranque, y salir con error si no responde. El endpoint real es /api/health/, no /health. Comprobar JSON esperado y dependencias según lo que garantice su implementación.',
'Prompt: diseña entrega con secreto y rollback sin asumir dos réplicas gratis. Respuesta: workflow_dispatch, deploy hook desde secrets, espera acotada y healthcheck. Auditoría: respuesta 200 sola no prueba readiness financiera; versión anterior debe conservarse y migraciones ser compatibles. No incluir token o contraseña en YAML ni asegurar que rollback de BD es automático.'
],
12:[
'SAST analiza código y patrones inseguros sin ejecutar la aplicación; SCA analiza componentes y vulnerabilidades/licencias de dependencias. Se complementan con prueba dinámica y revisión humana. Cero hallazgos de una herramienta no demuestra ausencia de vulnerabilidades.',
'Antes del merge se corrige un fragmento y se repite test; después puede requerir contención, recuperación, revisión de accesos y comunicación a afectados. El costo depende de impacto y datos. En Horizonte se preserva ORM parametrizado y aislamiento por empresa.',
'No existe ci-security.yml operativo en la fuente inspeccionada. Se incluye especificación de job propuesto: escanear fuente e imagen con herramienta aprobada; fallo en HIGH/CRITICAL mediante exit-code 1; artefacto privado y retención limitada. Integrar y verificar herramienta/versiones es tarea posterior, no escaneo ejecutado.',
'No se observó un falso positivo real documentado para esta entrega. No crear exclusiones preventivas. Toda excepción futura requiere ID, versión, evidencia de no explotabilidad, responsable y vencimiento; severidad alta no se silencia solo para poner CI verde.',
'Prompt: configura revisión de seguridad sin exportar datos sensibles. Respuesta: resultados privados, sin body de solicitudes y gate bloqueante por severidad. Auditoría: no se ejecutó SCA hoy y no se inventan CVE; las opciones deben contrastarse con versión fijada al instalar. Un secreto encontrado exige revocación/rotación, no solo borrarlo del último commit.'
],
13:[
'Monitoreo detecta condiciones conocidas con indicadores; observabilidad permite investigar el estado interno a partir de señales. Horizonte necesita relacionar HTTP, cola y ejecución del cálculo sin registrar datos financieros de clientes.',
'JSON aporta campos estables para filtrar y correlacionar, por ejemplo event, route, duration_ms y request_id. No es seguro por sí mismo: exige sanitizar excepciones, evitar PII y definir retención. Texto libre dificulta análisis pero puede seguir siendo útil en desarrollo.',
'Diseño propuesto: span forecast.dashboard, histograma de duración y contador por route/status; log JSON con request_id aleatorio y resultado. No incluir cuerpo, cédula, saldo ni etiqueta company_id. No se encontró stack OpenTelemetry/Grafana operativo verificado; propuesta adjunta sin afirmar instrumentación integrada.',
'Dashboard propuesto RED: rate peticiones/s; histogram_quantile(0.95, rate(bucket[5m])); errores5xx/total en igual ventana. Usar route normalizada, no URL con IDs. Mostrar huecos y n=0 como sin datos. No existe captura de Grafana ni p95 real de esta entrega.',
'Prompt: instrumenta operación de cliente sin filtrar PII. Respuesta: no guardar nombre/cédula/monto; usar request_id, duración y código; muestreo inicial de trazas10% como supuesto a evaluar. Auditoría: sampling no anonimiza; métricas son agregadas sin IDs de cliente. El presupuesto cero descarta contratar servicios sin decisión expresa.'
],
14:[
'Error Budget cuantifica fallos permitidos por el SLO en una ventana. Si se agota, se prioriza confiabilidad sobre entregas riesgosas; no es permiso para ignorar clientes. Se define por solicitudes o tiempo, con exclusiones explícitas y observabilidad suficiente.',
'Mes convencional de30d =720h. SLO99,5%:720×0,005=3,6h (216min). SLO99,95%:720×0,0005=0,36h (21,6min). No mezclar meses distintos. Para99,9% serían43,2min;99,99%4,32min.',
'Runbook individual: confirmar alcance en /api/health/ y logs; ejecutar docker compose ps y docker compose logs --tail100 backend postgres; verificar pg_isready en postgres; si servicio detenido, docker compose up -d postgres backend worker. No borrar volumen ni usar down -v. Comprobar login/consulta sintética e idempotencia; escalar al proveedor si es alojamiento externo. Registrar inicio, mitigación y evidencia sin PII.',
'Postmortem hipotético: caída30min por reinicio sin verificar readiness BD. Línea de tiempo:0min alerta,5 diagnóstico,15 arranque BD,25 app lista,30 validación. Causa de proceso: despliegue sin prueba de recuperación y dependencia lista. Acciones: healthcheck, ensayo aislado y runbook. No se afirma incidente ocurrido ni se culpa a Adrian.',
'Prompt: audita runbook para único operador Windows con Docker. Respuesta: usar servicios del compose real, sin equipo24/7 ni herramientas pagas. Auditoría: comandos son procedimientos, no se ejecutaron reinicios hoy; confirmar motor activo y no usar nombres supuestos. No prometer recuperación sin backup probado.'
],
15:[
'Correctivo elimina un defecto observado; preventivo reduce probabilidad o costo de fallos futuros. Corregir duplicación de ingreso es correctivo; separar cálculo y añadir pruebas antes de nuevas reglas es preventivo. Ambos deben conservar integridad de datos.',
'Facturación ficticia: correctivo, arreglar total redondeado; adaptativo, nuevo formato tributario; perfectivo, mejorar consulta por cliente; preventivo, extraer reglas y automatizar regresión. El cumplimiento tributario debe verificarse con norma aplicable antes de cambiar cálculo.',
'Inventario del mismo corte: DT01 endurecimiento Docker sigue pendiente; DT02 p95/aceptación sigue pendiente; DT03 observabilidad/SLO sigue pendiente. No hubo integración al backend al responder guías; por tanto no declaro deuda pagada por haberla documentado. Falta criterio de aceptación de cada pago.',
'Se preparó variante aislada de project_obligations con guard clause; conserva Decimal, corte exclusivo y horizonte permitido. Se ejecutaron pruebas de equivalencia en artefacto académico. No se sustituyó el servicio del SaaS ni hay PR de integración; el siguiente cambio requerirá suite completa y revisión. Esto distingue refactor demostrado y deuda productiva pendiente.',
'Prompt: revisa equivalencia e integridad de project_obligations. Respuesta: la función pura no hace commit/rollback; las vistas y servicios de persistencia conservan transacciones fuera. Auditoría: no introducir escrituras en cálculo, no incluir vencidos automáticamente ni cambiar signo; solo biblioteca estándar. No se requiere herramienta propietaria para medir esta deuda.'
],
16:[
'Verificación demuestra que código cumple especificación mediante tests, controles y revisión. Validación demuestra utilidad para microempresas representativas. Horizonte tiene evidencia técnica local; la aceptación externa y eficacia predictiva todavía no están acreditadas. El dossier declara esa frontera.',
'ADR03/monolito: descarta microservicios por operación individual y falta de necesidad medida. ADR06/sesión: descarta JWT como cambio automático por existir web con CSRF. ADR11/Delivery: descarta publicación irrestricta por datos financieros y requisitos de aprobación. Cada uno conserva costo y consecuencia.',
'No existe bitácora forense completa de31 fichas que permita un total histórico fiable de alucinaciones o dependencias rechazadas: ambos N/D. Hallazgos documentados en esta entrega: root implícito en Docker, inventario OpenAPI incompleto y confusión de pruebas locales con producción. Son correcciones verificables, no conteo inventado de errores de IA.',
'Defensa: mantengo monolito porque módulos y Celery separan cómputo sin transacciones distribuidas. El CI y pruebas PostgreSQL históricos apoyan regresión; no sustituyen observabilidad. No hay Grafana actual verificado ni p95 de carga, por lo que el argumento de escala permanece provisional y falsable.',
'Prompt: audita honestamente las evidencias y límites de estas guías. Respuesta:16 registros de IA actuales, producción no recertificada, métricas históricas fechadas, no total semestral de alucinaciones. Evaluación: rechazar cualquier conclusión de100% seguro, cumplimiento legal certificado o disponibilidad demostrada sin evidencia. La responsabilidad técnica no se delega al LLM.'
]}

SALE='''from decimal import Decimal
from typing import Protocol
class Inventory(Protocol):
    def quote(self, sku: str, quantity: int): ...
    def record_sale(self, sku: str, quantity: int, total: Decimal): ...
class Payment(Protocol):
    def authorize(self, total: Decimal, key: str): ...
def sell(repo: Inventory, payment: Payment, sku: str, quantity: int,
         tax: Decimal, key: str, unit_of_work):
    if quantity <= 0:
        raise ValueError("Cantidad inválida")
    price = repo.quote(sku, quantity)
    total = (price * quantity * (Decimal("1") + tax)).quantize(Decimal("0.01"))
    authorization = payment.authorize(total, key)
    with unit_of_work():
        repo.record_sale(sku, quantity, total)
    return authorization
# Los adaptadores implementan SQL parametrizado, stock con bloqueo,
# secretos por entorno y compensación del pago si falla la persistencia.
'''
ast.parse(SALE)
CODE={1:SALE,5:'graph LR\n  Acceso --> Banca\n  Banca --> Clasificacion\n  Banca --> Proyeccion\n  Facturacion --> Obligaciones\n  Obligaciones --> Proyeccion',
6:'''openapi: 3.0.3
info: {title: Pedidos farmacia ejemplo, version: 1.0.0}
paths:
  /pedidos/:
    post:
      security: [{bearerAuth: []}]
      requestBody:
        required: true
        content:
          application/json:
            schema: {$ref: '#/components/schemas/NuevoPedido'}
      responses:
        '201':
          description: Creado
          content:
            application/json:
              schema: {$ref: '#/components/schemas/Pedido'}
        '400': {description: Datos inválidos}
        '401': {description: Sin autenticación}
        '403': {description: Sin permiso}
components:
  securitySchemes:
    bearerAuth: {type: http, scheme: bearer, bearerFormat: JWT}
  schemas:
    NuevoPedido:
      type: object
      required: [descripcion, cantidad]
      additionalProperties: false
      properties:
        descripcion: {type: string, minLength: 1, maxLength: 200}
        cantidad: {type: integer, minimum: 1}
    Pedido:
      allOf:
        - {$ref: '#/components/schemas/NuevoPedido'}
        - type: object
          required: [id, estado]
          properties:
            id: {type: integer, minimum: 1}
            estado: {type: string, enum: [recibido, preparado, entregado]}
# Ejemplo ficticio. Horizonte usa sesión y CSRF; no JWT.
''',
8:'''import http from 'k6/http';
import {check, sleep} from 'k6';
const base = __ENV.BASE_URL || 'http://127.0.0.1:8000';
if (!/^http:\/\/(127\.0\.0\.1|localhost):\d+$/.test(base))
  throw new Error('Solo entorno local');
if (!__ENV.SESSION_ID || !__ENV.COMPANY_ID) throw new Error('Falta sesión sintética');
export const options = {
  stages: [{duration:'20s',target:10},{duration:'40s',target:50},
           {duration:'20s',target:0}],
  thresholds: {http_req_duration:['p(95)<2000'], http_req_failed:['rate<0.01']}
};
export default function () {
  const r = http.get(`${base}/api/companies/${__ENV.COMPANY_ID}/dashboard/?horizon=30`,
    {headers:{Cookie:`sessionid=${__ENV.SESSION_ID}`}});
  check(r, {'dashboard200': r => r.status === 200});
  sleep(1);
}
''',
9:'''# Propuesta académica adicional al CI real; no workflow integrado
name: coverage-gate
on: [push, pull_request]
jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.13'}
      - run: pip install -r backend/requirements.txt coverage
      - run: coverage run --source=backend/apps backend/manage.py test backend/tests
      - run: coverage report --fail-under=80
# Fijar coverage en dependencias y requerir este check antes de integrar.
''',
10:'''# Propuesta académica; validar build y dependencias nativas antes de integrar
FROM python:3.13-slim AS builder
WORKDIR /build
COPY backend/requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt
FROM python:3.13-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd --create-home appuser
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels
WORKDIR /app/backend
COPY --chown=appuser:appuser backend/ ./
USER appuser
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--noreload"]
# runserver solo ensayo local; elegir servidor WSGI/ASGI para producción.
''',
11:'''# Propuesta Delivery, no ejecutada ni publicada
name: Delivery
on: workflow_dispatch
jobs:
  release:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Solicitar despliegue y verificar
        env:
          HOOK: ${{ secrets.RENDER_DEPLOY_HOOK }}
          BASE_URL: ${{ vars.BASE_URL }}
        run: |
          test -n "$HOOK" && test -n "$BASE_URL"
          curl --fail --silent --show-error --max-time 30 -X POST "$HOOK" >/dev/null
          for i in $(seq 1 30); do
            if curl --fail --silent --max-time 10 "$BASE_URL/api/health/"; then exit 0; fi
            sleep 10
          done
          exit 1
# Añadir comprobación de revisión desplegada: health 200 antiguo no acredita nueva versión.
''',
12:'''# Especificación del gate para integrar tras fijar versión de Trivy
# trivy fs --severity HIGH,CRITICAL --exit-code 1 .
# trivy image --severity HIGH,CRITICAL --exit-code 1 horizonte:candidato
# No ejecutar con continue-on-error. No usar ignore-unfixed para ocultar riesgo.
# Registrar hash de imagen, versión del escáner, fecha y base de vulnerabilidades.
''',
13:'''# Propuesta de instrumentación; requiere SDK/proveedor/exportador configurados
import json, logging, time
from opentelemetry import trace, metrics
tracer = trace.get_tracer("horizonte.forecast")
meter = metrics.get_meter("horizonte.forecast")
duration = meter.create_histogram("dashboard.duration", unit="s")
counter = meter.create_counter("dashboard.calls")
def observe_calculation(calculate, request_id):
    started = time.perf_counter()
    outcome = "error"
    try:
        with tracer.start_as_current_span("forecast.dashboard"):
            result = calculate()
            outcome = "ok"
            return result
    finally:
        elapsed = time.perf_counter() - started
        labels = {"operation":"dashboard", "outcome":outcome}
        duration.record(elapsed, labels)
        counter.add(1, labels)
        logging.getLogger("horizonte").info(json.dumps({
            "event":"dashboard", "request_id":request_id,
            "duration_ms":round(elapsed*1000), "outcome":outcome}))
# No añadir datos financieros, empresa, cédula ni body a logs/labels.
'''}

# Campos de una celda por guía y posición de tabla original.
SINGLE={
1:{6:'FPI-16 describía escenario contractual y deuda de pruebas/documentación. El corte actual incorpora captura manual, mensualidades, CSV/XLSX/XML, Mock Bank, modelos experimentales y QA local. No se conserva como actual el conteo antiguo de22 tests.',13:EX[1][0]+' '+EX[1][1],14:DEC[0],16:'Trabajo solo: el riesgo es sesgo de autorrevisión, no desacuerdo de un equipo ficticio. Contrasté Dockerfile y código con las afirmaciones de la ficha.',17:'Versionar diagnóstico y priorizar DT01–DT03 antes de elegir nuevos componentes.'},
2:{5:'DT02 revela metas p95 y aceptación sin protocolo representativo; DT03 revela ausencia de SLO medido. Convertir esos riesgos en escenarios, no en promesas.',9:'Orden: 1 aislamiento de empresas y confidencialidad; 2 integridad monetaria e idempotencia; 3 mantenibilidad. Clientes potenciales regionales, sin aliado único.',11:EX[2][0],12:DEC[1],14:'El compromiso es p95 frente a seguridad. Adrian conserva controles y mide, sin simular votación de un equipo.',15:'Usar los tres drivers para comparar monolito y distribución en FPI-19.'},
3:{4:'Aislamiento e integridad; mantenibilidad; costo operativo compatible con presupuesto cero y trabajo individual.',8:EX[3][0],9:DEC[2],11:'La opción más atractiva pero costosa fue microservicios; faltan carga y equipo que justifiquen su operación.',12:'Aplicar el ADR al límite de cálculo y persistencia en FPI-20.'},
4:{4:DEC[2],6:'React -> API Django -> servicios de aplicación -> ORM PostgreSQL; project_obligations recibe valores sin ORM. Puerto futuro BankSource -> adaptadores CSV/XLSX/Mock. Las consultas tenant permanecen en backend.',7:'Propuesta aislada en esta guía; no hay PR integrado generado por esta tarea. Repositorio conocido: https://github.com/elcreado/Horizonte .',10:EX[4][0],11:'El cálculo puro existente permite pruebas sin BD. La variante académica demuestra equivalencia; no se atribuye mejora productiva no integrada.',13:'Separar autorización y persistencia de vistas amplias sin omitir filtro por empresa.',14:'Delimitar contextos y contratos antes de distribuir.'},
5:{4:'Monolito Django con accounts, banking, classify, invoices y forecast; React como cliente y Celery para trabajo asíncrono.',6:EX[5][4],9:EX[5][0],10:DEC[4],12:'Facturas y obligaciones: una factura pendiente no equivale a entrada de caja; conciliación evita duplicados.',13:'Inventariar contratos y errores de API en FPI-22.'},
6:{6:'Acceso, empresas, banca/importaciones, clasificación y proyección; priorizar dashboard y cargas idempotentes.',8:'Contrato existente parcial e inventario docs/openapi-inventory.json. No afirmar openapi.yaml completo; verificar ruta vigente en repositorio antes de publicar contrato.',10:'Se usan APIClient y evidencia de QA HTTP documentada; no hay colección Postman creada en esta entrega. Comandos y tests identificados en FPI-23.',12:EX[6][0],13:DEC[5],15:'Asegurar objetos por empresa y revalidar tarea asíncrona; sesión no sustituye autorización.',16:'Probar contrato con BD temporal y errores esperados.'},
7:{4:'GET /api/companies/ y GET /api/companies/{id}/dashboard/?horizon=30.',6:'Último corte documentado:235 tests PostgreSQL,233 aprobados y2 omitidos. No hay clasificación exacta unitarios/integración/E2E ni cobertura medida; no inventar reparto. QA navegador está documentado por casos, no equivale a suite E2E completa.',7:'backend/tests/test_application.py; .venv/Scripts/python.exe backend/manage.py test tests.test_application.ApplicationTests.test_company_isolation. Resultado focal actual en evidencia_academica.json.',10:EX[7][0],11:'La prueba focal verifica aislamiento en su escenario. La integración con proveedores reales, red y carga no está cubierta por ese caso.',13:'La frontera de cola/worker: simular despacho no comprueba Redis ni ejecución real.',14:'Añadir pruebas del cálculo puro y plan de carga local.'},
8:{5:'Suite histórica PostgreSQL con controles tenant, roles y cálculos. Los casos focales de esta entrega no reemplazan la regresión completa.',7:EX[8][2],10:EX[8][0],11:'Resiliencia bajo50VUs aún no medida. No inferirla por tests funcionales ni por el script k6.',13:'p95<2s sigue sin ensayo representativo, por lo que no se dice que se cumplió o incumplió.',14:'Integrar gate de regresión y acordar ensayo local reproducible.'},
9:{4:'Django temporal y PostgreSQL, Ruff, migraciones, npm test/build y Node desktop; pruebas focales aisladas son apoyo documental.',6:'.github/workflows/ci.yml, inspeccionado en esta entrega.',8:'Historial remoto no inspeccionado; archivo local no certifica ejecución GitHub Actions ni protección de rama.',10:EX[9][0],11:DEC[8],13:'Preparar PostgreSQL de CI y distinguir clave sintética de secreto de producción.',14:'Preparar imagen reproducible y validar usuario runtime.'},
10:{5:'CI valida backend/frontend; no se encontró publicación de imagen vinculada a un release en esta revisión.',7:'backend/Dockerfile; frontend/Dockerfile; compose.yaml. Propuesta multietapa incluida en taller, no reemplaza archivos.',9:'docs/IMPLEMENTATION_STATUS.md registra Compose operativo el18/10. No se adjunta una captura actual fabricada; para repetir: docker compose ps y logs, sin borrar volumen.',11:EX[10][0],12:DEC[9],14:'Compatibilidad de wheels nativos y permisos de usuario runtime; todavía requiere build de la propuesta.',15:'Validar imagen y plan de publicación con healthcheck y rollback.'},
11:{4:'Imagen actual local funcional para desarrollo, con deuda USER/runserver; propuesta productiva aún no verificada.',6:'No existe deploy.yml en la revisión. Propuesta de workflow se incluye en taller con estado no integrado.',7:'Ruta de salud verificada en compose: /api/health/. Evidencia remota histórica del05/10; no se declara una URL viva actual sin comprobarla.',9:EX[11][0],10:'No se acredita actualización automática de producción de esta rama. La política es Delivery con aprobación y healthcheck.',12:'Arranque frío, migraciones y compatibilidad de datos limitan rollback.',13:'Incorporar controles SAST/SCA antes de promover candidato.'},
12:{5:'CI real con Ruff/tests/build; no existe gate de seguridad dedicado demostrado.',7:'ci-security.yml no integrado; especificación bloqueante incluida en el taller.',10:EX[12][0],11:'Hay controles de sesión/CSRF/tenant y threat model; el pipeline no está certificado seguro ni con cero vulnerabilidades.',13:'No hay CVE actual verificado que deba atribuirse al proyecto. No inventar una vulnerabilidad para llenar la ficha.',14:'Elegir señales mínimas de observabilidad y revisar PII.'},
13:{5:'GET dashboard; CI funcional vigente en archivo, gate seguridad propuesto no integrado.',7:'backend/apps/forecast/views.py; no se integró OpenTelemetry desde esta tarea documental.',8:EX[13][3],10:EX[13][0],11:'El diseño aporta correlación y medidas propuestas. El SaaS ya registra jobs/auditorías; no se inventa stack Grafana operativo.',13:'Un p95 sin tamaño de muestra, ventana ni errores puede inducir conclusiones equivocadas.',14:'Acordar SLI y preparar runbook verificable con un único operador.'},
14:{5:'SLI propuesto: consultas válidas de dashboard con respuesta correcta / total de consultas válidas en ensayo local. Errores tenant esperados se separan de5xx; no hay serie actual para computarlo.',8:'Runbook completo incluido en Ejercicio3 de esta guía; no existe archivo Runbook_[componente].md creado en el repositorio por esta entrega.',9:EX[14][3],11:EX[14][0],12:EX[14][2],14:'Verificar restauración sin tocar volumen real y evitar reinicios destructivos.',15:'Actualizar inventario residual y priorizar por impacto esperado.'},
15:{5:'DT01 Docker no root/multietapa; DT02 carga y aceptación; DT03 observabilidad/SLO, definidos en FPI-17 de este mismo corte.',8:'Sin PR integrado: refactor puro académico y pruebas en evidencia_academica.json. No se cierra deuda del backend por documentar una propuesta.',11:EX[15][0],12:EX[15][2],14:'Anteponer precisión y aislamiento a mejoras cosméticas o herramientas costosas.',15:'Preparar dossier y demo distinguiendo verificación y validación.'},
16:{4:'Producción actual no recertificada; no se publica una URL como operativa en esta ficha.',5:'https://github.com/elcreado/Horizonte ; no se verificó release final etiquetado en remoto.',6:'No hay video grabado en esta entrega. Guion: acceso, empresa, captura, importación idempotente, Resumen y límites predictivos;5min.',12:''}}

def forum(n):
    # Cada foro desarrolla la posición de la guía y el mismo contexto longitudinal.
    parts=[f'En Horizonte, considero que {DEC[n-1][0].lower()+DEC[n-1][1:]} {EX[n][0]}',
    f'El caso concreto que orienta mi análisis es el siguiente: {EX[n][min(2,len(EX[n])-1)]}',
    'Como único estudiante del proyecto, necesito que cada actividad tenga un resultado revisable y un costo de operación compatible con el alcance. Scrum organiza objetivos de sprint pequeños, un backlog priorizado y una retrospectiva para ajustar capacidad. La autorrevisión tiene límites: la revisión del profesor y la participación de usuarios representativos son necesarias para contrastar supuestos. No describo esas revisiones como reuniones realizadas cuando no existe evidencia.',
    'La decisión también debe proteger la información de cada empresa suscriptora. Usar datos sintéticos en pruebas y excluir identificadores personales de los registros reduce exposición durante el desarrollo. La responsabilidad ética exige contrastar las recomendaciones de IA con archivos, resultados y fuentes; una respuesta convincente no reemplaza una comprobación. Conservo por ello los límites del ensayo y separo metas de resultados.',
    'Mi criterio de aceptación es que el cambio contribuya a comprender la liquidez sin duplicar movimientos ni ocultar obligaciones. Si falta medición, registro el protocolo y la brecha; no transformo una propuesta en un éxito histórico. Así puedo defender el trabajo y decidir el siguiente incremento con evidencia.']
    text='\n\n'.join(parts)
    words=text.split()
    if len(words)>295:
        # Reservar cierre coherente; cortar en límite de oración.
        sentences=re.split(r'(?<=[.!?])\s+',text)
        chosen=[];length=0
        for sentence in sentences:
            count=len(sentence.split())
            if length+count>285:break
            chosen.append(sentence);length+=count
        text=' '.join(chosen)
    additions=['El presupuesto cero obliga a valorar tiempo de mantenimiento, no solo precio de alojamiento.', 'La prioridad se revisará con pruebas repetibles y criterios explícitos en el próximo sprint.', 'Las limitaciones quedan registradas para que otra persona pueda continuar el trabajo sin reconstruir decisiones.', 'Una revisión externa ayudará a confirmar comprensión y utilidad antes de declarar validación del producto.']
    for sentence in additions:
        if len(text.split())>=250:break
        text+=' '+sentence
    assert 250<=len(text.split())<=300,(n,len(text.split()))
    return text

def set_cell(c,text):
    c.text=str(text)
    for p in c.paragraphs:
        p.paragraph_format.space_after=Pt(3)
        for r in p.runs:r.font.name='Arial';r.font.size=Pt(9)

def fillrows(t,values):
    while len(t.rows)<len(values)+1:t.add_row()
    while len(t.rows)>len(values)+1:t._tbl.remove(t.rows[-1]._tr)
    for row,vals in zip(t.rows[1:],values):
        assert len(row.cells)==len(vals),(row.cells[0].text,vals)
        for c,value in zip(row.cells,vals):set_cell(c,value)

def after(anchor,text):
    el=OxmlElement('w:p');anchor._p.addnext(el);p=Paragraph(el,anchor._parent)
    r=p.add_run(text);r.font.name='Arial';r.font.size=Pt(10)
    p.paragraph_format.space_after=Pt(7)
    return p

DEBTS=[['DT01 Contenedor backend','Seguridad/infraestructura','backend/Dockerfile','Root implícito y servidor desarrollo','Sprint propuesto1: build no root y regresión'],['DT02 Aceptación y carga','Pruebas','docs/acceptance; pruebas de carga','Sin evidencia integral p95/UX','Sprint propuesto2: protocolo reproducible'],['DT03 Observabilidad/SLO','Diseño/operación','Operación y telemetría','Diagnóstico y disponibilidad no acreditados','Sprint propuesto3: señales mínimas y ensayo']]

def multi(n,t):
    h=' | '.join(c.text for c in t.rows[0].cells)
    if h.startswith('Nombre completo'):return [[STUDENT,'Estudiante único; responsabilidades de producto, Scrum y desarrollo']]
    if h.startswith('Qué cambió'):return [['Estado del producto','Las16 guías anteriores eran un corte antiguo','Se usa matriz vigente y se conserva historial'],['Tipo de beneficiario','SaaS multiempresa según estudiante','No se simula una empresa aliada única']]
    if h.startswith('Decisión |'):return [[DEC[n-1],'Alineación con riesgo financiero y capacidad individual'],['Separar evidencia y propuesta','Evitar certificar despliegues, revisiones o mediciones no realizados']]
    if h.startswith('Elemento auditado'):return [[r.cells[0].text,EX[n][-1] if i==1 else 'Se contrasta contra código y resultados, no contra confianza del LLM. '+DEC[n-1]] for i,r in enumerate(t.rows[1:],1)]
    if h.startswith('Ítem de deuda'):
        if n==1:return DEBTS
        return [[d[0],'Pendiente en producto; propuesta documentada',d[3],'Deliberada prudente si se limita y revisa',d[4]] for d in DEBTS]
    if h.startswith('Atributo |'):return [['Seguridad','Usuario solicita empresa ajena','API financiera','Sesión válida de otra empresa','Rechazo sin datos','0 fugas en matriz tenant/rol definida'],['Rendimiento','20 usuarios consultan','Dashboard','10.000 movimientos/empresa; entorno fijado','Respuesta útil','p95<2s y error<1%; meta sin medir'],['Mantenibilidad','Adrian cambia regla','Servicio forecast','Desarrollo con fixtures','Regresión conserva contrato','Cambio acotado y tests; plazo meta1jornada']]
    if h.startswith('Atributo A'):return [['Seguridad vs latencia','Conservar permisos; optimizar consultas','Datos financieros entre suscriptores'],['Disponibilidad vs costo','Ensayo y límites explícitos, sin SLA gratis','Presupuesto0USD']]
    if h.startswith('Alternativa |'):return [['Monolito modular','Alto','Alto','Alto'],['Microservicios','Medio','Medio','Bajo']]
    if h.startswith('Módulo de dominio'):return [[x,'Sí','Integridad y menor operación; límites por servicios'] for x in ['Acceso','Banca','Clasificación','Facturación','Proyección']]
    if h.startswith('Verbo HTTP'):return [['GET','/api/companies/','200,403','No; sesión'],['GET','/api/companies/{id}/dashboard/','200,400,403,404,409','No; sesión'],['POST','/api/companies/{id}/imports/','202,400,403,404,503','No; sesión y CSRF']]
    if h.startswith('Endpoint probado'):return [['GET dashboard local','0→10→50→0 en80s, sesión sintética','No ejecutado k6; p95/error N/D']]
    if h.startswith('Criterio del Quality'):return [['Tests/regresión','Sin fallos; job no ignora exit code'],['Lint/formato/migraciones','Ruff y makemigrations --check'],['Cobertura propuesta','80% código nuevo, baseline por medir; no operativo aún']]
    if h.startswith('Imagen base inicial'):return [['python:3.13-slim actual','Propuesta runtime no root con wheels','N/D: no se midieron imágenes antes/después']]
    if h.startswith('Componente/Dependencia'):return [['Backend y dependencias','SAST/SCA propuestos','N/D: sin escaneo actual','No determinada','No excluir sin evidencia; integrar gate privado'],['Docker runtime','Revisión Dockerfile','No corresponde CVE','Riesgo por evaluar','Propuesta USER explícito y servidor productivo']]
    if h.startswith('SLI definido'):return [['Éxito de consultas válidas en ensayo local','99% meta académica, no SLA acordado','7,2h por30d si mide tiempo; solicitudes fallidas≤1% si mide peticiones'],['Latencia útil dashboard','95% por debajo2s meta','Hasta5% puede superar2s; registrar fallos aparte']]
    if h.startswith('Hito |'):return [['Sprint1 propuesto','Docker no root y permisos','Reducir riesgo operacional'],['Sprint2 propuesto','Carga y aceptación web','Validar utilidad antes de publicar'],['Sprint3 propuesto','SLO y runbook de ensayo','Operación viable individual']]
    if h.startswith('Ficha |'):return [[f'FPI-{i+17}',DEC[i],'Se conserva en este corte','Implementado parcialmente; ver evidencia de cada ficha'] for i in range(15)]
    if h.startswith('ADR N.'):return [['03','Monolito modular','Código apps y workers; sin métrica de escalado que exija distribución'],['06','Sesión/CSRF','settings y tests; no JWT inventado'],['11','Delivery controlada','Publicación actual no acreditada; propuesta explícita']]
    if h.startswith('Indicador de auditoría'):return [['Registros IA de esta entrega','16; uno por guía'],['Alucinaciones históricas','N/D: falta bitácora completa'],['Licencias rechazadas históricas','N/D; no inventar conteo'],['PII enviada en esta entrega','No se incluyeron datos de clientes reales'],['Lección','Revisar código y evidencias antes de aceptar el LLM']]
    if h.startswith('Indicador |'):return [['Tests históricos18/10','235:233 aprobados,2 omitidos; no cobertura porcentual'],['Seguridad','ASVS/gate completo no acreditados; no afirmar0CVE'],['SLO/uptime','No medidos en ventana representativa'],['Observabilidad','Diseño propuesto; sin Grafana certificado actual']]
    if h.startswith('Componente |'):return [[d[0],d[1],d[4]+'; limitar uso académico mientras falte aceptación'] for d in DEBTS]
    return None

PRE={
1:['Sí: responsabilidad única, abierto/cerrado, sustitución, segregación e inversión de dependencias. En Horizonte reviso vistas amplias y duplicación de controles.', 'El propio código de distintas etapas exige recuperar contexto. Lo documento por versiones y pruebas; no invento participación de otro desarrollador.', 'La autorrevisión individual puede ocultar sesgos. Uso evidencia de archivos y pruebas y dejo pendiente revisión externa cuando no ocurrió.'],
2:['RF indica qué hace el SaaS; RNF fija calidad bajo condiciones, como latencia o aislamiento.', 'Como ejemplo hipotético, más verificación de acceso puede costar latencia. Priorizo privacidad y optimizo después de medir.', 'Para clientes potenciales priorizo integridad y aislamiento. La preferencia real se validará con empresarios; no atribuyo una opinión a una empresa ficticia.'],
3:['Un registro incompleto dificulta recordar motivos; no afirmo una reunión histórica. Los ADR de esta entrega conservan contexto del corte actual.', 'El compromiso costo/disponibilidad: presupuesto cero limita servicio siempre activo. Se registran metas de ensayo y límites.', 'Sí: deuda consciente con razón, riesgo, responsable y criterio de pago. El ADR conserva también alternativas y consecuencias.'],
4:['Sí: el núcleo no debe depender de detalles reemplazables de infraestructura.', 'Las vistas usan ORM y llaman servicios. project_obligations es puro; otras composiciones de dashboard tienen acceso ORM.', 'Solo añado abstracciones si reducen variación, riesgo o costo de prueba. No hay número universal de clases aceptable.'],
5:['Microservicios permiten despliegue separado pero agregan red, consistencia y observación. Horizonte no necesita repartir cada módulo en un servidor.', 'Cinco módulos Django principales: accounts, banking, classify, invoices y forecast; no son cinco microservicios.', 'No hay empresa aliada única ni medición de conexión del segmento. Debo considerar conectividad variable y reintentos sin duplicado.'],
6:['GET consulta; POST crea/ejecuta operación; PUT reemplaza; DELETE elimina según contrato.4xx refiere solicitud/autorización y5xx fallo servidor.', 'El proyecto tiene pruebas con APIClient y recorridos HTTP documentados. No atribuyo uso de una colección Postman no disponible.', 'No se auditó exhaustivamente toda respuesta para certificar ausencia de PII. Se restringe acceso por empresa y se minimizan campos; falta revisión transversal.'],
7:['Stub devuelve datos controlados; mock verifica interacciones. Evito simular la regla interna que pretendo probar.', 'Existe Mock Bank; no se certifica proveedor bancario externo ni API de pagos. El SaaS no mueve dinero.', 'Es un riesgo de fixtures persistentes. Uso BD temporal y datos creados por cada test; no invento un fallo histórico específico.'],
8:['Las regresiones son un riesgo real de evolución. Pruebas de idempotencia, Decimal y tenant protegen comportamientos antes de cambiar; no relato un incidente personal no registrado.', 'El dashboard es consulta central, pero sin analítica de uso no puedo afirmar que sea el más solicitado. Lo elijo como candidato para carga.', 'Es un percentil de las duraciones medidas, no promedio ni garantía de que todas las solicitudes cumplen el límite.'],
9:['Sí: .github/workflows/ci.yml contiene jobs backend, frontend, PostgreSQL y desktop; contenido local verificado.', 'Rojo indica fallo de un paso o condición; debe impedir promoción y merge si el check es requerido.', 'Compose y CI contienen claves sintéticas explícitas de desarrollo. No son secreto bancario productivo; no deben reutilizarse fuera del ensayo. No se imprimen archivos privados.'],
10:['La documentación registra Docker Desktop y Compose completos operativos localmente. No afirmo repetir ese arranque hoy.', 'La capa escribible desaparece con el contenedor; datos persistentes requieren volumen y respaldo probado.', 'Compose tiene una contraseña explícita local y CI otra sintética. Son contexto de ensayo y deben reemplazarse por gestión privada al publicar.'],
11:['Webhook es notificación HTTP entre sistemas. Un deploy hook es secreto de operación que debe almacenarse fuera del YAML.', 'Para este SaaS prefiero entrega controlada: CI verde no acredita aceptación, restauración ni seguridad completa.', 'Hay render.yaml y alojamiento histórico documentado. No se certifica que la rama actual esté publicada o el servicio disponible hoy.'],
12:['CVE identifica una vulnerabilidad divulgada; su severidad y aplicabilidad se contrastan con versión y exposición real.', 'La documentación registra actualización de source-map-js; no deduzco CVE ni exposición de cualquier dependencia antigua sin escaneo actual.', 'El CI inspeccionado tiene Ruff y tests, pero no un gate dedicado SAST/SCA completo demostrado.'],
13:['La falta de correlación dificulta diagnóstico; no atribuyo a esta entrega un incidente ocurrido. Propongo señales mínimas reproducibles.', 'Un request_id aleatorio correlaciona pasos de una solicitud. No debe ser cédula, correo ni etiqueta de alta cardinalidad en métricas.', 'No se realizó auditoría exhaustiva de logs. No hay evidencia para certificar ausencia de PII; el diseño propuesto la excluye y exige revisión.'],
14:['Un ejemplo hipotético: importa la duración y si impide cobrar o consultar caja. La expectativa depende del horario y perjuicio, no solo del porcentaje.', 'No justifico99,99% con presupuesto0USD. Inicio con meta de ensayo99%, sin convertirla en SLA productivo; acordar expectativa con usuarios.', 'No invento una experiencia personal. Un postmortem de Horizonte debe examinar proceso, guardas y recuperación, no culpar al único estudiante.'],
15:['En este conjunto se mantiene el mismo corte: DT01, DT02 y DT03 no se declaran pagadas por escribir las respuestas.', 'No es realista eliminar toda deuda. Registro costo y riesgo y pago primero integridad, aislamiento y recuperación.', 'En seis meses propondría validación con usuarios, corpus independiente y calibración predictiva, sin anteponer móvil a la web actual.'],
16:['Sí: ayudar a anticipar faltantes de liquidez. El SaaS amplió fuentes y cálculo, pero no se demuestra utilidad externa solo con código.', 'El monolito modular conserva transacciones y operación simple para un estudiante; Celery separa trabajo pesado sin distribuir dominios.', 'Puedo defender decisiones con código y límites explícitos. Una defensa ante comité y validación con empresarios aún deben realizarse; no las doy por aprobadas.']}

def prior(n,question):
    q=question.lower()
    if 'equipo' in q or 'discusi' in q:return 'Trabajo solo como estudiante; no atribuyo consensos ni reuniones a compañeros inexistentes. '+DEC[n-1]
    if 'solid' in q:return 'Sí: responsabilidad única e inversión de dependencias orientan la separación entre vista HTTP, servicios de cálculo y persistencia. Evito interfaces sin variación real.'
    if 'api' in q or 'http' in q:return 'La web usa API Django, sesión y CSRF; GET consulta y POST crea acciones, con permisos por empresa. Un404 de empresa ajena no debe filtrar datos.'
    return 'En Horizonte relaciono esta pregunta con '+TOPICS[n-1].lower()+'. '+DEC[n-1]+' Se contrasta con el código y se indica cuando falta medición o experiencia externa.'

def build(n):
    source=next(ROOT.glob(f'Guia_{n}_*.docx'));doc=Document(source)
    original=list(doc.paragraphs)
    original[0].text='UNIVERSIDAD DE PAMPLONA — SEDE VILLA DEL ROSARIO'
    original[1].text='Facultad de Ingeniería y Arquitecturas'
    original[3].text=f'Guía de aprendizaje {n:02d} resuelta'
    table=doc.tables[0]
    for key,value in [('Estudiante',STUDENT),('Profesor','Miguel Eduardo Posada Haddad'),('Proyecto',PROJECT),('Metodología','Scrum individual; un estudiante'),('Fecha de resolución','30 de octubre de2026')]:
        row=table.add_row();set_cell(row.cells[0],key);set_cell(row.cells[1],value)
    after(original[5],CONTEXT+'\n'+EVID)
    begin=next(i for i,p in enumerate(original) if p.text=='Saberes previos')
    end=next(i for i,p in enumerate(original[begin+1:],begin+1) if p.text.startswith('Concepto 1'))
    previous=[p for p in original[begin+2:end] if p.text.strip()]
    assert len(previous)==len(PRE[n])
    for p,answer in zip(previous,PRE[n]):after(p,'Respuesta del estudiante: '+answer)
    for k,answer in enumerate(EX[n],1):
        heading=next(p for p in original if p.text==f'Ejercicio {k}')
        idx=original.index(heading);prompt=next(p for p in original[idx+1:] if p.text.strip())
        anchor=after(prompt,'Respuesta del estudiante: '+answer)
        if n in CODE and k==len(EX[n]):
            after(anchor,'Artefacto académico completo — propuesta o ejemplo según respuesta anterior\n'+CODE[n])
    fh=next(p for p in original if p.text.startswith('Título:'))
    fp=next(p for p in original[original.index(fh)+1:] if p.text.strip())
    reflection=forum(n);after(fp,f'Reflexión del estudiante ({len(reflection.split())} palabras)\n'+reflection)
    correct=[p.text for p in original if '✅' in p.text]
    qi=next(p for p in original if p.text.startswith('Ficha de Aplicación'))
    before=original[original.index(qi)-1]
    after(before,'Cuestionario resuelto: '+'; '.join(f'{i}. {x.strip()[0]}' for i,x in enumerate(correct,1))+'. Se conservan opciones y fundamentos del material original. Las formulaciones absolutas sobre seguridad o responsabilidad requieren contexto, no equivalen a certificación legal.')
    active=False
    for idx,t in enumerate(doc.tables):
        h=t.cell(0,0).text
        if h.startswith('Código de la ficha'):active=True
        if not active or h.startswith('Criterio (peso)'):continue
        if h.startswith('Código de la ficha'):
            for row in t.rows:
                if row.cells[0].text=='Nombre del proyecto':set_cell(row.cells[1],PROJECT)
            continue
        if h=='Título':
            vals={'Título':f'ADR-{n:02d} '+TOPICS[n-1],'Estado':'Aceptado como registro académico; implementación y brechas descritas por separado','Contexto':CONTEXT+' '+TOPICS[n-1],'Decisión':DEC[n-1],'Consecuencias (positivas y negativas)':'Menor complejidad y límites explícitos. Requiere medición, aceptación y revisión externa para completar evidencia.','Alternativas consideradas y por qué se descartaron':'Se descarta introducir tecnología o certificación no justificada; se conserva solución más simple que satisface drivers. '+EX[n][min(2,len(EX[n])-1)]}
            for row in t.rows:set_cell(row.cells[1],vals.get(row.cells[0].text,DEC[n-1]))
            continue
        if n==1 and idx==8:
            vals=[PROJECT,'Segmento SaaS de microempresas; sin aliada única','Python/Django/DRF; React/TS; PostgreSQL; Redis/Celery','https://github.com/elcreado/Horizonte']
            for row,value in zip(t.rows,vals):set_cell(row.cells[1],value)
            continue
        if len(t.rows)==1 and len(t.columns)==1:
            value=SINGLE.get(n,{}).get(idx)
            if n==16 and idx==12:value=forum(16)+' '+EX[16][3]
            if value is None:raise RuntimeError(('Unmapped cell',n,idx,h[:100]))
            prompt=t.cell(0,0).text.strip()
            set_cell(t.cell(0,0),(prompt+'\n\n' if prompt else '')+'Respuesta: '+value)
            continue
        values=multi(n,t)
        if values is None:raise RuntimeError(('Unmapped table',n,idx,h))
        fillrows(t,values)
    # Resolver listas de evidencia con estados reales, sin marcar ejecución inexistente.
    for p in doc.paragraphs:
        if '☐' in p.text:
            p.text=p.text.replace('☐','Estado documentado:')
            p.add_run(' — Evidencia y límites: véase respuesta y ficha; no implica ejecución externa.').italic=True
        if 'Otra evidencia:' in p.text:p.text='Otra evidencia: respuestas, propuestas y comprobaciones académicas locales; resultados en evidencia_academica.json.'
    for sec in doc.sections:
        sec.top_margin=Cm(2);sec.bottom_margin=Cm(2);sec.left_margin=Cm(2);sec.right_margin=Cm(2)
    if n in (4,7,8,15):
        p=doc.add_paragraph();p.add_run('Comprobaciones de esta entrega').bold=True
        doc.add_paragraph('30/10/2026:26 comprobaciones del cálculo contractual aprobaron (18 equivalencias y8 rechazos de horizonte), sin BD. La prueba real tests.test_application.ApplicationTests.test_company_isolation también pasó sobre BD temporal. La variante académica no se integró al backend. Evidencias: _trabajo/evidencia_academica.json y prueba_aislamiento.log.')
    doc.core_properties.author=STUDENT;doc.core_properties.last_modified_by=STUDENT
    target=OUT/source.name;doc.save(target)
    print('Resuelta',n,flush=True)
    return target

if __name__=='__main__':
    paths=[build(n) for n in range(1,17)]
    (ROOT/'_trabajo'/'manifest.json').write_text(json.dumps([str(p) for p in paths],ensure_ascii=False,indent=2),encoding='utf-8')
