# Horizonte: resumen de estado y pendientes

Revisión documental: **18 de octubre de 2026**. Código base `d795c6b`. Alcance base: objetivos,
RF-01 a RF-16, RNF-01 a RNF-10 y entregables de [README](../README.md) y
[SPECS](../SPECS.md). No se modifican ni se dan por cumplidas las metas originales.

## Resumen ejecutivo

**Prioridad posterior acordada:** centrarse en una aplicación web útil y presentable,
dejando escritorio y Android/iOS pendientes. El [plan de demostración](PLAN_DEMO_FUNCIONAL.md)
documenta el alta manual ya implementada y la estimación inicial basada en todo el historial hasta el corte común, confirmado completo y con mínimo siete días. La evidencia vigente está en [IMPLEMENTATION_STATUS](IMPLEMENTATION_STATUS.md).
La matriz inferior conserva el alcance completo, pero no fija por sí sola el orden de esta etapa.

La **V1 web local funciona mediante Docker Compose completo**: PostgreSQL, Redis,
migraciones, backend, worker Celery y frontend. Hay captura manual, sidebar, Resumen
inmediato y pagos mensuales. El escritorio y alojamiento tienen evidencia histórica
separada; no se certifica su disponibilidad ni se priorizan sobre la web.

Esto no equivale al cumplimiento completo del proyecto académico. Las brechas principales
son recuperación real por correo, aceptación del instalador en Windows limpio, validación
predictiva y probabilística, administración ampliada, contrato API completo y comprobaciones
de rendimiento, accesibilidad, disponibilidad y seguridad. Parte del trabajo falta implementarlo;
otra parte existe pero aún necesita evidencia de aceptación.

Se respeta la decisión de **presupuesto inicial 0 USD y respaldo manual únicamente**.
No se propone reactivar respaldos diarios, ni hacer llamadas para impedir la suspensión.
Android/iOS continúa como V2; no bloquea la entrega de escritorio inicial.

## Qué evidencia respalda este informe

- Código inspeccionado: `backend/apps`, `backend/config`, `frontend/src`, `desktop`,
  `compose.yaml`, scripts y `.github/workflows/ci.yml`.
- Última ejecución local registrada antes de esta auditoría: 235 pruebas PostgreSQL,
  233 aprobadas y 2 omitidas (preparador SQLite), Ruff/formato sobre 208 archivos,
  migraciones sin cambios, build frontend y tres pruebas Node aprobados.
  La auditoría documental registra aparte sus comprobaciones en [informe](DOCUMENTATION_AUDIT.md).
- Existe configuración CI con SQLite, PostgreSQL 16, frontend y pruebas Node del escritorio;
  esta última no instala Electron ni ejecuta la interfaz.
- Evidencia histórica del 5 de octubre: servicio Render operativo, recorridos HTTP con
  sesión/CSV/XML/Mock Bank, arranque empaquetado, respaldo/restauración aislada y mediciones
  HTTP limitadas. Se conserva en documentación de operación y aceptación.
- **No se ha recertificado el servicio remoto ni el instalador completo en esta auditoría.** Las pruebas locales no prueban su disponibilidad actual.
- La carpeta no versionada `Proyecto/` contiene documentos/plantillas/modelos del usuario:
  permanece intacta y sus DOCX/ZIP no se han auditado como entregables académicos terminados.

Estados usados: **implementado** = hay código y pruebas del comportamiento;
**parcial** = falta parte del requisito o su validación; **pendiente** = falta el entregable
o no se encontró evidencia suficiente. No se calcula un porcentaje artificial de avance.

## Objetivos planteados

