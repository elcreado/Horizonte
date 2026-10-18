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


## Actualización: secciones y captura diaria

- Backend: 224 pruebas, 219 aprobadas y cinco omitidas en SQLite por requerir PostgreSQL. Ruff y build TypeScript/Vite aprobados.
- Navegador: navegación por las diez secciones de la barra lateral con título y contenido independientes. Movimientos no muestra Facturas ni otras herramientas ajenas.
- La fecha del formulario se observa como 2026-10-16 (hoy en Colombia). Se guardó también una operación del 2026-10-15 y la fecha volvió a hoy tras confirmar el guardado.
- Se guardaron dos operaciones nuevas con igual fecha, descripción e importe; ambas aparecen como movimientos separados. No se duplicaron secciones al refrescar.
- API: fecha omitida usa hoy; un corte anterior no bloquea el registro; el saldo declarado permanece igual. El futuro se rechaza.
- API: un ingreso de 140 trece días antes del corte y un egreso de 70 al corte producen promedio diario de 5 en catorce días. Una operación posterior al corte queda fuera; confirmar solo siete días devuelve cobertura insuficiente.
- Los enlaces de navegación usan hash y permiten acceso directo. No se certificó una revisión visual móvil completa.


## Resumen, pagos mensuales y cola local

Suite completa: 231 pruebas, 226 aprobadas y cinco omitidas por requerir PostgreSQL. Ejecución fuera del sandbox para permitir temporales. Build React/TypeScript y Ruff aprobados.

Pruebas nuevas cubren: movimiento manual modifica gráfica sin volver a sumar saldo al corte; movimiento posterior actualiza caja una vez; alerta guardada coincide con Resumen; programación mensual idempotente y reflejada en calendario/proyección; cancelación; día 31 y febrero bisiesto; permisos; archivo de ejemplo procesado por worker real y reimportación sin duplicados, continuidad de mensualidades después de años sin consultar; arranque/cierre del worker junto a runserver.

Navegador local, empresa sintética aislada con 500.000 COP: añadir ingreso 70.000 produjo pendiente positiva (+10.000 diarios) en el resumen; programar «Sueldos» 100.000 para el día 1 creó vencimientos mensuales a partir del próximo mes. Descarga/subida del ejemplo revisada con la propia interfaz: completó con dos movimientos nuevos y cero duplicados, usando el worker iniciado automáticamente por runserver. El resumen cambió tras la carga. La segunda subida del mismo archivo terminó con cero movimientos nuevos y dos duplicados omitidos. No se ha desplegado esta rama en el alojamiento remoto.


## Corte de orquestación y demo repetible — 18 de octubre de 2026

- OpenCode: simulación aprobada; dos workers documentales, cada uno con un archivo exacto de salida, en worktrees aislados y con terminal/subagentes/rutas externas denegados. Codex revisó stdout/stderr, archivos y cada diff. Corrigió una frase sobre saldo posterior al corte y la etiqueta de Predicciones antes de aplicar parches comprobados. No se tomaron reportes de workers como evidencia de pruebas.
- Nuevo `prepare_web_demo`: pruebas de dry-run sin escrituras, bloqueo fuera de SQLite/desarrollo, usuario inexistente/inactivo, corte futuro, preparación repetida que conserva datos/contraseña, cifras esperadas y rollback ante error. El usuario inactivo se valida por la consulta de alta; no se añade autenticación ni cuentas nuevas.
- Nuevo test de concurrencia PostgreSQL: dos miembros distintos envían el mismo UUID; verifica 201/200, mismo ID, una transacción, un recibo, una auditoría y saldo inalterado. Se omite con SQLite; falta ejecución real con PostgreSQL.
- Suite completa: **235 pruebas, 229 aprobadas y seis omitidas**. Ruff check/format, `makemigrations --check --dry-run` y build frontend aprobados.
- Ensayo local del comando precedido de `--dry-run`, con corte 2026-10-18 y dos empresas nuevas en una cuenta sintética ya existente; no se resembraron empresas anteriores. En navegador, empresa Obligaciones: mínimo −81.000 COP. Empresa Historial manual: siete días completos y dos movimientos; 30/60/90 muestran 200.000/−100.000/−400.000 COP y déficit desde corte+51.
- No se ejecutaron fallos de red, auditoría completa de teclado/accesibilidad, aceptación remota ni despliegue en este corte. Esa evidencia sigue pendiente y se mantiene separada del ensayo local.
