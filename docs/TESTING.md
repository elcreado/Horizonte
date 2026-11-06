# Pruebas y arranque vigentes

Revisión: **18 de octubre de 2026**. Guía vigente de pruebas y arranque. El veredicto
autoritativo de implementación y verificación está en
[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md); la matriz de requisitos en
[ESTADO_Y_PENDIENTES.md](ESTADO_Y_PENDIENTES.md). Las narrativas de ejecución anteriores
se conservan en el [archivo del 18 de octubre](archive/2026-10-18/TESTING.md). Las cifras
de prueba citadas abajo son evidencia previa, no una ejecución nueva de esta guía.

## Pruebas locales con Docker (flujo principal)

Requiere Docker Desktop iniciado con contenedores Linux y Docker Compose. Desde CMD,
en la raíz del proyecto:

```bat
docker compose config --quiet
docker compose up --build -d --wait
docker compose ps -a
```

Abrir http://127.0.0.1:5173. Compose inicia PostgreSQL, Redis, migraciones,
Django, el worker Celery de importaciones y Vite. `migrate` termina con código 0;
los demás servicios permanecen activos. No requiere Python/Node en el host.

```bat
docker compose logs -f backend worker frontend
docker compose exec backend python backend/manage.py check
docker compose exec backend python backend/manage.py makemigrations --check --dry-run
docker compose exec backend ruff check backend
docker compose exec backend ruff format --check backend
docker compose exec backend python backend/manage.py test backend/tests --noinput
docker compose exec frontend npm run build
```

La suite crea y elimina exclusivamente `test_liquidity` en el PostgreSQL local.
No cambiar las variables para apuntar a servicios alojados. Los datos de la app
permanecen en `postgres_data`; `docker compose stop` los conserva y
`docker compose down` también conserva el volumen. No usar `down -v`.
La base previa `backend/db.sqlite3` se conserva separada: no se importa automáticamente.
Usar un usuario/empresa de pruebas de esta base PostgreSQL desde la interfaz.

Repetir `docker compose up --build -d --wait` después de modificar código o dependencias.
Los scripts `start-dev.ps1`, `start-backend.ps1` y `start-worker.ps1` usan Compose;
no abren procesos Python/Node del host. El instalador remoto sigue siendo otro entorno.

## Verificación Docker local — 18 de octubre de 2026

Evidencia previa (no una ejecución nueva de esta guía); el estado autoritativo vigente
está en [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md).

Flujo principal: `docker compose up --build -d --wait`. PostgreSQL, Redis, backend,
worker Celery y frontend activos; migraciones finalizadas con código 0. API directa
y vía Vite responden; Celery responde a `inspect ping`. Se conserva `postgres_data`.

Suite PostgreSQL ejecutada: **235 pruebas, 233 aprobadas y 2 omitidas** (preparación
de demo exclusiva de SQLite). Incluye concurrencia de solicitudes con el mismo UUID.
Ruff check y formato: 208 archivos; migraciones sin cambios; frontend compilado.
La primera pasada detectó fixtures/configuración ausentes en el contenedor y dos
supuestos de entorno en pruebas; se corrigieron y se repitió la suite completa.
No se ha desplegado este corte ni se certifica aceptación visual completa.

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

## Desarrollador: verificaciones locales

Verificaciones opcionales en el host, separadas del flujo Docker principal.
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

## Usuario final: escritorio sin Docker

Escenario alojado histórico/secundario; el flujo principal de verificación es Docker.

- Instalar `desktop/release/session-isolation/Horizonte Setup 0.1.0.exe` en Windows x64.
- Conectar con `https://horizonte-demo.onrender.com`; necesita internet y puede tardar al despertar.
- Inicio no exige sesión. Registrarse/acceder y seguir el [manual](USER_MANUAL.md).
- Usar el [recorrido de aceptación](acceptance/DESKTOP_ACCEPTANCE.md) para comparar importes.
- No arrancar Docker, Redis, Django ni Vite para consumir la aplicación alojada.
- Correo real no verificado: para probar recuperación se necesita proveedor/remitente/buzón;
  para los demás flujos no hacen falta credenciales bancarias reales ni servicios de pago.

## Ensayos especializados

- [Conectividad y recuperación](acceptance/QA_CONNECTIVITY.md).
- [Aceptación ampliada](acceptance/V1_ACCEPTANCE.md).
- [Respaldo manual y restauración aislada](operations/HOSTED_BACKUP.md), sin programación diaria.
- `scripts/measure_hosted_dashboard.py --samples 10`: usa cuenta QA privada en `.local-logs`;
  mide HTTP secuencial caliente, no renderizado ni concurrencia. No imprimir sus credenciales.
- [Investigación](research/README.md): reproducir reportes sin mezclar datos de producción.

Los cortes y comandos anteriores están en el [archivo del 18 de octubre](archive/2026-10-18/TESTING.md)
y en las [pruebas históricas](archive/2026-10-05/TESTING.md).

## Verificación V1 manual — 16 de octubre de 2026

Narrativa histórica conservada en el [archivo del 18 de octubre](archive/2026-10-18/TESTING.md).

## Actualización: secciones y captura diaria

Narrativa histórica conservada en el [archivo del 18 de octubre](archive/2026-10-18/TESTING.md).

## Resumen, pagos mensuales y cola local

Narrativa histórica conservada en el [archivo del 18 de octubre](archive/2026-10-18/TESTING.md).

## Corte de orquestación y demo repetible — 18 de octubre de 2026

Narrativa histórica conservada en el [archivo del 18 de octubre](archive/2026-10-18/TESTING.md).

## Regresión de mensualidades y QA web

Con Node 24 en el contenedor:

```bat
docker compose exec frontend npm test
```

Cuatro casos verifican conservar payload/UUID tras respuesta incierta o 503, liberar
el intento tras validación 400 y permitir altas intencionales independientes.
[Guion web y evidencia local](acceptance/WEB_V1_QA.md). No confundir el corte de conexión
antes del POST con una respuesta perdida después de confirmar la escritura.

## Pruebas de saldo histórico (30 de octubre de 2026)

Regresión focalizada:

```bat
docker compose exec backend python backend/manage.py test tests.test_balance_history tests.test_api_inventory --noinput
docker compose exec frontend npm test
```

Suite completa PostgreSQL: 247 pruebas, 245 aprobadas y 2 omitidas; SQLite: 240 aprobadas y 7
omitidas de 247. Las exclusiones de SQLite incluyen bloqueos concurrentes y persistencia de
Decimal extremo; el cálculo puro Decimal también se comprueba allí. Ver [resultados y casos](acceptance/BALANCE_HISTORY_QA.md).
La primera pasada SQLite restringida encontró permisos de temporales y su limitación de
persistencia extrema; la repetición autorizada pasó con exclusiones explícitas, sin ocultar fallos.

## Selección de empresa (4 de noviembre de 2026)

`docker compose exec frontend npm test` ejecuta 13 casos, incluidos cinco de preferencias:
usuario distinto, empresa no autorizada, JSON inválido, storage denegado y limpieza.
`docker compose exec frontend npm run build` comprueba TypeScript y Vite (653 módulos).
La [guía de selección](acceptance/COMPANY_SELECTION_QA.md) distingue resultados Node,
fixture de hook y web integrada. El fixture de desarrollo se sirve en
`http://localhost:5173/tests/companySelection.html`; no forma parte del build de la app.
Suite PostgreSQL repetida: 245 aprobadas y 2 omitidas de 247; no hubo cambios backend.