| Objetivo | Estado y brecha que falta cerrar |
|---|---|
| General: integrar finanzas y anticipar déficit mediante un híbrido | Parcial. Producto utilizable con datos sintéticos e híbrido experimental; falta demostrar eficacia con datos independientes y resultados predictivos validados. |
| OE-1: arquitectura modular, segura y extensible | Implementada como base Django/React, conectores y cola. Falta validación integral de seguridad y operación ante fallos. |
| OE-2: ETL asíncrono, normalización, deduplicación y clasificación | Implementado para CSV/XLSX/XML/Mock. Falta corpus representativo, medición de precisión/cobertura y validación de casos adversos. |
| OE-3: modelo híbrido de obligaciones y series temporales | Implementación experimental disponible. Falta validación temporal independiente y reconstrucción fiable de la información disponible en cada corte histórico. |
| OE-4: comparar Naive, ARIMA, Prophet e híbrido | Hay baselines, rolling-origin y evaluación ARIMA sobre datos sintéticos. No se encontró implementación/evaluación Prophet: evaluarlo o justificar formalmente su exclusión; no declararlo comparado. |
| OE-5: P10/P50/P90 y alertas explicables | Parcial. Cuantiles experimentales y alertas por obligaciones/umbral; faltan calibración por perfil, riesgo probabilístico y validación de comprensión del usuario. |
| OE-6: ASVS, OAuth/PKCE y cifrado | Sesión + CSRF y controles de aislamiento implementados; threat model disponible. Falta matriz ASVS y pruebas; OAuth/PKCE y ciclo de secretos de un proveedor externo siguen sin integrarse. No sustituir sesión de aplicación por OAuth sin necesidad. |

## Requisitos funcionales

| ID | Estado comprobado y pendiente concreto | Evidencia |
|---|---|---|
| RF-01 | Parcial. Registro/login/logout/perfil y reset de un solo uso implementados; falta proveedor/remitente y recepción real del correo alojado.  [Código](../backend/apps/accounts/recovery.py) · [Pruebas](../backend/tests/test_recovery.py) |
| RF-02 | Parcial. Empresas y roles propietario/contador/lector implementados. Administrador de plataforma tiene consulta restringida de usuarios; falta gestión ampliada y auditable de usuarios/empresas si se conserva ese actor original. No asumir que ser administrador permite leer finanzas ajenas.  [Código](../backend/apps/accounts/team.py) · [Pruebas](../backend/tests/test_team.py) |
| RF-03 | Implementado en Mock Bank: consentimiento, saldos, sincronización/revocación. No hay integración externa bancaria real; no se exige banca de producción para el sandbox inicial. Si se promete sandbox de proveedor, falta contratar/conectar ese entorno.  [Código](../backend/apps/banking/connections.py) · [Pruebas](../backend/tests/test_bank_connections.py) |
| RF-04 | Implementado CSV/XLSX, cola, idempotencia y límites de archivo. Falta aceptación visual con archivos representativos y fallos de conexión/worker.  [Código](../backend/apps/banking/tasks.py) · [Pruebas](../backend/tests/test_imports.py) |
| RF-05 | Implementado XML UBL, emitida/recibida, revisión de pendiente y vínculo único con obligación. Falta corpus documental más amplio. No valida firma ni certificación DIAN; API de proveedor no es obligatoria si XML satisface el alcance elegido.  [Código](../backend/apps/invoices/views.py) · [Pruebas](../backend/tests/test_invoices.py) |
| RF-06 | Parcial. Normalización y comercios/alias disponibles; falta medir resolución de comercios bancarios representativos. No hay evidencia de resolver genéricamente todos los ejemplos del requisito.  [Código](../backend/apps/banking/normalization.py) · [Pruebas](../backend/tests/test_normalization.py) |
| RF-07 | Reglas y sugerencias TF-IDF con abstención implementadas. Falta demostrar cobertura y exactitud de clasificación en corpus etiquetado independiente.  [Código](../backend/apps/classify/services.py) · [Pruebas](../backend/tests/test_classification.py) |
| RF-08 | Correcciones, reglas recordadas por empresa y auditoría implementadas. Falta evaluación longitudinal del aprendizaje, sin mezclar empresas ni incorporar etiquetas futuras.  [Código](../backend/apps/classify/views.py) · [Pruebas](../backend/tests/test_rules.py) |
| RF-09 | Detección semanal/mensual, revisión y materialización/vínculos implementados. Falta validar precisión/recall, cambios de patrón y falsos positivos en corpus independiente.  [Código](../backend/apps/forecast/recurrences.py) · [Pruebas](../backend/tests/test_recurrences.py) |
| RF-10 | Escenario determinístico y métodos Naive/estacional/SES/híbrido disponibles a 30/60/90 días. Falta validar eficacia del híbrido y coherencia en distintos perfiles. El Resumen combina historial ocurrido y compromisos; el escenario sin historial conserva solo obligaciones. Ninguno acredita un P50 calibrado.  [Código](../backend/apps/forecast/live_baseline.py) · [Pruebas](../backend/tests/test_live_baseline.py) |
| RF-11 | Parcial. P10/P50/P90 experimentales y candidato offline de intervalos. Falta calibración y evaluación por perfil/horizonte. Una banda no acredita probabilidad de déficit.  [Código](../backend/apps/forecast/empirical_quantiles.py) · [Pruebas](../backend/tests/test_empirical_quantiles.py) |
| RF-12 | Parcial. Umbral, fecha de déficit, días bajo umbral, saldo mínimo y pagos hasta el déficit explicados. Falta nivel de riesgo `low/medium/high` con metodología explícita y evaluación de sus factores; la explicación actual no es riesgo probabilístico validado.  [Código](../backend/apps/forecast/alerts.py) · [Pruebas](../backend/tests/test_threshold.py) |
| RF-13 | Dashboard de saldos COP, cobros/pagos y escenario de liquidez implementado. Falta aceptar visualmente el recorrido y completar la interpretación del riesgo según RF-12.  [Código](../backend/apps/forecast/views.py) · [Pruebas](../backend/tests/test_cashflow_fixes.py) |
| RF-14 | Parcial. Gráficos de proyección, banda experimental, ingresos/egresos, categorías y calendario; tablas CxC/CxP/recurrencias/alertas disponibles. Actualización 30/10: serie diaria reconstruida desde saldo declarado y cobertura completa por cuenta implementada y probada; días desconocidos se dejan nulos. No certifica extractos bancarios. El histórico mensual sigue mostrando flujos por separado. Revisar si se exigen gráficos específicos además de tablas para todas las vistas enumeradas.  [Código](../backend/apps/forecast/history.py) · [Pruebas](../backend/tests/test_history.py) |
| RF-15 | Parcial. Cuatro etapas de amplitud observada y avisos de datos insuficientes. Falta demostrar confianza predictiva; dos extremos temporales no prueban historial completo ni exactitud.  [Código](../backend/apps/forecast/coverage.py) · [Pruebas](../backend/tests/test_coverage.py) |
| RF-16 | Implementado procesamiento asíncrono de importaciones y Mock Bank. Facturas por carga XML, no sincronización periódica con proveedor. Falta ensayo de concurrencia y recuperación real durante cargas en el alojamiento.  [Código](../backend/apps/banking/tasks.py) · [Pruebas](../backend/tests/test_background.py) |

