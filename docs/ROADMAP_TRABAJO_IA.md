# Roadmap de implementación: dificultad, paralelismo y bloqueos

Revisión: **5 de noviembre de 2026**. Único seguimiento operativo por tareas.
[Requisitos y evidencia](ESTADO_Y_PENDIENTES.md), [verificaciones](IMPLEMENTATION_STATUS.md),
[hitos del producto](ROADMAP_ENTREGABLES.md). Se conservan T01–T16 y P01–P10.

Estados: **Planned**, **In Progress**, **Blocked**, **Done**, **Needs Verification**.
Done exige comportamiento y evidencia delimitada; Needs Verification puede tener
implementación completa, pero conserva aceptación abierta. No se asignan porcentajes ni fechas futuras.
Prioridad P0 = bloquea demo; P1 = completa V1; P2 = alcance académico/posterior.

## Corte de ejecución — 18 de octubre de 2026

Docker completo funciona localmente. Suite PostgreSQL registrada antes de esta auditoría:
235 pruebas, 233 aprobadas y 2 omitidas del preparador SQLite; frontend y Ruff correctos.
No es evidencia de publicación, accesibilidad, correo real ni validación científica.

## Hito 1: base funcional y contratos

| ID | Prioridad | Requisitos | Estado | Trabajo y criterio de aceptación | Dependencias | Evidencia o cierre pendiente |
|---|---|---|---|---|---|---|
| T01 | P1 | Todos | Done | Fijar el punto de partida: cambios locales, funciones existentes y comandos de comprobación. | Ninguna. | Inventario y revisión en [auditoría](DOCUMENTATION_AUDIT.md). |
| T02 | P1 | RF-10, RF-13 | Done | Escribir guion de presentación y cifras esperadas con fechas relativas al corte. | Ninguna. | [Guion](PLAN_DEMO_FUNCIONAL.md); cifras en test_prepare_web_demo y test_cashflow_fixes. |
| T03 | P1 | RF-10, RF-13 | Done | Preparar textos para diferenciar saldo al corte, movimiento ocurrido y obligación futura. | Ninguna. | [Manual](USER_MANUAL.md) y reglas en banking/manual.py. |
| T04 | P1 | V1-01, RNF-07 | Done | Cerrar reglas y contrato del alta manual: campos, cuenta, fecha, signo, categoría, saldo, origen, permisos, idempotencia y errores. | T01. | Contrato [API](API_DOCUMENTATION.md); test_manual_entries. |
| T05 | P1 | RF-01, RF-02 | Needs Verification | Revisar onboarding y elección de empresa/cuenta manual; corregir solo faltas de usabilidad detectadas. | T01. | Onboarding implementado y test_company_onboarding; falta aceptación de UI final. |
| T06 | P1 | V1-01, V1-02 | Needs Verification | Construir el formulario de movimiento contra el contrato: cuenta, fecha, ingreso/egreso, importe, descripción y categoría opcional. | T04. | ManualMovement.tsx y build correcto; falta cerrar errores/red/teclado en navegador. |
| T07 | P1 | RNF-07, V1-01 | Done | Preparar casos y fixtures de QA: permisos, fechas, importes, doble envío, cuenta ajena, fallos de red y saldo inalterado. | T02 y T04. | test_manual_entries, test_cashflow_fixes y test_manual_concurrency aprobados en PostgreSQL. |
| T08 | P1 | RF-05, RF-10, RF-12 | Done | Verificar el escenario de obligaciones existente, conciliación/reversión y resultado esperado de la demo. | T01 y T02. | test_obligations, test_cashflow_fixes; escenario −81.000 COP. |
| T09 | P1 | BN-03, V1-01 | Done | Preparar persistencia e idempotencia del movimiento manual; decidir si necesita migración y separar origen de captura de origen de clasificación. | T04. | ManualEntry, migración banking.0011 y prueba concurrente PostgreSQL. |
| T10 | P1 | V1-01, RF-08, RNF-06 | Done | Implementar API/servicio de alta: validación, permisos, Decimal, normalización, clasificación, auditoría y retirada de cobertura cuando corresponda. | T09. | banking/manual.py, test_manual_entries y test_manual_concurrency. |
| T11 | P1 | V1-02, V1-03 | Needs Verification | Integrar formulario y API reales; refrescar movimientos, histórico, categorías y vistas experimentales afectadas. | T05, T06 y T10. | main.tsx integra captura/refresco; smoke local previo, falta QA transversal. |
| T12 | P1 | RF-10, RF-13 | Done | Preparar datos/caso repetible y herramienta o procedimiento seguro de preparación de la demo. | T02, T08 y T11. | prepare_web_demo y sus pruebas previas SQLite; solo DEBUG/SQLite. Docker usa preparación manual desde la web. |

