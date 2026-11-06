# Auditoría documental del repositorio

Fecha: **18 de octubre de 2026**. Base de código `d795c6b`, rama
`codex/v1-manual-transactions`. Habilidad utilizada:
[project-docs-curator](../.agents/skills/project-docs-curator/SKILLS.md)
(el archivo local se llama `SKILLS.md`, no `SKILL.md`). No se cambiaron sus instrucciones.

## Alcance y fuentes

Inventario inicial: **50 Markdown propios del repositorio**, incluidos AGENTS, habilidades
locales y dos contratos académicos de `Proyecto/.documentacion`; excluye dependencias,
`.git`, entornos virtuales y artefactos externos de agentes. Se leyeron contenidos,
encabezados, enlaces y referencias de implementación. No se auditó contenido DOCX/ZIP,
ni se certificaron disponibilidad remota, legislación, bibliografía o resultados científicos.
README/SPECS conservan el alcance original; la conversación añade V1-01–V1-06, sin
renumerar RF-01–RF-16, RNF-01–RNF-10, BN ni T01–T16/P01–P10.

Fuentes únicas tras la revisión:

- [Matriz de requisitos](ESTADO_Y_PENDIENTES.md): criterios, brechas y enlaces a código/pruebas.
- [Estado](IMPLEMENTATION_STATUS.md): capacidades y verificaciones con alcance explícito.
- [Pruebas](TESTING.md): comandos; [manual](USER_MANUAL.md): recorrido del usuario.
- [Roadmap operativo](ROADMAP_TRABAJO_IA.md): prioridad, estado, dependencias y cierre.
- [Hitos](ROADMAP_ENTREGABLES.md): resumen de etapas, sin duplicar listas de tareas.

## Clasificación de cada Markdown inicial

KEEP = conservar; UPDATE = corregir; MERGE = consolidar sin perder historia;
ARCHIVE = histórico; REVIEW = mantener intacto hasta revisión de su propietario.
La clasificación describe esta intervención, no aprobación funcional o académica.

