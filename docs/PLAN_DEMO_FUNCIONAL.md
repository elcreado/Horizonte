# Primera versión web con captura manual

Revisión: **18 de octubre de 2026**. Rama: `codex/v1-manual-transactions`.

## Entrega

- Registro y selección de empresa con cuenta manual, saldo y fecha de corte.
- Captura de ingresos y egresos con categoría opcional, normalización y clasificación.
- Permisos por empresa, validación Decimal y fechas, sesión/CSRF, auditoría y reintentos idempotentes.
- Actualización del historial, categorías, cobertura, escenario y pronóstico tras guardar.
- **Resumen inmediato** (Operación → Resumen): promedio neto diario de todo el historial registrado hasta la última operación ocurrida (o el corte declarado si es posterior), más compromisos pendientes. No exige confirmar cobertura.
- **Predicciones avanzadas** (Análisis → Predicciones): requieren cobertura confirmada y una fecha de corte común entre cuentas COP.
- **Pagos y cobros mensuales** (Operación → Cobros y pagos): programación manual de nómina u otros importes.
- Arranque local con `manage.py runserver` y `BACKGROUND_MODE=database`: el worker de la cola de base de datos se inicia automáticamente.

## Recorrido y cifras esperadas

1. Crear una empresa de prueba con cuenta manual, saldo 500.000 COP y corte de hoy.
2. Registrar ingreso 70.000 y egreso 140.000 dentro de los últimos siete días. El saldo declarado sigue en 500.000: ya incluye ese historial.
3. Abrir Operación → Resumen: combina de inmediato el promedio neto diario con los compromisos pendientes y recalcula la gráfica, sin pedir confirmación de cobertura. Flujo neto diario: (70.000 − 140.000) / 7 = −10.000 COP. Sin obligaciones: saldo a 30 días = 200.000; 60 días = −100.000; 90 días = −400.000. Primer déficit: día 51 después del corte. Es una estimación orientativa, no una probabilidad.
4. Para las predicciones avanzadas, confirmar la cobertura en Configuración → Cuentas y saldos con «Confirmar historial completo», desde seis días antes del corte. Confirmar únicamente si se registró toda la actividad; días vacíos cuentan como cero. Las cuentas COP deben compartir la misma fecha de corte.
5. En Análisis → Predicciones elegir la estimación inicial y guardarla. Registrar un movimiento nuevo dentro del periodo retira la cobertura; revisar y confirmar otra vez antes de recalcular. Las ejecuciones guardadas no cambian.
6. Para enseñar solo obligaciones, crear otra empresa de prueba con 500.000 COP, cobro 119.000 a corte+10 y pago 700.000 a corte+15. Sin historial, el escenario contractual queda en 500.000 + 119.000 − 700.000 = −81.000 desde el pago. No confundirlo con la estimación que incluye flujo variable.
7. Programar la nómina mensual: en Operación → Cobros y pagos → Pagos y cobros mensuales, escribir concepto (por ejemplo «Sueldos»), valor, día 1 y fecha inicial, y pulsar «Programar todos los meses». Deja la fecha final vacía para repetir cada mes; si eliges día 29–31, los meses cortos usan su último día. Aparece en calendario y proyecciones y no realiza transferencias. Para cambiar importe o frecuencia, detén la programación y crea otra; al pagar, concílialo con su movimiento.
8. Cerrar sesión y volver a entrar para comprobar persistencia.

Usar empresas de prueba separadas por presentación permite repetir el caso sin borrar datos previos.

## Reglas y límites

El movimiento representa dinero ocurrido hasta hoy, con fecha inicial de hoy; también se pueden capturar operaciones posteriores al corte. Los compromisos futuros se registran en Obligaciones. El alta no recalcula el saldo declarado ni ejecuta pagos.

Regla de no duplicar el saldo declarado: el Resumen parte del saldo declarado y suma a la caja disponible solo los movimientos posteriores a ese corte; los anteriores o iguales ya están incluidos. Los pronósticos avanzados parten del saldo declarado al corte común y no suman movimientos posteriores: actualizar la fecha y el saldo del corte para incorporarlos.

Resumen y predicciones avanzadas son distintos: el Resumen usa el promedio neto de todo el historial registrado hasta su fecha efectiva más los compromisos pendientes, con días vacíos como cero, y no exige cobertura. Las predicciones avanzadas sí requieren cobertura confirmada con corte común; los métodos de 90 días completos y los cuantiles del híbrido exigen más historial. Ninguno es un modelo calibrado ni una garantía; la estimación excluye importes conciliados del flujo residual y puede repetir movimientos excepcionales.

## Arranque local

Dos ventanas CMD (backend Django y frontend React/Vite); SQLite local, sin Docker. En el backend define `DJANGO_DEBUG=1`, `POSTGRES_HOST=` y `BACKGROUND_MODE=database`, ejecuta `migrate` y luego `runserver`. Con esa configuración, `manage.py runserver` arranca solo el worker local de la cola de base de datos y la consola muestra «Cola local activa»: las dos ventanas bastan para importar archivos o sincronizar Mock Bank. Solo si decides operar el worker por separado, define `DJANGO_LOCAL_WORKER=0` y abre una tercera ventana con `manage.py run_background`.

Para iniciar localmente y consultar evidencia: [pruebas](TESTING.md), [manual](USER_MANUAL.md), [estado](IMPLEMENTATION_STATUS.md). Escritorio, móvil, banca externa, correo real y validación científica siguen fuera de esta entrega. No se ha publicado esta rama en el alojamiento.


## Preparación automática del caso (SQLite local)

Con un usuario existente, ejecutar primero `python backend/manage.py prepare_web_demo --username TU_USUARIO --dry-run` y después la misma orden sin `--dry-run`. Crea dos empresas nuevas: Obligaciones y Historial manual, con fecha relativa al corte, auditoría y sin modificar lotes previos ni contraseñas. Solo funciona en desarrollo con SQLite local; no utilizar `seed_demo` para reiniciar un caso del usuario. Instrucciones completas en el [manual](USER_MANUAL.md).
