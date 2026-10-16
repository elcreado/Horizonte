# Estado de implementación

Revisión: **16 de octubre de 2026**. Entrega web en `codex/v1-manual-transactions`.

## Implementado en esta rama

Actualización de navegación: dashboard dividido por barra lateral en Operación, Análisis y Configuración; cada sección carga solo sus herramientas. Captura manual inicia en hoy (Colombia), permite fechas pasadas y varios movimientos del mismo día, incluso con corte anterior.

- Alta manual de transacciones con cuenta propia manual, ingreso/egreso, fecha, importe y categoría opcional.
- Recibo inmutable `ManualEntry`, UUID único por empresa, restricción de BD y bloqueo transaccional. El mismo envío devuelve el ID original; contenido distinto con la misma clave devuelve 409. La categoría puede corregirse sin romper el reintento.
- Validaciones Decimal, fecha hasta hoy (hoy por defecto); el corte limita la predicción, no la captura, roles propietario/contador, sesión/CSRF y auditoría de autor/fecha. Captura manual diferenciada de clasificación manual.
- Saldo declarado sin modificación; retirada de cobertura cuando cambia historial confirmado.
- Refresco de vistas financieras. Claves React distintas por sección para evitar duplicados al actualizar.
- Estimación inicial de promedio neto diario de todo el historial registrado hasta el corte, con mínimo siete días completos, 30/60/90 días, gráfica y ejecuciones guardadas. Conserva los modelos experimentales previos y el escenario contractual.
- Contratos OpenAPI actualizados y migración `banking.0011_manualentry`.

## Verificación local

- Suite backend: 231 pruebas, 226 aprobadas y cinco omitidas por requerir PostgreSQL. La repetición fuera del sandbox pasó; la ejecución restringida falló al limpiar temporales. Inventario API regenerado antes de la repetición.
- Ruff lint y formato aprobados; sin migraciones pendientes de generar.
- TypeScript y build Vite aprobados.
- La migración se aplicó a SQLite local. Ninguna BD remota se migró.
- Pruebas de API nuevas: ingreso/egreso, categorías, saldo, auditoría, persistencia, reintentos, importes/fechas inválidos, roles, cuenta ajena, CSRF, cobertura y pronósticos guardados 30/60/90.
- QA de navegador y sus resultados: [pruebas](TESTING.md).

## Límites pendientes

No se acredita concurrencia nueva en PostgreSQL, precisión predictiva con empresas reales, cuantiles calibrados, disponibilidad o accesibilidad completa. Correo real, aceptación de instalador, banca externa y móvil siguen pendientes. Esta rama no está desplegada; las verificaciones locales no certifican el servidor remoto. Se mantiene respaldo manual únicamente.

La matriz académica detallada permanece en [estado y pendientes](ESTADO_Y_PENDIENTES.md); los cortes previos permanecen en `archive/`.


## Correcciones: Resumen, mensualidades e importaciones

- Resumen incorpora promedio neto diario de movimientos registrados y compromisos. La caja disponible suma solo operaciones posteriores al saldo declarado; el historial anterior influye en la estimación sin duplicar caja. Se advierte de datos incompletos y supuestos de días vacíos. Evaluaciones de alertas conservan la misma trayectoria del resumen (`summary_v2`).
- Pagos/cobros mensuales manuales con fecha inicial/final opcional, día 1–31, importe y concepto. Cada vencimiento se materializa una sola vez y puede conciliarse con un movimiento. Cancelación conserva histórico y obligaciones con conciliaciones. El sistema amplía la ventana futura al consultar las vistas; la programación sin fecha final permanece activa.
- Migración `forecast.0007_monthlyschedule_monthlyoccurrence_and_more` aplicada solo a SQLite local.
- `manage.py runserver` selecciona cola de BD local salvo configuración explícita e inicia un worker hijo en DEBUG; se detiene junto al servidor. En producción se mantienen workers separados. Ya no hace falta una tercera consola para importar con el arranque local estándar.
- Archivo de ejemplo validado mediante carga multipart y worker real de BD; reimportarlo omite duplicados. Pruebas y límites en TESTING.md.
