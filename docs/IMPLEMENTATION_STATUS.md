# Estado de implementación

## Interfaz más intuitiva — 5 de noviembre de 2026

Sidebar con iconos y menú móvil, acciones frecuentes, Resumen simplificado con método
desplegable, captura con radios/ayudas y confirmación para detener mensualidades.
[Cambios, pruebas visuales y revisión pendiente](acceptance/UI_GUIDELINES_QA.md). Docker:
13 pruebas frontend, build de 655 módulos y PostgreSQL 245 aprobadas + 2 omitidas de 247.
T14/T15 siguen abiertos; no se declara certificación de accesibilidad ni publicación.

## Selección de empresa — 4 de noviembre de 2026

Preferencia local validada contra membresías actuales, carga/error/vacío separados y
reintento de empresas. Respuestas canceladas no sustituyen la sesión nueva; el Resumen
se vincula a usuario, empresa, horizonte y revisión. Logout fallido visible en Equipo;
logout correcto limpia la preferencia. [Casos y límites](acceptance/COMPANY_SELECTION_QA.md).
Docker: PostgreSQL 245 aprobadas + 2 omitidas de 247; frontend 13 aprobadas y build correcto.
Fixture de hook verifica recuperación, respuesta obsoleta y lista vacía; la aceptación
integrada de todos los fallos de red, roles y teclado sigue pendiente en T14/T15.


## Actualización funcional — 30 de octubre de 2026

[Saldo histórico diario](releases/2026-10-30.md) implementado en Historial y categorías:
ancla declarada, cobertura común, huecos nulos, tabla exacta y procedencia por cuenta.
Doce pruebas backend nuevas y cuatro frontend. Verificación local: PostgreSQL 245 aprobadas
+ 2 omitidas de 247; SQLite 240 + 7 de 247; frontend 8 y escritorio 3 aprobadas, build correcto,
Ruff/formato 210 archivos y sin migraciones nuevas. Escenario visual y reconfirmación aprobados.
P05 conserva Needs Verification para aceptación más amplia; no se declara cierre de RF-14.
Los cortes anteriores se conservan a continuación y no se confunden con resultados actuales.


Revisión documental: **18 de octubre de 2026**, código base `d795c6b`, rama
`codex/v1-manual-transactions`. Esta revisión no publica ni certifica el alojamiento.
Requisitos y brechas: [matriz](ESTADO_Y_PENDIENTES.md). Trabajo pendiente:
[roadmap único por tareas](ROADMAP_TRABAJO_IA.md).

## Implementado en esta rama

| Comportamiento | Código y pruebas de respaldo |
|---|---|
| Captura manual: ingreso/egreso, varios movimientos por día, hoy en Colombia por defecto, pasado permitido, futuro rechazado | [Servicio](../backend/apps/banking/manual.py), [regresión](../backend/tests/test_manual_entries.py), [formulario](../frontend/src/ManualMovement.tsx) |
| Recibo UUID por empresa, reintento 200/201, conflicto 409, roles/CSRF/auditoría | [ManualEntry](../backend/apps/banking/models.py), [concurrencia PostgreSQL](../backend/tests/test_manual_concurrency.py) |
| Sidebar por Operación, Análisis y Configuración; refresco de vistas | [Interfaz](../frontend/src/main.tsx). Hay evidencia local acotada; falta aceptación transversal de navegación/red/teclado |
| Resumen afectado por movimientos y obligaciones | [Cálculo](../backend/apps/forecast/views.py), [pruebas](../backend/tests/test_cashflow_fixes.py). Solo movimientos posteriores al corte se suman al saldo declarado; el historial anterior alimenta el promedio sin duplicar caja |
| Predicción inicial 30/60/90 con historial completo confirmado hasta corte común y mínimo siete días; otros modelos con requisitos propios | [Motor](../backend/apps/forecast/live_baseline.py), [pruebas](../backend/tests/test_live_baseline.py). Promedio orientativo; cuantiles experimentales sin calibración demostrada |
| Programaciones mensuales con día 1–31, fin de mes, cancelación e idempotencia | [Servicio](../backend/apps/forecast/monthly.py), [pruebas](../backend/tests/test_cashflow_fixes.py). Generan obligaciones, no transferencias |
| CSV/XLSX/XML/Mock Bank y cola | [Importación](../backend/apps/banking/tasks.py), [pruebas CSV](../backend/tests/test_imports.py), [XLSX](../backend/tests/test_xlsx.py), [XML](../backend/tests/test_invoices.py), [cola](../backend/tests/test_background.py) |
| Entorno Docker completo y persistente | [Compose](../compose.yaml), [procedimiento](TESTING.md). PostgreSQL, Redis, migraciones, backend, Celery y frontend; SQLite anterior separada |
| Demo sintética sin borrar datos | [Comando](../backend/apps/accounts/management/commands/prepare_web_demo.py), [pruebas](../backend/tests/test_prepare_web_demo.py). Exclusivo de SQLite en DEBUG; no funciona en el PostgreSQL de Docker |

