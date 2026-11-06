> Archivo histórico previo a la auditoría documental del 18 de octubre de 2026.
> No usar como estado ni arranque vigente. Ver [índice actual](../../README.md).

# Estado de implementación

## Verificación Docker local — 18 de octubre de 2026

Flujo principal: `docker compose up --build -d --wait`. PostgreSQL, Redis, backend,
worker Celery y frontend activos; migraciones finalizadas con código 0. API directa
y vía Vite responden; Celery responde a `inspect ping`. Se conserva `postgres_data`.

Suite PostgreSQL ejecutada: **235 pruebas, 233 aprobadas y 2 omitidas** (preparación
de demo exclusiva de SQLite). Incluye concurrencia de solicitudes con el mismo UUID.
Ruff check y formato: 208 archivos; migraciones sin cambios; frontend compilado.
La primera pasada detectó fixtures/configuración ausentes en el contenedor y dos
supuestos de entorno en pruebas; se corrigieron y se repitió la suite completa.
No se ha desplegado este corte ni se certifica aceptación visual completa.


Revisión de documentación: **18 de octubre de 2026**. Entrega web en `codex/v1-manual-transactions`. La verificación histórica conserva las cifras del 16 de octubre; los cortes de ejecución anteriores se conservan abajo y la verificación Docker vigente encabeza este documento.

## Implementado en esta rama

Actualización de navegación: dashboard dividido por barra lateral en Operación, Análisis y Configuración; cada sección carga solo sus herramientas. Captura manual inicia en hoy (Colombia), permite fechas pasadas y varios movimientos del mismo día, incluso con corte anterior.

- Alta manual de transacciones con cuenta propia manual, ingreso/egreso, fecha, importe y categoría opcional.
- Recibo inmutable `ManualEntry`, UUID único por empresa, restricción de BD y bloqueo transaccional. El mismo envío devuelve el ID original; contenido distinto con la misma clave devuelve 409. La categoría puede corregirse sin romper el reintento.
- Validaciones Decimal, fecha hasta hoy (hoy por defecto); el corte limita solo el pronóstico experimental avanzado, no la captura ni el resumen; roles propietario/contador, sesión/CSRF y auditoría de autor/fecha. Captura manual diferenciada de clasificación manual.
- Saldo declarado sin modificación y sin contarse dos veces: solo las operaciones posteriores al saldo actualizan la caja disponible, mientras el historial anterior alimenta la estimación sin duplicar caja; retirada de cobertura cuando cambia el historial confirmado.
- Refresco de vistas financieras. Claves React distintas por sección para evitar duplicados al actualizar.
- Resumen: promedio neto diario de movimientos registrados y compromisos conocidos, disponible de inmediato, sin exigir confirmaciones ni esperar el corte. El pronóstico experimental avanzado (30/60/90 días, gráfica y ejecuciones guardadas) sí exige historial confirmado a través del corte común y un mínimo de siete días completos. Conserva los modelos experimentales previos y el escenario contractual.
- Programaciones mensuales persistentes, con migración `forecast.0007_monthlyschedule_monthlyoccurrence_and_more`, y worker de cola local automático con `runserver` frente a workers separados en producción.
- Contratos OpenAPI actualizados y migración `banking.0011_manualentry`.

## Verificación histórica — 16 de octubre

- Evidencia histórica del 16 de octubre de 2026, no una ejecución nueva: suite backend con 231 pruebas, 226 aprobadas y cinco omitidas por requerir PostgreSQL. La repetición fuera del sandbox pasó; la ejecución restringida falló al limpiar temporales. Inventario API regenerado antes de la repetición.
- Ruff lint y formato aprobados; sin migraciones pendientes de generar.
- TypeScript y build Vite aprobados.
- La migración se aplicó a SQLite local. Ninguna BD remota se migró.
- Pruebas de API nuevas: ingreso/egreso, categorías, saldo, auditoría, persistencia, reintentos, importes/fechas inválidos, roles, cuenta ajena, CSRF, cobertura y pronósticos guardados 30/60/90.
- QA de navegador y sus resultados: [pruebas](../../TESTING.md).

## Límites pendientes

No se acredita concurrencia nueva en PostgreSQL, precisión predictiva con empresas reales, cuantiles calibrados, disponibilidad o accesibilidad completa. Correo real, aceptación de instalador, banca externa y móvil siguen pendientes. Esta rama no está desplegada; las verificaciones locales no certifican el servidor remoto. Se mantiene respaldo manual únicamente.

La matriz académica detallada permanece en [estado y pendientes](../../ESTADO_Y_PENDIENTES.md); los cortes previos permanecen en `archive/`.


## Correcciones: Resumen, mensualidades e importaciones

- Resumen incorpora promedio neto diario de movimientos registrados y compromisos. La caja disponible suma solo operaciones posteriores al saldo declarado; el historial anterior influye en la estimación sin duplicar caja. Se advierte de datos incompletos y supuestos de días vacíos. Evaluaciones de alertas conservan la misma trayectoria del resumen (`summary_v2`).
- Pagos/cobros mensuales manuales con fecha inicial/final opcional, día 1–31, importe y concepto. Cada vencimiento se materializa una sola vez y puede conciliarse con un movimiento. Cancelación conserva histórico y obligaciones con conciliaciones. El sistema amplía la ventana futura al consultar las vistas; la programación sin fecha final permanece activa.
- Migración `forecast.0007_monthlyschedule_monthlyoccurrence_and_more` aplicada solo a SQLite local.
- `manage.py runserver` selecciona cola de BD local salvo configuración explícita e inicia un worker hijo en DEBUG; se detiene junto al servidor. En producción se mantienen workers separados. Ya no hace falta una tercera consola para importar con el arranque local estándar.
- Archivo de ejemplo validado mediante carga multipart y worker real de BD; reimportarlo omite duplicados. Pruebas y límites en TESTING.md.


## Avance y verificación — 18 de octubre de 2026

- Dos tareas documentales ejecutadas por OpenCode en worktrees aislados, después de simulación y autorización del envío limitado. Codex inspeccionó reportes, archivos, diffs y corrigió una imprecisión financiera antes de integrar. La carpeta original `.agents/` se conservó por SHA-256.
- T12: comando `prepare_web_demo --username TU_USUARIO --dry-run` y ejecución sin esa opción. Crea dos empresas sintéticas nuevas en SQLite local; no borra datos ni modifica contraseñas. Pruebas de simulación sin escrituras, repetición con lotes nuevos, cifras financieras y rollback de toda la preparación ante fallos.
- T13: prueba PostgreSQL de un mismo UUID enviado simultáneamente por propietario y contador; espera una sola transacción, un recibo y una auditoría, con respuestas 201/200. Incluida en la suite CI existente; posteriormente ejecutada y aprobada en Docker/PostgreSQL, según la verificación superior.
- Suite completa del 18 de octubre: 235 pruebas, 229 aprobadas y seis omitidas por requerir PostgreSQL (cinco anteriores y la nueva de concurrencia). Ruff, formato, comprobación de migraciones y build TypeScript/Vite aprobados. Sin nuevas migraciones.
- Preparación real local precedida por dry-run; navegador verificó el caso de obligaciones −81.000 COP y el pronóstico manual a 30/60/90 con corte relativo al día del ensayo. Evidencia detallada en [TESTING](../../TESTING.md).
- T14–T16 siguen parciales/pendientes: no se declara QA transversal, concurrencia PostgreSQL ni despliegue remoto completos. Ver [roadmap actualizado](../../ROADMAP_TRABAJO_IA.md).
