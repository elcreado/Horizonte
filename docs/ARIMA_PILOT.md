# Evaluación sintética de caja — corte reproducible

Reproducir con `python backend/manage.py research_forecast --companies 5 --seed 20261004 --step 90 --output data/generated/arima-pilot --report docs/ARIMA_PILOT.md --include-arima`. No requiere Docker ni APIs.

Dataset: 5 empresas, 24 meses (2023–2024), 3655 días-empresa completos.
Semilla 20261004; 2 empresas tienen saldo negativo en algún momento.

Entrenamiento inicial 180 días, expansión temporal y paso de 90 días.
Los flujos conocidos se incorporan solo si su anuncio ya ocurrió al corte.
MAE/RMSE son del saldo diario acumulado en COP. Nuevo déficit excluye cortes ya negativos.
DLDE solo cuando ambos escenarios tienen déficit; las ausencias no se convierten en cero.

| Horizonte | Método | Ventanas | MAE saldo COP | RMSE saldo COP | Precision | Recall | F1 | DLDE días | Pares DLDE |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 30 | naive | 30 | 4108549.17 | 13451752.52 | — | 0.000 | 0.000 | — | 0 |
| 30 | seasonal_naive | 30 | 2270963.41 | 14077687.55 | — | 0.000 | 0.000 | — | 0 |
| 30 | ses | 30 | 2760891.69 | 14141595.33 | — | 0.000 | 0.000 | — | 0 |
| 30 | hybrid_weekly | 30 | 2270963.41 | 14077687.55 | — | 0.000 | 0.000 | — | 0 |
| 30 | arima_100 | 30 | 2701183.54 | 14112812.18 | — | 0.000 | 0.000 | — | 0 |
| 60 | naive | 30 | 8486882.88 | 18116473.56 | — | 0.000 | 0.000 | — | 0 |
| 60 | seasonal_naive | 30 | 6197126.83 | 19091285.02 | — | 0.000 | 0.000 | — | 0 |
| 60 | ses | 30 | 6292988.99 | 19109275.99 | — | 0.000 | 0.000 | — | 0 |
| 60 | hybrid_weekly | 30 | 3663959.02 | 17869605.05 | 1.000 | 0.500 | 0.667 | 0.000 | 1 |
| 60 | arima_100 | 30 | 7301124.58 | 19543731.71 | — | 0.000 | 0.000 | — | 0 |
| 90 | naive | 30 | 13131871.74 | 22133924.91 | — | 0.000 | 0.000 | — | 0 |
| 90 | seasonal_naive | 30 | 10961820.93 | 23120158.26 | — | 0.000 | 0.000 | — | 0 |
| 90 | ses | 30 | 10676068.83 | 23013240.36 | — | 0.000 | 0.000 | — | 0 |
| 90 | hybrid_weekly | 30 | 4539693.70 | 19228608.80 | 1.000 | 0.500 | 0.667 | 0.000 | 1 |
| 90 | arima_100 | 30 | 12729808.93 | 24309226.50 | — | 0.000 | 0.000 | — | 0 |

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

- `daily.csv`: SHA-256 `f5193f5c8ae8e84a414cc161b2859895047a523fa5d93bfb44f1252169d41aca`
- `obligations.csv`: SHA-256 `c6c492250ab38a77a00920d22ecca0aed45a6caa46ea375761f6327916b32420`

Datos y métricas sin redondear en `data/generated/arima-pilot`: `manifest.json`, `daily.csv`, `obligations.csv` y `evaluation.json`.
Reproducir con la misma semilla y parámetros; se rechazan archivos cuyo checksum cambió.
Los CSV se regeneran y están ignorados por Git; este informe queda versionado.
