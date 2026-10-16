# Evaluación sintética de cuantiles experimentales

Generada por `research_probability`; no demuestra precisión con empresas reales.

Dataset: 100 empresas; entrenamiento mínimo 180 días; paso 30 días.

| Días | Ventanas | No disponibles | Cobertura puntual | Amplitud COP | Pinball P10 | Pinball P50 | Pinball P90 |
|---|---|---|---|---|---|---|---|
| 30 | 1800 | 0 | 0.7807 | 1797810.30 | 623743.34 | 564350.23 | 184622.37 |
| 60 | 1600 | 100 | 0.7726 | 3399779.23 | 1374966.09 | 1198760.10 | 373761.12 |
| 90 | 1400 | 200 | 0.7544 | 5173918.54 | 2293089.14 | 1987898.55 | 608787.27 |

Cobertura nominal P10–P90: 0,8. Métricas por día, no por trayectoria completa.

## Desglose por perfil

| Perfil | Días | Ventanas | Cobertura puntual | Amplitud COP | Pinball P50 |
|---|---|---|---|---|---|
| declining | 30 | 360 | 0.8160 | 1009848.59 | 147392.96 |
| retail | 30 | 360 | 0.8094 | 925227.75 | 141346.34 |
| seasonal | 30 | 360 | 0.7365 | 1247908.61 | 225867.85 |
| services | 30 | 360 | 0.7644 | 939753.43 | 154170.61 |
| volatile | 30 | 360 | 0.7774 | 4866313.09 | 2152973.38 |
| declining | 60 | 320 | 0.8033 | 1795001.68 | 277364.20 |
| retail | 60 | 320 | 0.8083 | 1663284.82 | 258954.64 |
| seasonal | 60 | 320 | 0.7355 | 3148702.09 | 582673.41 |
| services | 60 | 320 | 0.7664 | 1701179.60 | 281141.56 |
| volatile | 60 | 320 | 0.7493 | 8690727.96 | 4593666.67 |
| declining | 90 | 280 | 0.8031 | 2588478.64 | 399789.77 |
| retail | 90 | 280 | 0.7975 | 2401702.13 | 380647.80 |
| seasonal | 90 | 280 | 0.7031 | 5876769.37 | 1209586.75 |
| services | 90 | 280 | 0.7589 | 2448869.79 | 412747.86 |
| volatile | 90 | 280 | 0.7092 | 12553772.77 | 7536720.56 |

- Datos sintéticos y etiquetas de flujo variable perfectas; no mide eficacia real.
- Recurrencias simulan revisión y vínculo perfectos con información disponible al corte.
- Cuantiles condicionados a compromisos puntuales, sin incertidumbre de cumplimiento.
- Ventanas solapadas; cobertura puntual agregada no demuestra calibración condicional.
- No se seleccionan parámetros usando estas ventanas de prueba.
