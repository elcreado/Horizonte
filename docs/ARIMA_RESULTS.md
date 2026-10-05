# Evaluación sintética de caja — corte reproducible

Reproducir con `python backend/manage.py research_forecast --companies 100 --seed 20261004 --step 30 --output data/generated/arima-full --report docs/ARIMA_RESULTS.md --include-arima --arima-ses-fallback`. No requiere Docker ni APIs.

Dataset: 100 empresas, 24 meses (2023–2024), 73100 días-empresa completos.
Semilla 20261004; 40 empresas tienen saldo negativo en algún momento.

Entrenamiento inicial 180 días, expansión temporal y paso de 30 días.
Los flujos conocidos se incorporan solo si su anuncio ya ocurrió al corte.
MAE/RMSE son del saldo diario acumulado en COP. Nuevo déficit excluye cortes ya negativos.
DLDE solo cuando ambos escenarios tienen déficit; las ausencias no se convierten en cero.

| Horizonte | Método | Ventanas | MAE saldo COP | RMSE saldo COP | Precision | Recall | F1 | DLDE días | Pares DLDE |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 30 | naive | 1800 | 3181194.90 | 9122355.81 | 0.815 | 0.500 | 0.620 | 0.000 | 22 |
| 30 | seasonal_naive | 1800 | 1127113.47 | 8387455.75 | 1.000 | 0.523 | 0.687 | 0.000 | 23 |
| 30 | ses | 1800 | 1654671.02 | 8487330.31 | 0.958 | 0.523 | 0.676 | 0.000 | 23 |
| 30 | hybrid_weekly | 1800 | 1127113.47 | 8387455.75 | 1.000 | 0.523 | 0.687 | 0.000 | 23 |
| 30 | arima_100_ses_fallback | 1800 | 1583095.06 | 8482261.90 | 1.000 | 0.295 | 0.456 | 4.462 | 13 |
| 60 | naive | 1700 | 7780300.21 | 16186427.74 | 1.000 | 0.321 | 0.486 | 2.963 | 27 |
| 60 | seasonal_naive | 1700 | 4709307.01 | 14030511.00 | 1.000 | 0.274 | 0.430 | 0.000 | 23 |
| 60 | ses | 1700 | 5224633.32 | 14330574.94 | 1.000 | 0.286 | 0.444 | 0.667 | 24 |
| 60 | hybrid_weekly | 1700 | 2309545.65 | 12544548.65 | 1.000 | 0.512 | 0.677 | 1.698 | 43 |
| 60 | arima_100_ses_fallback | 1700 | 5625756.83 | 14583489.14 | 1.000 | 0.155 | 0.268 | 4.462 | 13 |
| 90 | naive | 1600 | 13735859.76 | 24553961.47 | 1.000 | 0.218 | 0.358 | 2.963 | 27 |
| 90 | seasonal_naive | 1600 | 9852308.90 | 20660969.78 | 1.000 | 0.185 | 0.313 | 0.000 | 23 |
| 90 | ses | 1600 | 10435215.38 | 21248965.79 | 1.000 | 0.194 | 0.324 | 0.667 | 24 |
| 90 | hybrid_weekly | 1600 | 3662611.81 | 16111955.09 | 1.000 | 0.435 | 0.607 | 3.222 | 54 |
| 90 | arima_100_ses_fallback | 1600 | 11210672.96 | 21715516.89 | 1.000 | 0.105 | 0.190 | 4.462 | 13 |

## Límites y pendientes

- Historial diario completo y sin faltantes; no valida cold start ni datos reales.
- Flujo residual separado por el generador: extracción perfecta, sin error de clasificación.
- Obligaciones solo visibles desde announced_on; no se revelan compromisos futuros antes.
- Saldo inicial de 3 millones COP para declining y 12 millones para los demás, por escala.
- Dataset controlado para evaluación; no demuestra precisión en microempresas reales.
- Ventanas solapadas; los errores no son muestras independientes.
- Métricas agregadas sobre caja sintética; no prueba eficacia con empresas reales.
- No se optimizan parámetros ni se selecciona modelo usando estas ventanas de prueba.
- DLDE solo para pares con déficit; ausencias se reportan en la matriz de confusión.
- La detección de nuevo déficit excluye ventanas ya negativas al corte; se cuentan aparte.
- Sin intervalos: pinball y cobertura no se calculan todavía.
- El híbrido simula confirmación perfecta de recurrencias y vínculos por categoría sintética; la aplicación requiere revisión humana.
- Perfiles y shocks diseñados para incluir crisis; no representan su frecuencia real.
- Compromisos mensuales anunciados 30 días antes y shock 7 días antes; hybrid_weekly extrapola patrones desde el pasado y no predice shocks nuevos.
- No se conectan estas métricas retrospectivas a una etiqueta de confianza en la interfaz.
- Faltan Prophet, intervalos calibrados, corpus independiente y usabilidad.

## Integridad

- `daily.csv`: SHA-256 `dd0c1f3014a279ce2ed8600966ba77bc5766f23ee1730afe3950c84be95b4a0e`
- `obligations.csv`: SHA-256 `117fb84ffc9c38435091b6f033a3112695612aa569dca608843b8919779fdd73`

Datos y métricas sin redondear en `data/generated/arima-full`: `manifest.json`, `daily.csv`, `obligations.csv` y `evaluation.json`.
Reproducir con la misma semilla y parámetros; se rechazan archivos cuyo checksum cambió.
Los CSV se regeneran y están ignorados por Git; este informe queda versionado.

## Respaldo explícito de ARIMA

ARIMA(1,0,0) usa SES en ajustes fallidos. Las métricas corresponden a esta política combinada, no a ARIMA puro.

- 30 días: 48 ventanas con SES de 1800 evaluadas.
- 60 días: 44 ventanas con SES de 1700 evaluadas.
- 90 días: 43 ventanas con SES de 1600 evaluadas.
Cada corte y motivo está registrado en arima_fallbacks del JSON; ninguna ventana se excluye para mejorar el promedio.