## Requisitos de la V1 solicitados durante el desarrollo

IDs adicionales porque las peticiones posteriores no tenían identificadores; no sustituyen RF/RNF.
Fuente: instrucciones del usuario de esta conversación, consolidadas en el [manual](USER_MANUAL.md).

| ID | Criterio de aceptación | Estado delimitado | Código/prueba | Tarea |
|---|---|---|---|---|
| V1-01 | Capturar manualmente ingresos/egresos del mismo día, hoy por defecto, pasado editable, futuro rechazado, reintento sin duplicado | Done en API; aceptación UI abierta | [manual.py](../backend/apps/banking/manual.py), [test_manual_entries](../backend/tests/test_manual_entries.py) | T04, T09, T10, T14 |
| V1-02 | Dashboard por secciones mediante sidebar y navegación diferenciada | Needs Verification: implementado/build, falta aceptación transversal | [main.tsx](../frontend/src/main.tsx) | T06, T11, T14 |
| V1-03 | Todo movimiento adicional afecta Resumen sin duplicar saldo; historial hasta corte alimenta la predicción avanzada | Done en cálculo/API; QA visual abierto | [test_cashflow_fixes](../backend/tests/test_cashflow_fixes.py), [test_live_baseline](../backend/tests/test_live_baseline.py) | T08, T11, T14 |
| V1-04 | Programar manualmente pagos/cobros todos los meses, incluido día 1 y fin de mes | Done en servicio; QA visual abierto | [monthly.py](../backend/apps/forecast/monthly.py), [test_cashflow_fixes](../backend/tests/test_cashflow_fixes.py) | T08, T14 |
| V1-05 | Procesar ejemplo CSV y reimportarlo sin duplicados; worker disponible | Done en prueba de cola BD y entorno Docker; recorrido visual Celery pendiente | [test_cashflow_fixes](../backend/tests/test_cashflow_fixes.py) | T07, T14 |
| V1-06 | Arrancar frontend/backend/worker/BD localmente con Docker y conservar datos; comandos en manual | Done en este equipo; reproducibilidad independiente abierta | [Compose](../compose.yaml), [TESTING](TESTING.md) | T01, T14, RNF-09 |

