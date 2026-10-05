# Medición local de importación

Fecha: 2026-09-30. PostgreSQL 16 en Docker Desktop, backend Python local.

Comando reproducible: `.venv/Scripts/python backend/manage.py benchmark_import`, con las variables POSTGRES del entorno local. Requiere PostgreSQL; no llama proveedores externos.

| Operación | Filas | Creadas | Duplicadas | Segundos |
|---|---:|---:|---:|---:|
| Primera importación CSV | 10000 | 10000 | 0 | 58.776 |
| Repetición CSV | 10000 | 0 | 10000 | 31.718 |

Archivo sintético generado en memoria: 348926 bytes. Se verificaron recuentos, saldo intacto y rollback de los registros temporales. El comando ejecuta la función de tarea directamente: no mide HTTP, espera de cola, transporte Redis, commit final ni carga concurrente. Una transacción exterior permite revertir todo. Las secuencias de identificadores pueden avanzar aun tras rollback.

Esta observación demuestra integridad a 10000 filas, pero no prueba «sin degradación relevante». El pipeline hace consultas por fila; se requiere optimización y comparación bajo el mismo entorno. No representa p95 ni un SLA. XLSX a esa escala se ha comprobado en parser, no en esta medición de base de datos.


## Importador por lotes

Misma medición local después de precargar movimientos y reglas y usar inserciones de 500 filas:

| Operación | Filas | Creadas | Duplicadas | Segundos |
|---|---:|---:|---:|---:|
| Primera importación CSV | 10000 | 10000 | 0 | 0.645 |
| Repetición CSV | 10000 | 0 | 10000 | 0.221 |

Saldo y rollback verificados. Son observaciones individuales, con cachés y carga del equipo no controlados, no p95 ni prueba concurrente. Se conservan las limitaciones metodológicas anteriores. La suite verifica conflictos atómicos, duplicados dentro del archivo, correcciones manuales y menos de 80 consultas para 1000 filas. Las reglas por empresa se leen una vez por trabajo; cambios posteriores se aplican a siguientes importaciones.


## XLSX y concurrencia

Comando: `.venv/Scripts/python backend/manage.py benchmark_import --format xlsx`. Libro sintético de 174038 bytes generado en memoria (generación fuera del tiempo medido). El tiempo incluye validación ZIP/XML, lectura XLSX, normalización, clasificación e inserción PostgreSQL.

| Operación | Creadas | Duplicadas | Segundos |
|---|---:|---:|---:|
| XLSX inicial | 10000 | 0 | 1.444 |
| XLSX repetido | 0 | 10000 | 1.066 |

Rollback y saldo verificados. Persisten las limitaciones: llamada directa a la tarea, sin cola ni HTTP, sin commit final ni medida p95.

`test_concurrent_imports.py` usa conexiones PostgreSQL independientes y una barrera de inicio: dos trabajos solapados más una reentrega del mismo trabajo producen exactamente 200 movimientos; dos trabajos con datos contradictorios dejan únicamente las dos filas del ganador y marcan fallido el otro. Los timeouts de bloqueo/sentencia acotan la prueba. Esto verifica integridad concurrente, no capacidad de múltiples workers en producción ni carga sostenida.
## Medición remota del 5 de octubre de 2026

- Recorrido real: cliente HTTP con sesión/CSRF → Render Free Virginia → cola en PostgreSQL
  Supabase mediante Session pooler → worker de BD en el servicio web.
- CSV sintético de 10.000 movimientos, 653.026 bytes en la petición multipart, sin comercios
  explícitos y con importes alternos de +1/-1 COP. IDs externos únicos.
- API respondió 202; trabajo terminó `completed` con 10.000 movimientos creados.
- Tiempo observado desde el envío hasta detectar finalización: **12,00 segundos**. Incluye
  latencia y sondeo cada tres segundos; no es el tiempo exacto interno de ejecución.
- Una ejecución con servidor despierto, una empresa y un cliente. No acredita p95, carga
  concurrente, arranque en frío, otros formatos ni cumplimiento global de rendimiento.
- Evidencia local sin credenciales: `.local-logs/remote-import-10000.json`.