## Hito 2: seguridad, aceptación y publicación

| ID | Prioridad | Requisitos | Estado | Trabajo y criterio de aceptación | Dependencias | Evidencia o cierre pendiente |
|---|---|---|---|---|---|---|
| T13 | P0 | RNF-01, RNF-07 | Needs Verification | Verificar seguridad e integridad del flujo nuevo: roles, tenant, CSRF, concurrencia/reintentos, clasificación, auditoría y cobertura. | T07 y T10. | Regresión PostgreSQL aprobada; aún falta revisión transversal de seguridad, no se cierra por un único ensayo. |
| T14 | P0 | V1-01–V1-06, RNF-10 | Needs Verification | Ejecutar QA de navegador con escenario real: ingreso/egreso manual, clasificación, obligaciones, conciliación, dashboard, red, logout y persistencia. | T08, T11, T12 y T13. | Recorridos locales previos acotados; faltan red, teclado, recuperación de errores y sesión completos. |
| T15 | P0 | Hallazgos de T14 | In Progress | Corregir problemas de uso que encuentre QA y cerrar guía corta de presentación. | T14 ejecutada y hallazgos registrados. | Esperar hallazgos registrados de T14 y volver a ejecutar los casos corregidos. |
| T16 | P1 | RNF-09, RF-16 | Planned | Publicar y comprobar la versión demostrable: integración, CI, migraciones, despliegue y prueba de humo sobre la versión publicada. | T12, T13, T14 y T15. | Después de QA y autorización del despliegue: CI, migraciones, smoke y recuperación sobre versión publicada. |

T16 requiere cerrar T12–T15 y autorización de publicación; no se contrata ni despliega nada
como parte de la limpieza documental. La concurrencia PostgreSQL ya está verificada en
su caso específico, aunque T13 conserva controles más amplios pendientes.

## Avance local de T14/T15

[Guion y resultados parciales](acceptance/WEB_V1_QA.md): registro, movimientos del mismo
día, Resumen, mensualidad con interrupción del backend, importación real con Celery y
logout/reingreso verificados. Corregido el payload mutable de reintento mensual y agregadas
cuatro regresiones frontend a CI. Textos de acceso/importación y parche source-map-js revisados.
235 pruebas backend (233 aprobadas, 2 omitidas), cuatro frontend y tres escritorio; build,
Ruff y migraciones correctos. No se cierra T14/T15: faltan escenarios de red tras commit,
roles visuales, reimportación visual, teclado completo y otros casos de la tabla.

## Hito 3: objetivos completos

