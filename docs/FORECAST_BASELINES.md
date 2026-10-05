# Referencias del motor de pronóstico

Módulo: backend/apps/forecast/baselines.py.

## Comparación ARIMA completada (5 de octubre de 2026)

La evaluación de 100 empresas sintéticas y 24 meses está en [ARIMA_RESULTS.md](ARIMA_RESULTS.md).
ARIMA(1,0,0), con SES únicamente ante fallo recuperable de ajuste, comparte las mismas ventanas
temporales que los demás métodos. Necesitó respaldo en 48/1800, 44/1700 y 43/1600 ventanas
para 30/60/90 días. No se descartaron ventanas fallidas. En los tres horizontes su MAE de saldo
supera al híbrido y su recall de nuevo déficit es menor; no se incorpora a las rutas de producción.
El orden fue fijado antes de evaluar, sin selección de parámetros usando las ventanas de prueba.
Las dependencias opcionales están en `backend/requirements-research.txt`; no requiere servicios externos.
Esta comparación resuelve el pendiente de ARIMA(1,0,0) de las notas históricas inferiores,
pero no valida otros órdenes, SARIMA, Prophet, datos reales ni intervalos calibrados.

## Método híbrido con recurrencias confirmadas

`method=hybrid_weekly` agrega estimaciones de fechas de patrones confirmados **vigentes** al patrón
semanal residual y a las obligaciones pendientes. Detecta el patrón con historia hasta el corte y
exige que su fingerprint coincida con la revisión actual; evidencia cambiada exige nueva confirmación.
Excluye esos movimientos históricos del residual, separa `recurring_flow` y no crea obligaciones.
Vínculos existentes y referencias `REC-...` prevalecen incluso cancelados, saldados o movidos de fecha.
Obligaciones ambiguas de igual fecha/sentido devuelven 409 para revisión, evitando sumar dos veces.
Las ejecuciones guardadas conservan fechas estimadas y causas de supresión.

La evaluación sintética compara este método con los tres baselines. En el horizonte de 90 días,
el MAE de saldo baja de 9.852.308,90 a 3.662.611,81 COP respecto a Seasonal Naive y el recall de
nuevo déficit sube de 0,185 a 0,435. Son resultados del corpus diseñado: revisión/vínculos perfectos
y sin faltantes; no demuestran precisión con empresas reales ni intervalos calibrados. Los shocks
que aún no se anunciaron siguen sin poder incorporarse como flujos conocidos.

Evaluación reproducible de saldo y déficit: `python backend/manage.py research_forecast` genera
100 empresas sintéticas ×24 meses y el informe `docs/RESEARCH_RESULTS.md`. Incorpora solo obligaciones
anunciadas al corte, evalúa por prefijos temporales y cuenta aparte los saldos ya negativos. No usa
estos resultados de prueba para elegir automáticamente un modelo en la aplicación. El historial de
producción y la calibración de intervalos siguen pendientes.

Se implementan Naive (último flujo diario observado) y Seasonal Naive semanal (últimos siete flujos repetidos), siguiendo https://otexts.com/fpp3/simple-methods.html. También se ofrece suavizado exponencial simple (SES) con α fijo de 0,30, inicializado con la primera observación; estima un nivel constante para los días futuros. El parámetro no se ha optimizado con datos reales. Ninguno de los tres métodos produce cuantiles ni probabilidades y no sustituyen todavía el escenario del dashboard.

La preparación residual conserva el importe no conciliado de cada movimiento y excluye por completo los movimientos identificados como recurrentes. Una recurrencia conciliada no se descuenta dos veces. No se usan movimientos posteriores al corte. Los días sin registros se convierten en cero solamente si el llamador declara cobertura completa; ahora puede registrarse por cuenta mediante una declaración auditada en el dashboard.

La composición híbrida suma al saldo inicial únicamente flujos conocidos futuros y estimaciones residuales. El llamador debe proporcionar flujos conocidos sin duplicar obligaciones y recurrencias. Las obligaciones ya representadas por recurrencias siguen siendo una única fuente.

La evaluación rolling-origin entrena con prefijos y reserva ventanas completas de 30/60/90 días. Reporta MAE, RMSE y sMAPE de flujo diario; los pares cero/cero aportan cero a sMAPE. No son métricas de saldo acumulado. Ventanas solapadas no representan muestras independientes. Mínimo de entrenamiento y paso son parámetros experimentales, no criterios de confianza validados.

