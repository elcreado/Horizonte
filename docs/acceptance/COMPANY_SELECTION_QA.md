# Selección de empresa y recuperación de carga

Verificación local: **4 de noviembre de 2026**, rama `codex/v1-manual-transactions`.
Alcance T14/T15; no cierra toda la aceptación web. Docker es el entorno principal.

## Contrato

Dashboard y Empresa y equipo comparten la selección. Se conserva en este navegador
solo el usuario autenticado y el ID de empresa. Al recargar se consulta la lista del
servidor antes de restaurarla; si ya no pertenece a esa lista, se elige la primera
empresa disponible. No hay autorización basada en localStorage. Una lista vacía
no se confunde con una consulta fallida. Logout correcto elimina la preferencia;
un fallo mantiene la sesión y la selección con un error visible. No se promete
sincronización en vivo entre pestañas, cuentas o dispositivos.

## Preparación

Iniciar Docker según el [manual](../USER_MANUAL.md). Utilizar una cuenta sintética
con dos empresas. No borrar información ni cambiar accesos reales para probar.
La prueba aislada no consulta backend ni representa una autenticación real:
[fixture](../../frontend/tests/companySelection.html) y
[controles](../../frontend/tests/companySelectionHarness.tsx), accesibles con Vite en
`http://localhost:5173/tests/companySelection.html`. Usa un origen diferente del
recorrido real en `127.0.0.1`, para separar sus preferencias del navegador.
Las solicitudes se completan o fallan desde botones y deliberadamente ignoran AbortSignal.
No está importada por la aplicación ni incluida en su build de producción.

## Casos y evidencia

| Caso | Acción y resultado esperado | Resultado |
|---|---|---|
| SEL-01 | Elegir segunda empresa y recargar Resumen: se conserva la selección tras consultar membresías. | Aprobado en web real con las dos empresas QA existentes. |
| SEL-02 | Entrar en Empresa y equipo y recargar: misma selección y título del equipo. | Aprobado en web real. |
| SEL-03 | Cambiar entre secciones: comparten empresa; no se muestra el resumen anterior durante la carga del nuevo. | Cambio de empresa Resumen y navegación Equipo aprobados; todas las secciones y respuestas dashboard retardadas pendientes. |
| SEL-04 | ID eliminado/ajeno o preferencia de otro usuario: primera empresa autorizada; nunca restaurar acceso ausente. | Regresión Node aprobada; cambio de usuario observado en fixture; revocación real pendiente. |
| SEL-05 | JSON corrupto, tipo inválido o almacenamiento bloqueado: selección en memoria funciona. | Regresión Node aprobada; bloqueo desde ajustes reales del navegador pendiente. |
| SEL-06 | Carga inicial fallida: estado error; reintentar carga una lista válida, sin confundirla con una lista vacía. | Hook aprobado en fixture: fallo de solicitud 1, éxito de solicitud 2; indisponibilidad específica de /companies/ en la web integrada pendiente. |
| SEL-07 | Respuesta vacía válida: estado listo, ninguna empresa ni error. | Hook aprobado en fixture, solicitud 5. |
| SEL-08 | Mientras carga usuario A, cambiar a B; completar B, elegir empresa B y después responder lista vacía de A. | Aprobado en fixture: solicitud 4 y después 3; se conserva 702 para fixture-b. |
| SEL-09 | Crear empresa: agregarla a la lista y seleccionarla. | Hook aprobado con creación simulada 703; alta real seguida de recarga pendiente en este corte. |
| SEL-10 | Detener backend local, intentar logout: error visible y empresa conservada; restaurar backend. | Aprobado en Equipo con segunda empresa; fallo al obtener CSRF antes del POST. No demuestra pérdida de respuesta tras logout confirmado. |
| SEL-11 | Logout correcto y reingreso: no restaurar la preferencia de la sesión terminada; seleccionar primera disponible. | Aprobado en web real: volvió a la primera empresa QA. Datos previos intactos. |
| SEL-12 | Intentar seleccionar un ID fuera de la lista cargada. | Aprobado en fixture: ID 999 no reemplaza 702; backend sigue siendo autoridad de acceso. |

## Comprobaciones automáticas

13 pruebas frontend aprobadas: cinco nuevas de selección, cuatro de saldos y cuatro
de reintentos mensuales. Build TypeScript/Vite correcto. Suite PostgreSQL repetida:
247 pruebas, 245 aprobadas y dos omitidas del preparador SQLite.
Las pruebas puras de preferencias no sustituyen las verificaciones del hook ni las
pruebas de autorización del backend. No se ejecutó CI remoto ni despliegue.

## Delegación

Plan JSON y simulación de OpenCode revisados, guía aislada sin lectura de archivos
privados. Primeros intentos fallaron por permisos/conectividad; el intento con acceso
a red agotó 180 segundos sin crear archivos. No se integró salida delegada. Codex
redactó y revisó este documento directamente.