| ID | Prioridad | Requisitos | Estado | Criterio de aceptación y dependencias |
|---|---|---|---|---|
| P01 | P2 | RF-01–RF-16 | Needs Verification | Completar manuales, ejemplos y aceptación documental. Para documentar el comportamiento nuevo como implementado: T11 y su evidencia. Borradores pueden empezar antes. |
| P02 | P2 | RF-01 | Blocked | Configurar y comprobar recuperación real por correo. Proveedor/remitente/buzón autorizados y secretos privados; no depende del formulario manual. No contratar nada de pago. |
| P03 | P2 | Entregable 14 | Needs Verification | Completar ejemplos/errores OpenAPI de todas las familias. Contratos reales de cada familia; para alta manual, T04 y T10. Generación central coordinada. |
| P04 | P2 | RF-02 | Planned | Administración ampliada de usuarios/empresas. Contrato de capacidades, autorización/auditoría y pruebas de abuso antes de publicar mutaciones. Independiente del alta manual, pero comparte cuentas/roles y exige coordinación. |
| P05 | P2 | RF-14 | Needs Verification | Implementado saldo diario reconstruido con ancla declarada, cobertura de todas las cuentas, huecos nulos, rangos y procedencia. Doce regresiones backend y cuatro frontend nuevas; navegador con cifras exactas. Falta aceptación más amplia y contraste independiente; no es saldo certificado por banco. [Entrega](releases/2026-10-30.md). |
| P06 | P2 | RNF-02–RNF-10 | Needs Verification | Rendimiento, concurrencia, accesibilidad y recuperación manual. Versión estable y condiciones medibles; corpus/entornos aislados para carga y restore. El ensayo completo de nueva UI espera T11. |
| P07 | P2 | RF-06–RF-09 | Needs Verification | Evaluación de clasificación y recurrencias. Corpus independiente autorizado, etiquetas temporales y separación por empresa/grupo; las pruebas sintéticas actuales no bastan. |
| P08 | P2 | RF-10, OE-4 | Needs Verification | Validar híbrido/comparación académica y resolver inclusión de Prophet. Evidencia disponible en cada corte, corpus temporal y protocolo fijado antes de comparar. No atribuir cambios posteriores al pasado. |
| P09 | P2 | RF-11, RF-12, RF-15 | Needs Verification | Calibración de cuantiles, riesgo/factores y confianza por perfil. Corpus/protocolo de P08 y validación temporal de los modelos evaluados; no deducir probabilidad de déficit de una banda sin metodología. |
| P10 | P2 | OE-6, RNF-01, tesis | Needs Verification | Revisión de seguridad integral, operación y entrega de tesis. Alcance ASVS definido, funcionalidades finales verificadas y resultados disponibles. Threat modeling puede avanzar antes; cumplimiento final y conclusiones no. |

P01: auditoría y guías actualizadas; falta que un tercero complete el recorrido.
P02: bloqueo externo por proveedor/remitente/buzón; no impide probar manualmente con una cuenta conocida.
P03: inventario de 52 rutas/68 operaciones existente; errores, ejemplos y snapshots requieren revisión.
P06: los ensayos limitados de concurrencia no prueban carga, disponibilidad o varios workers en producción.
Escritorio, móvil y proveedor bancario externo permanecen Planned y aplazados; no son tareas aprobadas
para implementar durante esta auditoría.

## Contrato vigente de captura manual

La fecha inicia en hoy (America/Bogota), permite pasado y varios movimientos por día,
incluso después del corte, nunca futuro. Saldo declarado sin cambios automáticos;
Resumen suma a caja solo operaciones posteriores al corte y usa historial para estimar.
Predicciones avanzadas requieren cobertura confirmada hasta corte común. Recibos UUID,
Decimal, tenant, rol, CSRF y auditoría se conservan. Contrato completo en [API](API_DOCUMENTATION.md).

## Cómo interpretar el orden

Codex retiene contratos, seguridad, integridad y revisión. Las tareas simples e independientes
pueden delegarse a OpenCode en worktrees aislados con plan simulado, alcance exacto y revisión
antes de integrar. No ejecutar implementaciones dependientes sin su contrato y evidencia.

## Planificación histórica

El [plan anterior completo](archive/2026-10-18/ROADMAP_TRABAJO_IA.md) conserva dificultad,
oleadas, criterios originales, reparto de archivos y decisiones. Su regla antigua que limitaba
captura al corte quedó superada por la captura diaria autorizada; no usarla como contrato actual.

## Accesos a secciones históricas

