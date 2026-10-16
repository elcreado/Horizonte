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

- Suite backend: 224 pruebas, 219 aprobadas y cinco omitidas por requerir PostgreSQL. La repetición fuera del sandbox pasó; la ejecución restringida falló al limpiar temporales. Inventario API regenerado antes de la repetición.
- Ruff lint y formato aprobados; sin migraciones pendientes de generar.
- TypeScript y build Vite aprobados.
- La migración se aplicó a SQLite local. Ninguna BD remota se migró.
- Pruebas de API nuevas: ingreso/egreso, categorías, saldo, auditoría, persistencia, reintentos, importes/fechas inválidos, roles, cuenta ajena, CSRF, cobertura y pronósticos guardados 30/60/90.
- QA de navegador y sus resultados: [pruebas](TESTING.md).

## Límites pendientes

No se acredita concurrencia nueva en PostgreSQL, precisión predictiva con empresas reales, cuantiles calibrados, disponibilidad o accesibilidad completa. Correo real, aceptación de instalador, banca externa y móvil siguen pendientes. Esta rama no está desplegada; las verificaciones locales no certifican el servidor remoto. Se mantiene respaldo manual únicamente.

La matriz académica detallada permanece en [estado y pendientes](ESTADO_Y_PENDIENTES.md); los cortes previos permanecen en `archive/`.
