# Pruebas y arranque vigentes

Revisión: **15 de octubre de 2026**. Para el estado de requisitos consultar
[resumen](ESTADO_Y_PENDIENTES.md); resultados actuales en [matriz](IMPLEMENTATION_STATUS.md).

## Usuario final: escritorio sin Docker

- Instalar `desktop/release/session-isolation/Horizonte Setup 0.1.0.exe` en Windows x64.
- Conectar con `https://horizonte-demo.onrender.com`; necesita internet y puede tardar al despertar.
- Inicio no exige sesión. Registrarse/acceder y seguir el [manual](USER_MANUAL.md).
- Usar el [recorrido de aceptación](acceptance/DESKTOP_ACCEPTANCE.md) para comparar importes.
- No arrancar Docker, Redis, Django ni Vite para consumir la aplicación alojada.
- Correo real no verificado: para probar recuperación se necesita proveedor/remitente/buzón;
  para los demás flujos no hacen falta credenciales bancarias reales ni servicios de pago.

## Desarrollador: verificaciones locales

Desde la raíz, con `.venv` y dependencias de frontend/escritorio preparadas:

```powershell
.venv\Scripts\ruff.exe check backend
.venv\Scripts\ruff.exe format --check backend
.venv\Scripts\python.exe backend/manage.py makemigrations --check --dry-run
.venv\Scripts\python.exe backend/manage.py test backend/tests
npm --prefix frontend run build
npm --prefix desktop test
```

La suite sin variables PostgreSQL usa SQLite y omite comprobaciones específicas de PostgreSQL.
Nunca apuntar la suite a Supabase ni a datos de usuario: crea/destruye una BD de pruebas.
Si Windows bloquea la limpieza de temporales en el sandbox, registrar el error de permisos
y ejecutar en un entorno local autorizado; no confundirlo con una prueba aprobada o un bug funcional.

CI contiene backend, backend-postgres con BD efímera, frontend y desktop. El job desktop
solo usa Node: no instala ni prueba visualmente la aplicación.

## Desarrollo local opcional

- Requiere Python/Node, dependencias y Docker Desktop para el flujo de scripts existente.
- `scripts/start-dev.ps1` inicia dependencias, backend, worker y frontend; abrir
  `http://127.0.0.1:5173/`. Compose solo levanta PostgreSQL/Redis.
- Scripts separados: `start-backend.ps1` y `start-worker.ps1`. No dejar el frontend activo
  esperando que el usuario arranque un backend que no se ha iniciado.
- `npm --prefix desktop start` permite HTTP local solo en desarrollo; el instalador exige HTTPS.

## Datos y límites de prueba

- CSV/XLSX: `external_id,date,amount,description`, ingreso positivo/egreso negativo,
  fechas ISO, decimal con punto, ID estable; 2 MiB y 10.000 filas.
- XLSX: una hoja, columnas A–D, identificadores como texto y sin fórmulas.
- XML: UBL de prueba, UTF-8, hasta 2 MiB; empresa debe ser emisor/receptor. Revisar el
  pendiente antes de crear/vincular obligación. No certifica firma ni aceptación DIAN.
- Ejemplos: `frontend/public/movimientos-ejemplo.csv` y `frontend/public/factura-ejemplo.xml`.
- Importar historial no cambia el saldo declarado. No sumar factura, obligación y movimiento
  como si fueran tres flujos distintos. Usar conciliación para asociar pagos registrados.
- Pronóstico: saldos COP con mismo corte; cobertura confirmada para métodos experimentales.
  Cuantiles y etiquetas de historial no equivalen a precisión o probabilidad demostrada.

## Ensayos especializados

- [Conectividad y recuperación](acceptance/QA_CONNECTIVITY.md).
- [Aceptación ampliada](acceptance/V1_ACCEPTANCE.md).
- [Respaldo manual y restauración aislada](operations/HOSTED_BACKUP.md), sin programación diaria.
- `scripts/measure_hosted_dashboard.py --samples 10`: usa cuenta QA privada en `.local-logs`;
  mide HTTP secuencial caliente, no renderizado ni concurrencia. No imprimir sus credenciales.
- [Investigación](research/README.md): reproducir reportes sin mezclar datos de producción.

Los cortes y comandos anteriores están en [pruebas históricas](archive/2026-10-05/TESTING.md).


## Verificación V1 manual — 16 de octubre de 2026

Rama `codex/v1-manual-transactions`. Ejecutado:

- `python backend/manage.py test backend/tests --noinput`: 222 pruebas, 217 aprobadas, cinco omitidas por requerir PostgreSQL. Ejecución final fuera del sandbox para permitir limpieza de temporales.
- `ruff check backend`, `ruff format --check backend`: aprobados.
- `python backend/manage.py makemigrations --check --dry-run`: sin cambios.
- `npm run build` en frontend: TypeScript y Vite aprobados.
- Inventario API regenerado con `python backend/manage.py export_api_inventory`.

QA de navegador local con empresa sintética separada, corte 2026-10-16 y saldo 500.000 COP:

| Caso | Resultado observado |
|---|---|
| Inicio público y login | Acceso correcto; datos privados disponibles después de iniciar sesión. |
| Ingreso manual 70.000 y egreso 140.000 | Ambos guardados, clasificación automática Ventas/Proveedores, cuenta y origen manual visibles. |
| Actualización | Historial y desglose de categorías actualizados. Se corrigió duplicación de secciones por claves React repetidas. |
| Saldo declarado | Se mantiene en 500.000 COP. |
| Sin confirmación | La predicción solicita siete días completos; no interpreta datos faltantes como cero silenciosamente. |
| Confirmar 2026-10-10 a 2026-10-16 | Entrenamiento siete días y dos movimientos; promedio −10.000 diarios. |
| Horizonte 30/60/90 | Mínimos 200.000 /−100.000 /−400.000 COP. Primer déficit en 60/90: 2026-12-06. |
| Guardar pronóstico | Guardado desde la interfaz. |
| Logout y reingreso | Vuelve a Inicio sin datos financieros; al reingresar persisten ambos movimientos, cobertura y pronóstico guardado. |

Pruebas API complementarias verifican persistencia tras reautenticar, permisos de lector/contador, cuenta ajena/conectada, CSRF, validaciones, reintentos, conflicto de clave, cobertura y obligaciones contadas una sola vez. No se simuló pérdida de respuesta ni corte de red en navegador; la idempotencia sí se comprobó por API. No se ejecutó concurrencia en PostgreSQL ni aceptación en servidor remoto. No equivale a aceptación de instalador o auditoría completa de accesibilidad.

Preparar una empresa nueva por ensayo con [guion reproducible](PLAN_DEMO_FUNCIONAL.md). Para arrancar: migrar backend, construir frontend y ejecutar `python backend/manage.py runserver 127.0.0.1:8000`. Abrir el origen local; no cargar `.env.hosted` para pruebas locales.