## Verificación Docker local — 18 de octubre de 2026

Ejecución registrada antes de esta auditoría: **235 pruebas, 233 aprobadas y 2 omitidas**
(preparación exclusiva de SQLite). Incluye concurrencia PostgreSQL para un UUID enviado
por propietario y contador. Ruff y formato: 208 archivos; migraciones sin cambios;
frontend compilado; tres pruebas Node de escritorio aprobadas. Compose arrancó,
API directa y a través de Vite respondieron, y Celery respondió a `inspect ping`.
La auditoría documental registra sus propias comprobaciones en [informe](DOCUMENTATION_AUDIT.md).

El ejemplo CSV se verificó con carga multipart y worker de BD. El ping de Celery
verifica disponibilidad del worker, no equivale a un recorrido visual completo de importación.
El procedimiento reproducible está en [TESTING](TESTING.md).

## Límites pendientes

No se acredita precisión con empresas reales, cuantiles calibrados, ASVS, disponibilidad,
rendimiento representativo ni accesibilidad completa. Correo real y aceptación del
instalador siguen pendientes; escritorio y móvil están aplazados. La rama no está
desplegada: las pruebas locales no certifican el servidor remoto. Respaldo manual únicamente.

## Verificación histórica — 16 de octubre

Las cifras SQLite, recorridos, correcciones y preparación de demo de los cortes anteriores
se conservan íntegros en el [estado anterior](archive/2026-10-18/IMPLEMENTATION_STATUS.md)
y las [pruebas anteriores](archive/2026-10-18/TESTING.md). No mezclar esos resultados
con una ejecución actual ni sumar sus conteos.

## Correcciones: Resumen, mensualidades e importaciones

La descripción vigente está consolidada en la tabla superior. La cronología permanece
en el archivo; las migraciones `banking.0011_manualentry` y `forecast.0007_monthlyschedule_monthlyoccurrence_and_more`
se aplicaron también al PostgreSQL local de Docker. No se migró la BD remota.

## Avance y verificación — 18 de octubre de 2026

Consultar la verificación Docker superior y el roadmap. Los ensayos de red, aceptación
integral y publicación siguen abiertos; una prueba concurrente aprobada no cierra toda
la revisión de seguridad de T13.

## Continuación T14/T15 — QA web local

Corregido el reintento de pagos mensuales: conserva UUID y datos originales ante envío
incierto, bloquea edición/cancelación y libera solo con respuesta definitiva. Cuatro
regresiones frontend aprobadas; CI incorpora `npm test`. También se corrigieron textos
de acceso/importación y source-map-js 1.2.1 → 1.2.2, sin otras actualizaciones de dependencias.

Navegador: registro, dos movimientos el mismo día, Resumen 200.000 COP a 30 días antes
de importar, interrupción/restablecimiento del backend con reintento mensual, CSV completado
por Celery y logout/reingreso. Suite PostgreSQL repetida: 233 aprobadas y 2 omitidas;
frontend build, Ruff, migraciones y tres pruebas de escritorio correctos. Auditoría npm
frontend sin vulnerabilidades conocidas reportadas. [Casos y límites](acceptance/WEB_V1_QA.md).
T14/T15 continúan abiertos por casos restantes; no se publica ni se acredita ASVS.
