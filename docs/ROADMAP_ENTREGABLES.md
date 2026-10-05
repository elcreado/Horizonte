# Hoja de ruta de entregables de Horizonte

**Corte de análisis:** 5 de octubre de 2026. **Fuente de verdad:** código actual, `README.md`, `SPECS.md`, `docs/IMPLEMENTATION_STATUS.md`, `docs/FORECAST_BASELINES.md` y pruebas ejecutadas. Este documento distingue una aplicación que ya funciona en desarrollo de una versión funcional distribuible y del alcance completo de investigación descrito en las especificaciones.

## Estado actual comprobado

**Estado vigente del 5 de octubre:** Render Free y Supabase están conectados y operativos.
CI del calendario `37379774142` terminó correctamente; commit `67d2350` desplegado,
Inicio y salud HTTP 200 y bundle actualizado comprobado. Suite local: 197 pruebas,
192 aprobadas y 5 omitidas; CI PostgreSQL aprobada. Instalador vigente:
`desktop/release/session-isolation/Horizonte Setup 0.1.0.exe`, con URL remota precargada.
El usuario final necesita Windows e internet, sin Docker/Python/Node/PostgreSQL local.
Instalación/desinstalación limpia y QA visual siguen pendientes. Respaldo manual y
restauración estructural/Client Django verificados; respaldo diario rechazado por el usuario.
Correo real pendiente de configuración. Véase [aceptación V1](V1_ACCEPTANCE.md).

### Corte histórico inicial (no describe la versión vigente)

- [x] Inicio público sin sesión; registro, acceso/cierre de sesión, recuperación local de contraseña y gestión básica de cuenta, empresas y roles.
- [x] Django/DRF, React/Vite, PostgreSQL/Redis y worker Celery en el arranque local. Las rutas de la interfaz consumen `/api` mediante el proxy de Vite en desarrollo.
- [x] Importación CSV/XLSX, XML de factura, cuentas y fuente Mock Bank con consentimiento de prueba, sincronización asíncrona y revocación.
- [x] Movimientos, clasificación por reglas con corrección, normalización parcial y comercios con etiqueta explícita; obligaciones, conciliación, recurrencias y auditoría de las acciones instrumentadas.
- [x] Dashboard con saldo, flujos conocidos, histórico, umbral y alertas determinísticas; referencia experimental Naive/Seasonal Naive/SES separada del escenario principal y ejecuciones guardadas.
- [x] Verificación en este corte: 112 pruebas Django aprobadas con SQLite (2 omitidas), Ruff lint/formato y build Vite aprobados. El build avisa de un bloque JavaScript de 633,65 kB. Esto no verifica por sí solo PostgreSQL, navegador ni instalador.
- [ ] No hay evidencia de exactitud predictiva en datos representativos ni de P10/P50/P90 calibrados, conexión bancaria externa, empaquetado de aplicación, despliegue de producción o prueba de recuperación con correo SMTP real.

**Inconsistencia documental:** `docs/TESTING.md` contiene apartados históricos que todavía llaman “pendiente” a funciones ya implementadas. `docs/IMPLEMENTATION_STATUS.md` es la matriz más reciente, aunque acumula notas de cortes sucesivos. Antes de presentar el entregable hay que dejar una guía vigente única. El árbol ilustrativo de `README.md` también describe directorios objetivo (`workers/`, `ml/`, `deploy/`) que aún no existen como tales.

## Primer entregable: versión funcional

**Meta propuesta:** una persona puede instalar o abrir la aplicación en un entorno de prueba, crear su empresa, cargar movimientos y facturas sintéticas, revisar obligaciones y recibir un pronóstico 30/60/90 días con límites y riesgo explicados. El sistema conserva datos, separa empresas y se puede recuperar ante fallos. Se demostrará con datos sintéticos; un banco real no debe convertirse en dependencia para mostrar el flujo principal.

Los pasos están en orden de dependencia. Cada uno termina con una evidencia de aceptación.

1. **Congelar el alcance y la documentación de la versión.**
   - [ ] Decidir y registrar si “versión funcional” exige todo el MVP de `README.md`/`SPECS.md` o un primer corte con Mock Bank + importaciones. La recomendación es cerrar ese primer corte sin prometer integración bancaria real, pero **no** marcar el MVP académico completo como terminado.
   - [ ] Actualizar la matriz RF/RNF con tres estados consistentes: terminado, parcial y pendiente; corregir los apartados históricos de `TESTING.md` y el árbol objetivo del README.
   - **Aceptación:** una lista de funciones y exclusiones coincide con la interfaz, API y pruebas; ningún escenario experimental se presenta como probabilidad validada.