| Archivo | Categoría | Evidencia / acción aplicada y destino |
|---|---|---|
| [CODESTYLE.md](../CODESTYLE.md) | KEEP | Referencia complementaria o convención útil, sin duplicado que justifique eliminarla. |
| [Proyecto/.documentacion/artifact-brief.md](../Proyecto/.documentacion/artifact-brief.md) | REVIEW | Contrato de plantilla/DOCX del usuario; titularidad y entregable académico fuera de esta auditoría. Se conserva intacto. |
| [Proyecto/.documentacion/artifact.md](../Proyecto/.documentacion/artifact.md) | REVIEW | Contrato de plantilla/DOCX del usuario; titularidad y entregable académico fuera de esta auditoría. Se conserva intacto. |
| [README.md](../README.md) | UPDATE | Corregidos alcance, referencias o contradicciones; conserva su ruta y propósito. |
| [SPECS.md](../SPECS.md) | UPDATE | Corregidos alcance, referencias o contradicciones; conserva su ruta y propósito. |
| [docs/API_DOCUMENTATION.md](API_DOCUMENTATION.md) | UPDATE | Corregidos alcance, referencias o contradicciones; conserva su ruta y propósito. |
| [docs/ESTADO_Y_PENDIENTES.md](ESTADO_Y_PENDIENTES.md) | MERGE | Consolidado en su ruta original; versión anterior preservada en docs/archive/2026-10-18/ESTADO_Y_PENDIENTES.md. |
| [docs/IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) | MERGE | Consolidado en su ruta original; versión anterior preservada en docs/archive/2026-10-18/IMPLEMENTATION_STATUS.md. |
| [docs/PLAN_DEMO_FUNCIONAL.md](PLAN_DEMO_FUNCIONAL.md) | KEEP | Referencia complementaria o convención útil, sin duplicado que justifique eliminarla. |
| [docs/README.md](README.md) | UPDATE | Corregidos alcance, referencias o contradicciones; conserva su ruta y propósito. |
| [docs/ROADMAP_ENTREGABLES.md](ROADMAP_ENTREGABLES.md) | MERGE | Consolidado en su ruta original; versión anterior preservada en docs/archive/2026-10-18/ROADMAP_ENTREGABLES.md. |
| [docs/ROADMAP_TRABAJO_IA.md](ROADMAP_TRABAJO_IA.md) | MERGE | Consolidado en su ruta original; versión anterior preservada en docs/archive/2026-10-18/ROADMAP_TRABAJO_IA.md. |
| [docs/TECHNICAL_MANUAL.md](TECHNICAL_MANUAL.md) | UPDATE | Corregidos alcance, referencias o contradicciones; conserva su ruta y propósito. |
| [docs/TESTING.md](TESTING.md) | MERGE | Consolidado en su ruta original; versión anterior preservada en docs/archive/2026-10-18/TESTING.md. |
| [docs/USER_MANUAL.md](USER_MANUAL.md) | UPDATE | Corregidos alcance, referencias o contradicciones; conserva su ruta y propósito. |
| [docs/acceptance/DESKTOP_ACCEPTANCE.md](acceptance/DESKTOP_ACCEPTANCE.md) | UPDATE | Corregidos alcance, referencias o contradicciones; conserva su ruta y propósito. |
| [docs/acceptance/QA_CONNECTIVITY.md](acceptance/QA_CONNECTIVITY.md) | UPDATE | Corregidos alcance, referencias o contradicciones; conserva su ruta y propósito. |
| [docs/acceptance/V1_ACCEPTANCE.md](acceptance/V1_ACCEPTANCE.md) | UPDATE | Corregidos alcance, referencias o contradicciones; conserva su ruta y propósito. |
| [docs/archive/2026-10-05/HOSTING_FREE.md](archive/2026-10-05/HOSTING_FREE.md) | ARCHIVE | Corte histórico conservado; índice actualizado si corresponde. No es evidencia vigente. |
| [docs/archive/2026-10-05/IMPLEMENTATION_HISTORY.md](archive/2026-10-05/IMPLEMENTATION_HISTORY.md) | ARCHIVE | Corte histórico conservado; índice actualizado si corresponde. No es evidencia vigente. |
| [docs/archive/2026-10-05/IMPLEMENTATION_STATUS.md](archive/2026-10-05/IMPLEMENTATION_STATUS.md) | ARCHIVE | Corte histórico conservado; índice actualizado si corresponde. No es evidencia vigente. |
| [docs/archive/2026-10-05/REVISION.md](archive/2026-10-05/REVISION.md) | ARCHIVE | Corte histórico conservado; índice actualizado si corresponde. No es evidencia vigente. |
| [docs/archive/2026-10-05/ROADMAP_ENTREGABLES.md](archive/2026-10-05/ROADMAP_ENTREGABLES.md) | ARCHIVE | Corte histórico conservado; índice actualizado si corresponde. No es evidencia vigente. |
| [docs/archive/2026-10-05/TECHNICAL_MANUAL.md](archive/2026-10-05/TECHNICAL_MANUAL.md) | ARCHIVE | Corte histórico conservado; índice actualizado si corresponde. No es evidencia vigente. |
| [docs/archive/2026-10-05/TESTING.md](archive/2026-10-05/TESTING.md) | ARCHIVE | Corte histórico conservado; índice actualizado si corresponde. No es evidencia vigente. |
| [docs/archive/README.md](archive/README.md) | UPDATE | Corte histórico conservado; índice actualizado si corresponde. No es evidencia vigente. |
| [docs/desktop/DESKTOP.md](desktop/DESKTOP.md) | UPDATE | Corregidos alcance, referencias o contradicciones; conserva su ruta y propósito. |
| [docs/desktop/DESKTOP_RELEASE.md](desktop/DESKTOP_RELEASE.md) | UPDATE | Corregidos alcance, referencias o contradicciones; conserva su ruta y propósito. |
| [docs/desktop/DESKTOP_V1_FUNCTIONAL.md](desktop/DESKTOP_V1_FUNCTIONAL.md) | UPDATE | Corregidos alcance, referencias o contradicciones; conserva su ruta y propósito. |
| [docs/operations/BACKGROUND_WORKER.md](operations/BACKGROUND_WORKER.md) | UPDATE | Corregidos alcance, referencias o contradicciones; conserva su ruta y propósito. |
| [docs/operations/HOSTED_BACKUP.md](operations/HOSTED_BACKUP.md) | KEEP | Procedimiento especializado; mantiene límites y evidencia histórica propios del alojamiento. |
| [docs/operations/HOSTING_FREE.md](operations/HOSTING_FREE.md) | KEEP | Procedimiento especializado; mantiene límites y evidencia histórica propios del alojamiento. |
| [docs/operations/PLATFORM_ADMIN.md](operations/PLATFORM_ADMIN.md) | UPDATE | Corregidos alcance, referencias o contradicciones; conserva su ruta y propósito. |
| [docs/operations/QUEUE_DIAGNOSTICS.md](operations/QUEUE_DIAGNOSTICS.md) | KEEP | Procedimiento especializado; mantiene límites y evidencia histórica propios del alojamiento. |
| [docs/research/ARIMA_PILOT.md](research/ARIMA_PILOT.md) | KEEP | Método o resultado sintético específico. Parámetros/corpus difieren; no es duplicado por compartir título. Reportes generados intactos. |
| [docs/research/ARIMA_RESULTS.md](research/ARIMA_RESULTS.md) | KEEP | Método o resultado sintético específico. Parámetros/corpus difieren; no es duplicado por compartir título. Reportes generados intactos. |
| [docs/research/CLASSIFICATION_MODEL.md](research/CLASSIFICATION_MODEL.md) | KEEP | Método o resultado sintético específico. Parámetros/corpus difieren; no es duplicado por compartir título. Reportes generados intactos. |
| [docs/research/FORECAST_BASELINES.md](research/FORECAST_BASELINES.md) | UPDATE | Corregidos alcance, referencias o contradicciones; conserva su ruta y propósito. |
| [docs/research/IMPORT_BENCHMARK.md](research/IMPORT_BENCHMARK.md) | KEEP | Método o resultado sintético específico. Parámetros/corpus difieren; no es duplicado por compartir título. Reportes generados intactos. |
| [docs/research/INTERVAL_CALIBRATION.md](research/INTERVAL_CALIBRATION.md) | KEEP | Método o resultado sintético específico. Parámetros/corpus difieren; no es duplicado por compartir título. Reportes generados intactos. |
| [docs/research/INTERVAL_RESULTS.md](research/INTERVAL_RESULTS.md) | KEEP | Método o resultado sintético específico. Parámetros/corpus difieren; no es duplicado por compartir título. Reportes generados intactos. |
| [docs/research/PROBABILITY_EVALUATION.md](research/PROBABILITY_EVALUATION.md) | KEEP | Método o resultado sintético específico. Parámetros/corpus difieren; no es duplicado por compartir título. Reportes generados intactos. |
| [docs/research/PROBABILITY_RESULTS.md](research/PROBABILITY_RESULTS.md) | KEEP | Método o resultado sintético específico. Parámetros/corpus difieren; no es duplicado por compartir título. Reportes generados intactos. |
| [docs/research/README.md](research/README.md) | KEEP | Método o resultado sintético específico. Parámetros/corpus difieren; no es duplicado por compartir título. Reportes generados intactos. |
| [docs/research/RESEARCH_RESULTS.md](research/RESEARCH_RESULTS.md) | KEEP | Método o resultado sintético específico. Parámetros/corpus difieren; no es duplicado por compartir título. Reportes generados intactos. |
| [docs/security/THREAT_MODEL.md](security/THREAT_MODEL.md) | UPDATE | Corregidos alcance, referencias o contradicciones; conserva su ruta y propósito. |
| [AGENTS.md](../AGENTS.md) | KEEP | Instrucciones/habilidad local; lectura para ejecutar la auditoría, sin modificaciones. |
| [.agents/skills/codex-opencode-orchestrator/README.md](../.agents/skills/codex-opencode-orchestrator/README.md) | KEEP | Instrucciones/habilidad local; lectura para ejecutar la auditoría, sin modificaciones. |
| [.agents/skills/codex-opencode-orchestrator/SKILL.md](../.agents/skills/codex-opencode-orchestrator/SKILL.md) | KEEP | Instrucciones/habilidad local; lectura para ejecutar la auditoría, sin modificaciones. |
| [.agents/skills/project-docs-curator/SKILLS.md](../.agents/skills/project-docs-curator/SKILLS.md) | KEEP | Instrucciones/habilidad local; lectura para ejecutar la auditoría, sin modificaciones. |

