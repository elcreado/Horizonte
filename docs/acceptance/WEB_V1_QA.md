# Aceptación web V1 (ejecución parcial)

Revisión: 18 de octubre de 2026. Procedimiento con **ejecución parcial** para la primera
versión web con captura manual, en navegador, sobre el arranque **local con Docker Compose**.

Guion preparado por OpenCode y revisado por Codex. La tabla se actualizó con el ensayo
local de Codex del 18 de octubre; los pasos restantes conservan su estado pendiente.
No es aceptación completa ni comprobación remota.

## Alcance

- Entorno único evaluado: local, servidor de desarrollo en la máquina del revisor
  (ver arranque en `../USER_MANUAL.md` y `../PLAN_DEMO_FUNCIONAL.md`).
- Archivo de orquestación del entorno local: [`../../compose.yaml`](../../compose.yaml).
- Cifras de referencia del caso funcional: [`../PLAN_DEMO_FUNCIONAL.md`](../PLAN_DEMO_FUNCIONAL.md).

Queda **fuera** de este procedimiento y no se valida aquí:

- Despliegue remoto, alojamiento Render/Supabase ni servidor `https://horizonte-demo.onrender.com`.
- Seguridad evaluada formalmente (ASVS) o auditoría de seguridad.
- Validación científica, calibración de cuantiles P10/P50/P90 o precisión con empresas reales.
- Escritorio/instalador, móvil, banca externa real, correo real y pagos reales.

Este procedimiento es una **prueba funcional local de interfaz**; distinguirla de lo anterior
es parte del criterio de aceptación.

## Reglas del ejercicio

- Usar **usuarios, empresas, archivos y correos sintéticos**. No cargar datos financieros ni
  bancarios reales.
- El movimiento representa dinero ocurrido; **no** ejecuta pagos ni transferencias reales
  (incluida la nómina mensual).
- El **saldo declarado** y la **fecha de corte** son una observación manual: registrar un
  movimiento **no recalcula** el saldo automáticamente. El Resumen parte del saldo declarado
  y suma solo los movimientos **posteriores** al corte; los anteriores o iguales ya están incluidos.
- No borrar datos previos; ningún paso de este guion autoriza eliminar información existente. Cada caso usa empresas de prueba separadas.
- Registrar por paso: hora, resultado y evidencia (captura o texto), sin incluir contraseñas,
  claves ni archivos financieros privados.

## Preparación

1. Abrir Docker Desktop y esperar a que el motor Linux esté listo.
2. En CMD, desde la raíz del proyecto, ejecutar `docker compose up --build -d --wait`.
3. Comprobar `docker compose ps -a` (se espera `migrate` como `Exited (0)` y servicios activos).
4. Abrir la interfaz en `http://127.0.0.1:5173` y la salud del backend en
   `http://127.0.0.1:8000/api/health/`.

## Tabla de ejecución

| ID | Área | Pasos | Resultado esperado | Resultado |
|---|---|---|---|---|
| QA-WEB-01 | Inicio público | Abrir la interfaz sin sesión. | Se muestra la pantalla de Inicio sin exigir autenticación; el dashboard redirige a inicio de sesión. | Aprobado: Inicio público observado |
| QA-WEB-02 | Registro | Crear cuenta sintética y empresa con cuenta manual, saldo **500.000 COP** y corte **hoy**; iniciar sesión. | Se crea la cuenta y la membresía de propietario; se puede seleccionar la empresa creada. | Aprobado: registro web y empresa seleccionable |
| QA-WEB-03 | Navegación | Abrir cada sección de la barra lateral; usar Atrás del navegador y recargar (F5) en una sección. | Cada opción abre su vista conservando la empresa; Atrás y recargar vuelven a la misma sección sin perder la selección. | Parcial: recarga conservando segunda empresa aprobada el 4/11 en Resumen y Equipo; faltan Atrás y todas las secciones |
| QA-WEB-04 | Captura hoy | En Movimientos, con la fecha por defecto (hoy, hora de Colombia), guardar ingreso **70.000** y egreso **140.000** con descripción de prueba. | La fecha inicial es **hoy**; ambos guardados confirman y vuelven a hoy; el saldo declarado sigue en **500.000** (no cambia por el alta). | Aprobado: dos movimientos de hoy; saldo declarado 500.000 |
| QA-WEB-05 | Captura fecha pasada | Guardar un movimiento con una **fecha pasada** dentro de los últimos siete días. | El movimiento se guarda con la fecha elegida y aparece en el historial. | No ejecutado |
| QA-WEB-06 | Resumen sin doble conteo | Antes de agregar el movimiento adicional de QA-WEB-05 u obligaciones, abrir Operación → Resumen con solo el ingreso de 70.000 y el egreso de 140.000. | El Resumen recalcula la gráfica sin pedir confirmación de cobertura; parte del saldo declarado y suma **solo** movimientos posteriores al corte, sin sumar dos veces los ya incluidos. Flujo neto diario de referencia (70.000 − 140.000) / 7 = **−10.000 COP**; saldos 30/60/90 días = **200.000 / −100.000 / −400.000** (estimación orientativa, no probabilidad). | Parcial: 30 días = 200.000; falta 60/90 en este ensayo |
| QA-WEB-07 | Nómina mensual (día 1) | En Cobros y pagos → Pagos y cobros mensuales crear «Sueldos», valor, **día 1** y fecha inicial; pulsar Programar todos los meses con fecha final vacía. | Aparece un vencimiento cada mes en calendario y proyecciones; no se realiza ninguna transferencia real. | Parcial: nómina día 1 creada y vencimientos visibles; falta calendario/proyección completa |
| QA-WEB-08 | Nómina meses cortos | Programar un pago con día **29–31** y avanzar hasta un mes corto. | Febrero y los meses cortos usan su **último día**; no se genera un vencimiento en fecha inexistente. | No ejecutado |
| QA-WEB-09 | Importación CSV | En Fuentes de datos, descargar el ejemplo y subirlo a la cuenta manual. Esperar el resultado. | El proceso queda **en cola** y pasa a **completado** con dos movimientos nuevos; el estado se observa sin ejecutar un tercer proceso manual (Celery incluido). | Aprobado: Celery completó importación #12 con 2 nuevos y 0 duplicados |
| QA-WEB-10 | Importación duplicada | Subir **dos veces** el mismo archivo. | La segunda carga omite los duplicados; no se crean movimientos repetidos. | No ejecutado |
| QA-WEB-11 | Interrupción de red y reintento exacto | Guardar un movimiento, interrumpir la conexión antes de confirmar y pulsar **Reintentar guardado**. | Se reenvía con los **mismos datos**; no se recarga la página antes de confirmar; no se crea un movimiento duplicado. | No ejecutado |
| QA-WEB-12 | Contrato de reintento mensual | Con el guardado mensual en estado incierto, intentar editar campos y cancelar; luego pulsar **Reintentar guardado**. | El payload original y su UUID se conservan; campos y acciones de cancelar quedan deshabilitados; **Reintentar guardado** reenvía la solicitud **idéntica**; un **4xx de validación** vuelve a habilitar la edición; no se usa `localStorage` para conservar la clave. | Parcial: backend detenido antes del POST, edición bloqueada y reintento correcto; respuesta perdida tras commit cubierta parcialmente por pruebas automatizadas |
| QA-WEB-13 | Lector y otra empresa | Añadir un usuario existente con rol **Consulta** en la empresa y una segunda cuenta **sin membresía** en la primera empresa. | El lector solo consulta (sin acciones de escritura); los datos financieros de la primera empresa **no** aparecen en la cuenta ajena. | No ejecutado |
| QA-WEB-14 | Teclado y foco | Recorrer formulario y diálogos solo con teclado (Tab, Shift+Tab, Esc). | Existe foco visible; se puede saltar a cada control; los diálogos se cierran con Esc sin activar acciones destructivas. | Parcial: salto al contenido activado con Enter; falta recorrido completo |
| QA-WEB-15 | Cierre y reingreso | Cerrar sesión y volver a entrar con la cuenta sintética. | Inicio sigue visible sin sesión; el dashboard exige autenticación; tras entrar persisten empresa, movimientos y programación mensual. | Aprobado en este caso: empresa seleccionada, Resumen con historial importado y nómina pendiente tras reingreso |

