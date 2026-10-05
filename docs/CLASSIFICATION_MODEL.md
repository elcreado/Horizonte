# Clasificación experimental por empresa

TF-IDF con unigramas/bigramas y centroides normalizados, sin dependencias de servicios externos.
Consulta: `GET /api/companies/{company}/movements/{movement}/category-suggestion/`.
Requiere sesión y membresía; el movimiento debe pertenecer a esa empresa.

- Entrena con hasta 1.000 movimientos manualmente clasificados de esa empresa y dirección.
- Excluye Otros, el movimiento consultado y su misma descripción normalizada del entrenamiento.
- Requiere dos categorías con al menos tres descripciones distintas cada una; repeticiones no
  aumentan soporte. Etiquetas contradictorias de la misma descripción hacen el modelo no disponible.
- Sugiere con similitud mínima 0,35 y margen 0,15; umbrales heurísticos fijados, sin precisión
  validada. Un texto desconocido o ambiguo produce abstención.
- Similitud no equivale a confianza probabilística. No modifica categoría ni aplica sugerencias
  durante importación. Las reglas existentes siguen funcionando; la revisión humana prevalece.
- La consulta usa correcciones actuales: no constituye un backtest histórico. Para medir
  rendimiento habrá que separar ejemplos por tiempo/entidad y evitar etiquetas futuras.

Pruebas de soporte mínimo, repetición, contradicciones, abstención, consulta sin mutación e
imposibilidad de entrenar con etiquetas de otra empresa implementadas. UI en Movimientos →
Clasificar → Sugerir categoría. Seleccionar la propuesta solo rellena el selector; Guardar categoría
aplica la corrección manual existente. Cancelar no aplica nada. Consultas se cancelan al cerrar
el editor y no sustituyen automáticamente la selección del usuario.
Evaluador selectivo en `evaluation.py`: cobertura, acierto condicionado a sugerencia, fracción
correcta de todas las observaciones, matriz de confusión y precisión/recall/F1 por categoría.
Las abstenciones cuentan como casos no resueltos, incluyendo falsos negativos de su categoría.
Una precisión con denominador cero devuelve null; no se convierte en cero ni en 100 %.
Rechaza descripción normalizada compartida entre entrenamiento y prueba y repeticiones de
descripción en la prueba. El llamador debe garantizar misma empresa/dirección y etiquetas
disponibles al corte; separar textos no garantiza separación de comercio o plantilla semántica.
No se han medido resultados de generalización con un corpus representativo.

## Evaluación reproducible de corpus

Comando sin acceso a BD ni servicios externos:

```powershell
.venv\Scripts\python.exe backend/manage.py research_classification --input corpus.csv --company empresa-prueba --direction out --cutoff 2026-06-30 --output data/generated/classification-evaluation.json
```

CSV UTF-8 de hasta 2 MB/10.000 filas, columnas exactas:
`company_id,direction,date,reviewed_on,description,category,group_id`.
Empresa y dirección deben coincidir con los argumentos en todas las filas. Fechas ISO;
categorías compatibles con ingreso/egreso. `group_id` identifica comercio o plantilla: debe
ser asignado de manera consistente al preparar el corpus, no inventado por fila para evitar
el control de solapamiento.

- Entrenamiento: fecha de movimiento y revisión anteriores o iguales al corte.
- Etiquetas de movimientos antiguos revisadas después del corte se excluyen y se contabilizan.
- Prueba: movimientos posteriores al corte. La revisión no puede preceder al movimiento.
- Grupos compartidos entre entrenamiento/prueba y descripciones normalizadas repetidas se
  rechazan. Este protocolo mide generalización a grupos distintos, no repetición de comercios.
- El JSON incluye hash del archivo, corte, empresa/dirección, conteos y métricas, sin guardar
  descripciones. No sobrescribe el corpus. Mantener archivos privados fuera de Git y usar
  identificadores anonimizados; el formato no prueba por sí solo la procedencia de las etiquetas.

Validación con fixtures confirma corte de etiquetas y rechazo de grupos/empresas mezclados.
No se presenta el resultado de fixtures como precisión real o validación de producción.

Falta corpus etiquetado de evaluación, ejecución de métricas cobertura/precisión, controles de generalización
y QA visual/interacción. No se declara RF-07 completo.
