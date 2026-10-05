# Evaluación probabilística: contrato y pendientes

El módulo `backend/apps/forecast/probability_metrics.py` evalúa predicciones P10/P50/P90 de saldo.
El módulo de métricas no genera cuantiles. La evaluación del dataset se encuentra en
`PROBABILITY_RESULTS.md`; la UI no
presenta intervalos ni probabilidades como si estuvieran validados.

- Entradas: observaciones y predicciones emparejadas por empresa/fecha, del mismo tamaño positivo,
  con importes Decimal finitos. El llamador debe garantizar el corte temporal fuera de muestra.
- Pinball por cuantil: `q * (observado - previsto)` si el error es positivo; `(q - 1) * error`
  en caso contrario. Se promedia sin redondear a centavos la métrica. Para P50 corresponde a
  la mitad del error absoluto medio, no al MAE completo.
- Cobertura puntual: proporción de observaciones dentro de P10–P90, incluyendo extremos.
  Se informa cobertura nominal 0,8 y amplitud media en COP. Esos números no prueban calibración.
- CDF empírica: proporción de observaciones menores o iguales a cada cuantil. Con distribuciones
  discretas los empates afectan la interpretación; no se fuerza coincidencia exacta con q.
- Se rechazan cuantiles cruzados, campos ausentes y muestras de distinto tamaño. No se reordenan
  ni descartan predicciones erróneas para mejorar las métricas.
- La cobertura por día no equivale a probabilidad de cubrir toda la trayectoria ni a probabilidad
  de déficit dentro del horizonte. No derivar esa última multiplicando coberturas diarias.

Primera estimación implementada en `empirical_quantiles.py`: Seasonal Naive sobre flujo variable
y cuantiles empíricos del error acumulado en ventanas históricas enteramente anteriores al corte.
Usa interpolación lineal `(n-1)*q`, al menos 20 orígenes y paso semanal. Las ventanas pueden
solaparse; 20 orígenes no equivalen a 20 muestras independientes. Compromisos conocidos y
recurrencias se consideran puntuales; no cubre su incertidumbre ni shocks no observados.
Si faltan ventanas completas, rechaza el cálculo. No utiliza simulación aleatoria ni supone
independencia de errores diarios. Historial semanal exacto puede generar intervalos de ancho cero;
eso describe la muestra, no demuestra ausencia de riesgo futuro.

Rolling-origin sintético agregado por horizonte y perfil implementado. Cobertura puntual medida para
30/60/90 días: 0,7807 / 0,7726 / 0,7544, inferior al 0,8 nominal. No se declara calibración.
El desglose muestra cobertura a 90 días de 0,7031 estacional y 0,7092 volátil, frente a 0,7975
en comercio. No se escogen parámetros a partir de estos resultados; requieren otro período
de validación o ajuste exclusivamente dentro del pasado de cada corte.
Falta calibración validada usando exclusivamente pasado y persistencia/API/UI.
La validación real requiere datos autorizados. Motor vivo conectado para `hybrid_weekly`: requiere
270 días completos por cuenta, devuelve cuantiles experimentales en API/tabla y conserva la
serie de entrada al guardar. Si falta cobertura, mantiene saldo puntual sin cuantiles.
No reutilizar
la ventana final de evaluación para escoger parámetros.

Pruebas actuales: penalización asimétrica calculada a mano, caso P50, cobertura/amplitud,
cuantiles cruzados, no finitos y muestras inválidas. No son pruebas de precisión de un modelo.

Reproducir sobre el dataset generado por `research_forecast`:

```powershell
.venv\Scripts\python.exe backend/manage.py research_probability
```

Produce el reporte Markdown y `data/generated/probability-evaluation.json`, verifica SHA-256
del manifiesto y contabiliza ventanas no disponibles antes de consultar sus saldos futuros.

Fórmula contrastada con la [documentación oficial de métricas de scikit-learn](https://scikit-learn.org/stable/modules/model_evaluation.html).