<a id="1-tareas-fáciles"></a>
[Consultar sección histórica](archive/2026-10-18/ROADMAP_TRABAJO_IA.md#1-tareas-fáciles).

<a id="2-tareas-de-dificultad-media"></a>
[Consultar sección histórica](archive/2026-10-18/ROADMAP_TRABAJO_IA.md#2-tareas-de-dificultad-media).

<a id="3-tareas-difíciles-de-la-demo"></a>
[Consultar sección histórica](archive/2026-10-18/ROADMAP_TRABAJO_IA.md#3-tareas-difíciles-de-la-demo).

<a id="4-contrato-mínimo-que-desbloquea-el-alta-manual--t04"></a>
[Consultar sección histórica](archive/2026-10-18/ROADMAP_TRABAJO_IA.md#4-contrato-mínimo-que-desbloquea-el-alta-manual--t04).

<a id="5-oleadas-de-ejecución-y-agentes-en-paralelo"></a>
[Consultar sección histórica](archive/2026-10-18/ROADMAP_TRABAJO_IA.md#5-oleadas-de-ejecución-y-agentes-en-paralelo).

<a id="6-reparto-de-archivos-para-evitar-que-los-agentes-se-pisen"></a>
[Consultar sección histórica](archive/2026-10-18/ROADMAP_TRABAJO_IA.md#6-reparto-de-archivos-para-evitar-que-los-agentes-se-pisen).

<a id="7-paquete-mínimo-para-encargar-una-tarea-a-otro-agente"></a>
[Consultar sección histórica](archive/2026-10-18/ROADMAP_TRABAJO_IA.md#7-paquete-mínimo-para-encargar-una-tarea-a-otro-agente).

<a id="8-puerta-de-salida-idea-demostrable"></a>
[Consultar sección histórica](archive/2026-10-18/ROADMAP_TRABAJO_IA.md#8-puerta-de-salida-idea-demostrable).

<a id="9-vía-posterior-objetivos-completos-de-menor-a-mayor-dificultad"></a>
[Consultar sección histórica](archive/2026-10-18/ROADMAP_TRABAJO_IA.md#9-vía-posterior-objetivos-completos-de-menor-a-mayor-dificultad).

<a id="base-que-ya-existe-y-no-hay-que-rehacer"></a>
[Consultar sección histórica](archive/2026-10-18/ROADMAP_TRABAJO_IA.md#base-que-ya-existe-y-no-hay-que-rehacer).

<a id="qué-no-puede-darse-por-hecho-ni-ejecutarse-antes"></a>
[Consultar sección histórica](archive/2026-10-18/ROADMAP_TRABAJO_IA.md#qué-no-puede-darse-por-hecho-ni-ejecutarse-antes).

<a id="qué-sí-puede-avanzar-sin-esperar-toda-la-implementación"></a>
[Consultar sección histórica](archive/2026-10-18/ROADMAP_TRABAJO_IA.md#qué-sí-puede-avanzar-sin-esperar-toda-la-implementación).

## Actualización significativa — 30 de octubre de 2026

P05 implementado de extremo a extremo sin convertir neto mensual en saldo. Contrato API,
cálculo, gráfica, tabla exacta, cobertura y documentación verificados. [Evidencia y límites](releases/2026-10-30.md).
247 pruebas PostgreSQL (245 aprobadas, 2 omitidas), 8 frontend y 3 escritorio; SQLite 240/247
con 7 exclusiones explícitas. No se cierra todo RF-14, T14 ni T16: siguen accesibilidad,
selección de empresa al recargar, escenarios de red, aceptación independiente y publicación.

## Avance T14/T15 — 4 de noviembre de 2026

Corregida la selección de empresa al recargar, con validación de membresía y separación
por usuario; reintento de carga, datos obsoletos descartados y error de logout visible
en Equipo. [Evidencia de selección](acceptance/COMPANY_SELECTION_QA.md): recarga dashboard
/Equipo y cierre/reingreso reales; fallos, vacío y respuestas fuera de orden en fixture.
Cinco regresiones nuevas (13 frontend aprobadas), build correcto y PostgreSQL 245/247
con dos exclusiones conocidas. La selección al recargar indicada en el corte anterior
queda resuelta para estos casos. T14/T15 siguen Needs Verification/In Progress: faltan
recorrido completo por teclado, roles visuales, respuestas perdidas tras commit y QA
transversal. T16 no se inicia ni se publica con esta entrega.

## Mejora de interfaz T14/T15 — 5 de noviembre de 2026

Aplicadas Web Interface Guidelines al dashboard y estilos compartidos: menú móvil con
Escape/foco, acciones directas, explicación desplegable, radios de captura y confirmación
mensual. [Evidencia y límites](acceptance/UI_GUIDELINES_QA.md): escritorio, 320/390/650 px,
validación nativa y teclado focalizado. 13 frontend, build y 245 PostgreSQL aprobadas
con dos exclusiones conocidas. T14/T15 no se cierran: restan lector de pantalla, zoom,
contraste completo, borradores, sincronización de filtros/URL y QA transversal previo.
