# Estado de implementación vigente

Revisión: **15 de octubre de 2026**. La versión de escritorio funcional para pruebas está
entregada; el alcance académico completo sigue parcial. Matriz de objetivos/RF/RNF y plan:
[ESTADO_Y_PENDIENTES.md](ESTADO_Y_PENDIENTES.md).

## Evidencia local de esta revisión

- Frontend: TypeScript + Vite aprobados.
- Escritorio: tres pruebas Node de configuración aprobadas; no sustituyen instalar Electron.
- Backend: 215 pruebas ejecutadas, 210 aprobadas y 5 omitidas con SQLite. Primera ejecución
  restringida falló por permisos al limpiar temporales; repetición autorizada fuera del
  sandbox aprobada. No se modificó el código para ocultar esos fallos.
- Migraciones: `makemigrations --check --dry-run` no detecta cambios.
- Servicio remoto y recorrido visual: no revalidados en esta revisión documental.

## Base implementada

- Inicio público, sesión/CSRF, empresas y roles; consulta administrativa restringida.
- CSV/XLSX/XML y Mock Bank asíncronos; clasificación, correcciones y recurrencias.
- Obligaciones/conciliación reversible, dashboard 30/60/90, calendario e historiales.
- Pronóstico y cuantiles experimentales separados del escenario contractual.
- Cliente Windows Electron/NSIS, backend alojado y BD persistente; consumo sin Docker local.

## Pendientes principales

- Correo de recuperación real y aceptación completa en Windows limpio.
- Administración ampliada y saldo histórico real/gráficos pendientes del alcance original.
- Validación de clasificación/recurrencias, híbrido, cuantiles y confianza predictiva.
- OpenAPI completo, accesibilidad y ensayos representativos de rendimiento/operación/seguridad.
- Consolidación de tesis y experimentos; móvil en V2. Respaldo diario excluido.

El detalle de cortes antiguos se conservó en
[estado histórico](archive/2026-10-05/IMPLEMENTATION_STATUS.md); no es esta matriz vigente.