## Archivos creados y material archivado

Se creó este informe y seis snapshots en `docs/archive/2026-10-18/`:
[índice previo](archive/2026-10-18/README.md),
[estado](archive/2026-10-18/IMPLEMENTATION_STATUS.md),
[matriz](archive/2026-10-18/ESTADO_Y_PENDIENTES.md),
[pruebas](archive/2026-10-18/TESTING.md),
[roadmap operativo](archive/2026-10-18/ROADMAP_TRABAJO_IA.md) y
[hitos](archive/2026-10-18/ROADMAP_ENTREGABLES.md).
Categoría ARCHIVE para los seis. Se conservaron las versiones completas y sus cifras;
solo se añadieron avisos, navegación y ajuste de enlaces relativos. Las rutas vigentes
permanecen para preservar enlaces; no se borró permanentemente ningún documento.
El archivo previo de octubre y los originales académicos permanecen intactos.

## Duplicados y contradicciones resueltos

- Estado y TESTING repetían cronología con distintos conteos: evidencia consolidada,
  cronología en archivo y resultados fechados. Docker local tiene 235/233/2; no confundir
  con 231/226/5 o 235/229/6 de SQLite en cortes anteriores.
- Roadmap de entregables marcaba captura/persistencia como pendientes y el de IA conservaba
  contrato anterior que prohibía movimientos posteriores al corte. Se preservó el original
  y se documentó el contrato autorizado: hasta hoy, incluso después del corte.