Los criterios originales de RF/RNF/BN se conservan en [README](../README.md).
La columna de evidencia no convierte casos limitados en cumplimiento completo.

## Requisitos no funcionales

| ID | Estado comprobado y pendiente concreto |
|---|---|
| RNF-01: secretos | No se incluyen credenciales de BD en Electron; HTTPS, sesión HttpOnly/CSRF y variables de servidor. Falta auditoría de secretos/logs/retención; el ciclo de tokens bancarios cifrados de proveedor real no está implementado. No confundir archivos locales privados con cifrado. |
| RNF-02: disponibilidad ≥99 % | No acreditada. Definir ventana de ensayo, monitorización y registro de caídas. Render Free admite suspensión; no prometer disponibilidad permanente con la evidencia existente. |
| RNF-03: dashboard <2 s | No acreditado de extremo a extremo. Hay muestras HTTP secuenciales calientes de aproximadamente 0,4–0,6 s; faltan dataset, concurrencia, p95 representativo, arranque frío y renderizado de interfaz. |
| RNF-04: no bloquear web | Arquitectura asíncrona implementada. Falta medir navegación/consultas mientras se importan archivos o sincroniza en el servicio real. |
| RNF-05: escalabilidad de workers | Cola con leases, reintentos y pruebas PostgreSQL de concurrencia. Falta ensayo operativo de varios workers y recuperación; despliegue gratuito actual no demuestra escalado horizontal en producción. |
| RNF-06: trazabilidad | Jobs y auditorías instrumentados. Falta revisar exhaustivamente usuario/fuente/fechas/errores en cada operación y definir retención sin datos sensibles en logs. |
| RNF-07: aislamiento | Amplia matriz de sesiones/roles y objetos ajenos; no es garantía absoluta. Ampliar cobertura de objetos/roles, casos de concurrencia y auditoría de seguridad. |
| RNF-08: recuperación | Respaldo manual y restauración aislada ya ensayados. Falta cifrado, retención, copia externa y ensayo de fallos. Respaldo diario excluido expresamente: no es una tarea pendiente. |
| RNF-09: portabilidad | Implementado y probado localmente: Compose completo con migraciones, frontend/backend, Celery, PostgreSQL y Redis; volumen conservado. Falta repetición desde checkout limpio en otro equipo para cerrar reproducibilidad independiente. |
| RNF-10: accesibilidad/responsive | CSS responsive, tablas y foco/atajo de contenido implementados. Faltan teclado/Narrador, zoom, contraste y tamaños móviles con evidencia visual; compilar no prueba accesibilidad. |

## Reglas de negocio y entregables

- BN-01 a BN-05 y BN-07/08 tienen implementación para el sandbox: no transferencias,
  consentimiento, deduplicación, factura distinta de cobro, correcciones, horizontes y cola.
  Mantener pruebas de regresión y completar aceptación visual. BN-06 sigue parcial por RF-15.
- Entregables 2–6 y 13: frontend, backend, BD, ETL, motor y pruebas presentes; el motor
  conserva límites experimentales. Presencia de código no demuestra cierre de todos los RF.
- Entregable 7: reporte sintético de 100 empresas ×24 meses y generador presentes;
  los archivos generados son locales y debe prepararse su distribución/reproducción final.