2. **Cerrar el recorrido de datos de extremo a extremo.**
   - [ ] Probar en PostgreSQL + Redis + Celery reales: registro → empresa → Mock Bank/CSV/XLSX → XML → conciliación/obligaciones → clasificación → dashboard, incluido reintento, revocación y recuperación de jobs interrumpidos.
   - [ ] Ampliar corpus de XML UBL y de extractos bancarios; resolver casos ambiguos de comercio y validar que facturas, recurrencias y movimientos conciliados no dupliquen caja futura.
   - [ ] Medir importación completa de 10.000 filas por HTTP/cola/BD, no solo el parser; documentar tiempo, hardware y errores.
   - **Aceptación:** datos y saldos reproducibles tras reinicio, sin duplicados ni flujos contados dos veces; 10.000 filas cumplen el umbral de rendimiento que se fije.

3. **Completar el motor de proyección que promete la especificación.**
   - [ ] Crear dataset sintético representativo de 100 empresas × 24 meses con patrones, faltantes y episodios de déficit; versionar generador, semilla y particiones.
   - [ ] Preparar cortes históricos sin fuga temporal: obligaciones, conciliaciones y etiquetas deben reflejar lo conocido en cada fecha de evaluación.
   - [ ] Comparar Naive/Seasonal Naive/SES con modelos más avanzados justificados; aplicar rolling-origin a 30/60/90 días y medir error de flujo, saldo y fecha de déficit.
   - [ ] Incorporar al escenario principal un método seleccionado con fallback para historial insuficiente. Calibrar P10/P50/P90 y comprobar cobertura de intervalos antes de publicarlos.
   - [ ] Generar alertas explicables desde el pronóstico, con período, mínimo, factores y regla de riesgo; automatizar evaluación cuando cambien los datos relevantes.
   - **Aceptación:** informe reproducible de MAE/RMSE/sMAPE, pinball/cobertura y precisión/recall/F1 de déficit; la UI distingue valor observado, estimación y rango; los datos insuficientes no muestran falsa precisión.

4. **Asegurar las operaciones y la experiencia de usuario.**
   - [ ] Completar auditoría transversal de accesos y conexiones, controles de tasa, CSP, validaciones de entrada y pruebas IDOR/CSRF/XSS; definir threat model. Conservar el aislamiento por empresa en cada nueva API.
   - [ ] Revisar con teclado y tamaños móviles Inicio, registro, acceso, importaciones, obligaciones, dashboard y errores/vacíos; dividir el bundle si perjudica la carga.
   - [ ] Probar recuperación por un SMTP de pruebas y configurar secretos, HTTPS y cookies seguras para cualquier entorno remoto. Mantener solo datos sintéticos hasta completar protección y autorización de datos reales.
   - **Aceptación:** checklist de seguridad y accesibilidad firmado con resultados; ninguna acción financiera queda disponible a otro tenant o rol.

5. **Hacer reproducible la entrega y su operación.**
   - [ ] Crear imágenes/versiones de backend, frontend y worker y un Compose de aplicación completo, o documentar expresamente la instalación manual elegida; agregar migraciones, health checks y configuración de arranque.
   - [ ] Ejecutar CI sobre PostgreSQL además de SQLite, incluyendo migraciones, pruebas backend, lint/formato y build frontend; añadir una prueba de aceptación de navegador para el flujo principal.
   - [ ] Completar la política de respaldo manual y recuperación, con retención, cifrado y comprobación de fallos; medir p95 del dashboard y carga con workers. El respaldo y la restauración local ya se ensayaron. No se programarán respaldos diarios, por decisión del usuario.
   - [ ] Preparar manual de usuario, manual técnico, contrato OpenAPI y guía corta de prueba con credenciales de demo creadas localmente.
   - **Aceptación:** desde un equipo limpio se sigue una única guía y se completa el flujo de demostración sin editar código; una restauración documentada recupera los datos de prueba.

**Puerta de salida:** la versión solo se etiqueta “funcional” cuando pasan los pasos 2, 4 y 5 y se decide explícitamente el nivel de pronóstico del paso 3. Si el modelo híbrido probabilístico y sus experimentos son parte obligatoria del *primer entregable académico*, el paso 3 completo también es bloqueante. Una demo determinística o una referencia experimental son funcionales como software, pero no satisfacen por sí solas todos los objetivos predictivos de `README.md` y `SPECS.md`.

## Aplicación de escritorio: viabilidad

**Sí es viable**, porque la interfaz ya es React y el backend expone HTTP; hoy **no** basta con compilar Vite o poner la página en una ventana. El frontend usa rutas `/api`, sesiones/cookies y CSRF, y el sistema requiere Django, base de datos, Redis y Celery para importaciones y sincronización. `compose.yaml` solo inicia PostgreSQL y Redis; `start-dev.ps1` levanta procesos de desarrollo. Ninguno es un instalador de escritorio.