- RNF-09 y entregable 12 describían Compose parcial: hoy contiene frontend, backend,
  migraciones, worker, Redis y PostgreSQL. Reproducibilidad en otro equipo sigue pendiente.
- API mezclaba 48/61 y 50/64: el JSON actual tiene **52 rutas y 68 operaciones**.
  Su prueba contrasta inventario con las rutas reales; no acredita errores/ejemplos completos.
- FORECAST_BASELINES contradecía su propio resultado ARIMA y decía que Resumen era solo
  obligaciones. Se corrigió sin cambiar reportes generados ni métricas.
- Escritorio/alojamiento se distinguen de la prioridad web local. Un aviso histórico no
  elimina sus tareas de aceptación. El preparador automático sigue limitado a SQLite.
- Se corrigió la jerarquía del encabezado de comercios y se mantuvieron anclas antiguas
  del roadmap mediante enlaces al archivo. Las referencias a comandos en código inline
  y URLs externas no se presentan como enlaces remotos verificados.

## Reconciliación y roadmap

T01–T16 y P01–P10 conservan su identidad, propósito y dependencias; las reglas antiguas
quedan archivadas. Done se limita a evidencia concreta. T05/T06/T11/T13/T14 mantienen
Needs Verification por aceptación UI o seguridad integral; T15/T16 permanecen Planned.
P02 sigue Blocked por proveedor/remitente/buzón. La prueba concurrente PostgreSQL sí pasó,
pero no cierra ASVS ni seguridad completa. V1-01–V1-06 trazan solicitudes posteriores a
manual, cálculo, navegación, mensualidades, importación y Docker.

## Verificación de esta auditoría

- Suite PostgreSQL completa ejecutada nuevamente: **235 pruebas, 233 aprobadas, 2 omitidas**
  por preparador exclusivo de SQLite. Sin fallos; base `test_liquidity` aislada.
- Frontend TypeScript/Vite compilado; tres pruebas Node de escritorio aprobadas.
- Ruff check y formato correctos en 208 archivos; migraciones sin cambios.
- Validación de los **57 Markdown finales**: **361 enlaces locales comprobados, sin destinos ni anclas rotos**. Se conservaron 16 RF, 10 RNF, 6 V1, 16 T y 10 P. Las 31 referencias web no se verificaron remotamente. Registro en artefactos locales de auditoría.
- QMD se consultó mediante CLI porque no hay MCP QMD expuesto. Índice y embeddings actualizados localmente; la colección existente cubre `docs/`, mientras raíz, habilidades y contratos se inventariaron directamente.
- OpenCode consolidó únicamente TESTING, después de plan JSON y simulación, con lectura
  limitada a TESTING/IMPLEMENTATION_STATUS previamente autorizados. Codex revisó reporte,
  stdout/stderr, alcance y contenido antes de aplicar y ajustar el resultado.
- Verificadas las seis copias históricas frente a Git: cuerpos completos preservados, con solo avisos y ajuste de enlaces.
- El cambio previo de `.gitignore` se conserva intacto. No se modifica código, modelos,
  migraciones, dependencias, JSON generado, datos ni configuración de infraestructura.
  No se realiza commit ni push durante esta auditoría.

## Asuntos pendientes de revisión

1. **Aceptación web:** red, teclado, accesibilidad, persistencia/sesión y flujo integral con
   Celery; distinguirlo del ensayo de importación con worker BD y del ping de Celery.
2. **Reproducibilidad Docker:** repetir desde checkout limpio en otro equipo. Decidir si
   adaptar el preparador SQLite a PostgreSQL aporta valor; no se ha aprobado ni implementado aquí.
3. **Objetivos originales:** correo real, administración ampliada, saldo histórico real,
   OpenAPI completo, rendimiento representativo, disponibilidad, ASVS y política de recuperación manual.
4. **Investigación:** corpus independiente, evidencia temporal sin fuga, calibración,
   confianza/riesgo, decisión formal sobre Prophet y validación con usuarios. Los informes
   sintéticos existentes y sus títulos similares no se fusionan ni se reescriben.
5. **Propietario académico:** revisar contratos de plantilla y DOCX de Proyecto, referencias
   regulatorias/bibliografía y cambios de alcance formales. No se certifica su corrección legal.
6. **Publicación y clientes:** autorizar y verificar el corte remoto tras QA; escritorio,
   firma/actualización y Android/iOS mantienen su prioridad aplazada.
7. **Habilidad local:** el nombre `SKILLS.md` permite lectura manual pero podría impedir
   descubrimiento automático que espere `SKILL.md`; se informa sin renombrar instrucciones del usuario.