Pendiente: extracción ORM versionada históricamente, evaluación persistida/asíncrona, ETS estacional, ARIMA/SARIMA/Prophet, intervalos calibrados y comparación en dataset representativo. No evaluar el pasado con conciliaciones o etiquetas creadas después: se necesitan snapshots o reconstrucción temporal antes de conectar estos algoritmos al evaluador real.

Las pruebas verifican aritmética residual, periodicidad, acumulación del saldo, corte temporal y métricas sobre series sintéticas. No demuestran precisión predictiva en empresas reales.


## Referencia conectada a la aplicación

La API `GET /api/companies/{id}/experimental-forecast/?horizon=30|60|90&method=naive|seasonal_naive|ses` y la sección «Referencia estadística experimental» consultan movimientos hasta el corte compartido de las cuentas. La ventana de entrenamiento es de 90 días completos, declarados por propietario o contador para **cada cuenta** manual en el dashboard; Mock Bank declara su cobertura sintética al sincronizar. Una declaración humana no demuestra que el banco entregó todos los movimientos. Se exigen al menos cuatro días con flujo variable distinto de cero; si faltan datos, la API responde 409 y explica el motivo.

El residual descuenta importes de conciliaciones activas y los movimientos de recurrencias confirmadas que tienen una obligación futura vinculada dentro del horizonte. Las obligaciones pendientes se suman una sola vez como flujos conocidos. La referencia arranca del saldo declarado, sin volver a sumar el historial. Cambiar el corte o importar nuevas filas en un periodo confirmado retira la declaración de cobertura. Los estados de la UI siguen separados: el escenario principal conserva solo obligaciones; la referencia es experimental y no incluye P10/P50/P90, validación de precisión con empresas reales ni probabilidad de déficit.

Las pruebas de integración cubren falta de cobertura, suma de obligación y estimación residual, exclusión de recurrencia, aislamiento de empresa, permisos y revocación de cobertura. Las ejecuciones estadísticas guardadas incluyen serie de entrenamiento, flujos conocidos y resultado; son revisables desde el dashboard. Faltan versiones temporales de conciliaciones para evaluación histórica, comparar modelos más avanzados y calibrar intervalos antes de presentar un pronóstico probabilístico.
## Candidato ARIMA de investigación

Política opcional `--arima-ses-fallback`: registra cada fallo de ajuste y usa SES en la
misma ventana. El método se identifica como `arima_100_ses_fallback`; sus métricas no son
de ARIMA puro. El informe JSON guarda compañía, corte, horizonte y motivo, y cada métrica
incluye `fallback_windows`. Prueba automatizada fuerza fallos y verifica igualdad de ventanas
y MAE con SES, sin depender de instalar statsmodels en CI.

Ya se integró la opción `--include-arima` en `research_forecast`. Piloto completado con
cinco empresas ×24 meses, cortes de 90 días y horizontes 30/60/90; resultados en `ARIMA_PILOT.md`.
La ejecución de 100 empresas con cortes de 30 días se detuvo ante un ajuste sin convergencia.
No existe todavía un resultado global aceptado. Falta registrar cobertura y ventanas fallidas
sin ocultarlas ni comparar promedios sobre conjuntos de ventanas distintos.

`arima_candidate.predict_arima` implementa ARIMA(1,0,0) con constante y estacionariedad
impuesta, orden prefijado antes de evaluar, entrenamiento mínimo de 60 días y ventana máxima
de 730 días. Escala solo con datos de entrenamiento y devuelve importes Decimal redondeados a
céntimos. Ajustes sin convergencia o predicciones no finitas fallan explícitamente.

Dependencias locales opcionales: `pip install -r backend/requirements-research.txt`.
Render no instala estas dependencias ni ejecuta este candidato. Se comprobó un ajuste real de
statsmodels 0.15.0 con 180 observaciones sintéticas y 30 predicciones finitas. Falta integrarlo
en rolling-origin y comparar 30/60/90 días sobre el dataset versionado; esta comprobación no
demuestra mejora de precisión ni calibración. No sustituye los métodos del producto.

Referencia: [API oficial ARIMA de statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima.model.ARIMA.html).