- **Opción recomendada para un primer instalador:** empaquetar la interfaz en una ventana Tauri o Electron y mantener Django, PostgreSQL, Redis y Celery en un servidor de prueba seguro. Así el usuario final instala una app de escritorio que sigue funcional en línea, sin Docker local. Hay que introducir una URL de API configurable, decidir un origen estable para cookies/CSRF, HTTPS, inicio/cierre de sesión y actualización del instalador. El modo sin conexión no estaría disponible.
- **Opción sin servidor y sin Docker:** empaquetar Django/Python como proceso auxiliar, sustituir o integrar las dependencias PostgreSQL/Redis/Celery de manera soportada, iniciar y detener procesos con seguridad, migrar la BD, guardar datos en una ruta de usuario, hacer backups y gestionar puertos/local-only. Requiere pruebas de importaciones, concurrencia y actualización del esquema. Es un proyecto aparte y no está listo hoy.
- **Elección implementada para el primer instalador:** Electron con NSIS para Windows x64 y servidor remoto HTTPS. Existe `desktop/release/hosted/Horizonte Setup 0.1.0.exe` (sin firma). La prueba automatizada verifica restricciones del cliente y permisos en la configuración local; faltan instalación/desinstalación en Windows limpio y el recorrido autenticado remoto. Tauri queda como alternativa futura; no es el cliente actual.
- **Prueba de viabilidad antes de prometer entrega:** crear un prototipo Windows que abre Inicio sin sesión, inicia sesión contra API de prueba, sube un CSV, espera el job y muestra dashboard; cerrarlo y abrirlo otra vez sin pérdida de sesión indebida. Después probar instalación, actualización y desinstalación en una máquina limpia. Solo entonces decidir soporte Windows; macOS/Linux requieren builds y QA propios.

Referencias del empaquetado: [Tauri sidecars](https://v2.tauri.app/develop/sidecar/), [requisitos Windows de Tauri](https://v2.tauri.app/start/prerequisites/), [distribución de Electron](https://www.electronjs.org/docs/latest/tutorial/distribution-overview/) y [seguridad de Electron](https://www.electronjs.org/docs/latest/tutorial/security/).

## Segunda versión: metas posteriores al primer entregable

- [ ] **Port móvil Android e iOS.** Extraer la configuración de API y sesión del origen de Vite, adaptar navegación, gráficos, formularios y carga de archivos a pantallas pequeñas, y probar autenticación/cookies/CSRF dentro de WebView. Evaluar Capacitor para reutilizar React y compartir el backend remoto; Android requiere Android Studio/SDK e iOS un entorno macOS/Xcode para compilación y pruebas. Publicar en tiendas solo después de QA en dispositivos reales. La aplicación móvil consumiría la API; no ejecutaría Django/Celery dentro del teléfono.
- [ ] **Integración financiera real en entorno autorizado.** Elegir proveedor tras comprobar cobertura colombiana, contrato, sandbox, costos y consentimiento. Implementar OAuth/OIDC + PKCE según el proveedor, sincronización incremental, revocación, cifrado de tokens y contratos de fallo/reintento.
- [ ] **Facturación y datos de mayor cobertura.** Integrar API de facturación si aporta valor frente a XML y ampliar validación de estados de pago, conciliación y corpus de documentos.
- [ ] **Mejora continua del modelo.** Evaluar ARIMA/SARIMA/Prophet u otros modelos solo si superan baselines bajo rolling-origin; calibrar por segmentos, supervisar deriva y volver a entrenar sin mezclar empresas ni filtrar futuro.
- [ ] **Producto y operación.** Notificaciones opt-in, invitaciones a miembros, observabilidad, soporte, actualizaciones del cliente de escritorio y métricas de uso; investigación de usabilidad con microempresas autorizadas.

La exclusión de “aplicación móvil nativa” en `README.md`/`SPECS.md` sigue siendo correcta para el alcance inicial; al aprobar la segunda versión deberá actualizarse para distinguir el port móvil planificado del primer entregable.

## Acciones externas para probar o distribuir

- **Prueba del usuario con el instalador:** Windows x64 e internet; conectar a `https://horizonte-demo.onrender.com`. No necesita Docker ni herramientas de desarrollo. Render Free puede suspenderse y tardar al reactivarse.
- **Desarrollo local opcional:** abrir Docker Desktop y ejecutar `scripts/start-dev.ps1`; no hacen falta cuenta bancaria ni credenciales externas para Mock Bank. Sí requiere Python/Node y dependencias; no es un requisito para probar el instalador.
- **Prueba de correo real en Render Free:** configurar Resend mediante API HTTPS y un remitente permitido; los puertos SMTP habituales están bloqueados. Sin estas credenciales solo se verifica la recuperación con correo simulado. Véase `HOSTING_FREE.md`.
- **Prueba de banco real o sandbox:** crear cuenta de desarrollador y conceder acceso del proveedor elegido; el proyecto no puede inventar esas credenciales.
- **Escritorio en línea:** disponer de servidor HTTPS accesible para el instalador y un equipo Windows limpio para ensayo. **Escritorio sin conexión:** requiere el trabajo adicional descrito arriba, no solo Docker Desktop.
- **Port móvil V2:** Android Studio/SDK y dispositivo o emulador Android; para compilar/probar iOS, macOS con Xcode y dispositivo/simulador. Se necesitará un backend remoto HTTPS para que la app móvil sea funcional.

La [documentación de Capacitor](https://capacitorjs.com/docs) confirma su uso con proyectos web existentes y sus [requisitos de entorno](https://capacitorjs.com/docs/getting-started/environment-setup) para Android/iOS.
