# Primera versión web con captura manual

Revisión: **16 de octubre de 2026**. Rama: `codex/v1-manual-transactions`.

## Entrega

- Registro y selección de empresa con cuenta manual, saldo y fecha de corte.
- Captura de ingresos y egresos con categoría opcional, normalización y clasificación.
- Permisos por empresa, validación Decimal y fechas, sesión/CSRF, auditoría y reintentos idempotentes.
- Actualización del historial, categorías, cobertura, escenario y pronóstico tras guardar.
- Estimación inicial 30/60/90 basada en el promedio neto de todo el historial hasta el corte, con mínimo siete días completos confirmados.
- Métodos previos y guardado de ejecuciones siguen disponibles; sus límites se conservan.

## Recorrido y cifras esperadas

1. Crear una empresa de prueba con cuenta manual, saldo 500.000 COP y corte de hoy.
2. Registrar ingreso 70.000 y egreso 140.000 dentro de los últimos siete días. El saldo declarado sigue en 500.000: ya incluye ese historial.
3. En Saldos de cuentas, abrir «Confirmar historial completo» y confirmar desde seis días antes del corte. Confirmar únicamente si se registró toda la actividad; días vacíos cuentan como cero.
4. En Predicciones con tus datos, elegir estimación inicial. Flujo neto diario: (70.000 −140.000) /7 = −10.000 COP. Sin obligaciones: saldo final 30 días = 200.000; 60 días = −100.000; 90 días = −400.000. Primer déficit: día 51 después del corte.
5. Guardar el pronóstico. Registrar un movimiento nuevo dentro del periodo retira la cobertura; revisar y confirmar otra vez antes de recalcular. Las ejecuciones guardadas no cambian.
6. Para enseñar solo obligaciones, crear otra empresa de prueba con 500.000 COP, cobro 119.000 a corte+10 y pago 700.000 a corte+15. El escenario contractual queda en −81.000 desde el pago. No confundirlo con la estimación que incluye flujo variable.
7. Cerrar sesión y volver a entrar para comprobar persistencia.

Usar empresas de prueba separadas por presentación permite repetir el caso sin borrar datos previos.

## Reglas y límites

El movimiento representa dinero ocurrido hasta hoy, con fecha inicial de hoy; también se pueden capturar operaciones posteriores al corte. Para incluirlas en la predicción hay que actualizar el corte y su saldo. Los compromisos futuros se registran en Obligaciones. El alta no recalcula el saldo declarado ni ejecuta pagos.

La estimación inicial repite el promedio de todo el historial hasta el corte, con mínimo siete días; no es un modelo calibrado ni una garantía. Excluye importes conciliados del flujo residual. No estima recurrencias por separado y puede repetir movimientos excepcionales. Los otros modelos conservan el requisito de 90 días completos; cuantiles del híbrido requieren más historial.

Para iniciar localmente y consultar evidencia: [pruebas](TESTING.md), [manual](USER_MANUAL.md), [estado](IMPLEMENTATION_STATUS.md). Escritorio, móvil, banca externa, correo real y validación científica siguen fuera de esta entrega. No se ha publicado esta rama en el alojamiento.