## Evidencia y cierre

- Para cada fila completar la columna **Resultado** con `No ejecutado`, `Parcial`, `Aprobado`, `Fallido` o
  `Bloqueado`, más hora y evidencia.
- Si un paso falla, anotar ID, mensaje, hora y si ocurre en la interfaz o en el backend/worker;
  revisar `docker compose logs backend worker frontend` para la importación pendiente.
- Distinguir siempre en las notas lo observado en **local** de lo que requeriría despliegue
  remoto, evaluación ASVS o validación científica; no extrapolar resultados locales a esos ámbitos.
- No incluir secretos ni datos reales en la evidencia.

## Hallazgos corregidos (T15)

- La programación mensual guardaba solo el UUID y dejaba editar tras un fallo. Ahora conserva
  los valores originales e impide cambiarlos o detener otra regla mientras el envío está
  incierto. El reintento usa la misma solicitud; respuesta válida libera el formulario,
  4xx permite corregir y 5xx conserva el intento. No se usa almacenamiento del navegador.
- El acceso ya no propone el usuario demo ni menciona una variable de entorno como contraseña.
- El estado de importación deja de recomendar runserver como arranque local; remite al entorno Docker.
- Auditoría npm detectó source-map-js 1.2.1; lockfile actualizado únicamente a 1.2.2.
  La instalación Docker posterior informó cero vulnerabilidades conocidas en ese momento.

Limitaciones: navegar fuera de mensualidades o recargar pierde el recibo en memoria;
consultar las programaciones antes de repetir un envío incierto. No se reclama persistencia
entre sesiones del intento ni tolerancia a todas las pérdidas de red.

## Verificación automatizada final del bloque

- Docker/PostgreSQL: 235 pruebas, 233 aprobadas y 2 omitidas del preparador SQLite.
- `docker compose exec frontend npm test`: cuatro regresiones de solicitud mensual
  inmutable, respuesta perdida, error 503, validación 400 y altas intencionales independientes.
- Build TypeScript/Vite correcto (649 módulos); Ruff y formato: 208 archivos correctos;
  migraciones sin cambios; tres pruebas Node de escritorio aprobadas.
- `npm audit --audit-level=high` dentro del frontend Docker: cero vulnerabilidades
  conocidas reportadas en esta ejecución. No certifica seguridad integral del producto.
- CI ahora ejecuta también `npm test` del frontend; no se ha ejecutado CI remoto en este bloque.

La interrupción del navegador ocurrió durante la obtención de CSRF, antes del POST;
no demuestra una pérdida de respuesta después de que el servidor confirme un commit.
La conservación de valores/UUID y los reintentos con 5xx sí tienen regresión automatizada.

## Seguimiento de selección — 4 de noviembre de 2026

[Guía y evidencia específica](COMPANY_SELECTION_QA.md). Resumen y Equipo conservan la
segunda empresa tras recarga. Logout fallido mantiene selección y muestra error;
logout correcto limpia preferencia y al reingresar selecciona primera empresa autorizada.
La persistencia de datos del caso QA-WEB-15 se mantiene; no implica recordar la selección
tras logout. No se modificaron movimientos, saldos, membresías ni empresas en este corte.
