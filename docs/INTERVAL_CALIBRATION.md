# Candidato de calibración temporal

Implementación: `backend/apps/forecast/calibrated_intervals.py`.
Estado: candidato offline; no conectado a las rutas ni a la interfaz de producción.

El ajuste de errores semanales utiliza exclusivamente el prefijo anterior al bloque reservado.
Veinte orígenes posteriores, separados por siete días, calculan errores acumulados por cada día
del horizonte. Sus resultados están observados por completo antes del corte de predicción.
El límite inferior y superior se expanden con el estadístico de orden 17/20
(`ceil((20+1)*0.8)`), truncado a cero para evitar contracción. La mediana queda intacta.
Se registran frontera de entrenamiento, rango de calibración y correcciones por horizonte.

La regla sigue la idea de puntuaciones de error del artículo
[Conformalized Quantile Regression](https://arxiv.org/abs/1905.03222).
Las ventanas solapadas de una serie temporal no establecen intercambiabilidad; no se afirma
la garantía de cobertura del artículo. Los extremos se llaman `lower`/`upper`, no P10/P90:
calibrar la cobertura del intervalo no demuestra calibración individual de los cuantiles.
No se deriva probabilidad de déficit de estos límites. Se calibra solamente flujo residual;
obligaciones y recurrencias se tratan como compromisos puntuales, sin incertidumbre de cumplimiento.

Las pruebas cubren tendencia en el bloque reservado, aritmética de compromisos, orden de límites,
historia insuficiente, valores no finitos, métricas y ventanas emparejadas.

## Evaluación realizada

[INTERVAL_RESULTS.md](INTERVAL_RESULTS.md) compara 100 empresas sintéticas en cortes idénticos,
con paso de 30 días. Reproducir tras generar el corpus con:

```powershell
python backend/manage.py research_forecast --companies 100 --seed 20261004 --output data/generated/arima-full
python backend/manage.py research_intervals --input data/generated/arima-full --report docs/INTERVAL_RESULTS.md --step 30
```

El primer comando regenera el mismo corpus sin requerir ARIMA; las métricas de intervalos están
en `data/generated/arima-full/interval-evaluation.json`. Los checksums del corpus están en su
manifest y se verifican antes de evaluar. No se ajustaron parámetros usando estos resultados.
Las ventanas comienzan al reunir 20 orígenes de ajuste y 20 de calibración completos; no comparan
con todas las ventanas del informe probabilístico anterior, sino únicamente cortes disponibles
para ambos métodos.

Cobertura agregada corregida: 0,8269/0,8296/0,8101 frente a 0,7742/0,7705/0,7413 sin corregir.
La amplitud aumenta en los tres horizontes. El interval score empeora ligeramente a 30 días y
mejora a 60/90; el perfil volátil a 90 días conserva cobertura de solo 0,6701.
No basta el agregado para declarar calibración por perfil. Sigue pendiente corpus independiente,
otros regímenes y validación de los errores de compromisos antes de integrar en producción.