- Entregable 8: reportes de experimentos presentes; falta corpus independiente, comparación
  completa acordada y conclusiones sin extrapolar resultados sintéticos a empresas reales.
- Entregables 9–11: threat model, manual de usuario y manual técnico presentes; actualizar
  junto a cada cambio y validar que un tercero puede seguirlos.
- Entregable 12: Compose completo implementado y probado localmente; falta repetir en otro equipo desde checkout limpio. No implica despliegue remoto del corte.
- Entregable 14: OpenAPI todavía parcial en errores, ejemplos y algunos snapshots históricos.
  Tener todas las rutas inventariadas no lo convierte en un contrato completo para clientes.
- Entregable 1: documento final de tesis, bibliografía y demostración académica no acreditados
  por este análisis de código. Revisar por separado los archivos académicos del usuario y
  modelos/diagramas frente al esquema vigente. No se movieron ni se borraron esos originales.

## Criterios de éxito del MVP

- **10.000 transacciones sin degradación relevante:** hay límite y ensayo previo de importación;
  falta definir degradación admisible y medir mientras se usa la interfaz con carga representativa.
- **Clasificar automáticamente al menos el 80 %:** no acreditado en corpus independiente.
  Medir cobertura automática y exactitud por separado; no convertir abstenciones en aciertos.
- **Idempotencia, corrección manual, XML, forecast 30/60/90 y procesamiento asíncrono:**
  implementados y probados en escenarios delimitados; falta aceptación integral del instalador.
- **Detectar déficit y explicar alertas:** implementado para historial y obligaciones conocidas;
  no demuestra anticipación estadística ni explicación del riesgo probabilístico completo.
- **Aislamiento y auditoría:** controles/pruebas presentes; completar auditoría transversal,
  no prometer garantía absoluta por una suite verde.
- El plan académico de 24 semanas y los porcentajes sujetos al piloto son planificación,
  no evidencia de ejecución. Estado del arte, referencias regulatorias y bibliografía deben
  revisarse con fuentes primarias al cerrar la tesis; no se han revalidado en este informe.

## Próximos pasos, en orden

El seguimiento único con prioridad, dependencias y criterios está en
[ROADMAP_TRABAJO_IA](ROADMAP_TRABAJO_IA.md): primero QA de la web (T13–T15), después
publicación autorizada (T16). P01–P10 conservan documentación, correo, API, administración,
saldo histórico, calidad, investigación y seguridad. Escritorio/móvil quedan aplazados.

## Qué requiere acciones externas del usuario

- **Prueba web local:** Docker Desktop con motor Linux; `docker compose up --build -d --wait`. No requiere Python/Node en el host ni claves bancarias. Para el cliente alojado, consultar la referencia de escritorio histórica.
- **Correo real:** cuenta de proveedor, credenciales guardadas de forma privada, remitente
  permitido y buzón de prueba. Si exige dominio propio o pago, no activarlo sin autorización.
- **Windows limpio:** equipo o VM aislada para aceptación; no equivale al equipo de desarrollo.
- **Investigación/usabilidad:** datos autorizados o corpus sintético independiente y participantes;
  decidir formalmente cambios en objetivos académicos, no eliminarlos por conveniencia.
- **Banca externa y móvil V2:** accesos del proveedor y herramientas/dispositivos de compilación;
  verificar requisitos y costes al ejecutar esa fase. No son requisitos de uso de la V1.

## Documentación ordenada en esta revisión

- Guías vigentes y resumen en la raíz de `docs/`, con [índice](README.md).
- `desktop/`, `acceptance/`, `operations/`, `security/`: referencia por tarea.
- `research/`: métodos y resultados experimentales; se conservan, no son basura documental.
- `archive/2026-10-05/`: cortes originales de estado, pruebas, manual técnico, despliegue,
  roadmap y revisión que mezclaban etapas. Llevan aviso de archivo y no son instrucciones vigentes.
- Se actualizan enlaces/rutas y las salidas predeterminadas de comandos de investigación
  para que los reportes nuevos se guarden en `docs/research/`.
