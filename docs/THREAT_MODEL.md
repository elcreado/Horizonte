# Modelo de amenazas del primer entregable

Fecha: 5 de octubre de 2026. Revisión del código actual; no constituye auditoría ASVS,
pentest ni certificación. Entorno objetivo: React/Django en un origen HTTPS, PostgreSQL
Supabase en esquema privado, cola en BD y cliente Electron Windows. Usar solo datos sintéticos
hasta completar las validaciones externas y la política de tratamiento de datos.

## Activos y fronteras de confianza

- Datos financieros y membresías de empresa: únicamente Django decide qué usuario puede acceder.
- Contraseñas y sesiones: hashes Argon2; sesiones en BD y cookies HttpOnly. No hay tokens
  financieros en localStorage ni credenciales PostgreSQL en el cliente.
- Archivos importados: entrada no confiable, temporalmente persistida para procesamiento.
- Trabajos de cola y sus argumentos: datos privados que deben consumirse y borrarse al terminar.
- Pronósticos guardados: entradas y resultados históricos de cada empresa; requieren aislamiento.
- Claves de Django, BD y correo: solo variables del servidor. No son parte del build React/Electron.
- Equipo del usuario ↔ servidor: HTTPS y cookies/CSRF. El servidor remoto entrega código web al
  escritorio; comprometer el servidor compromete la interfaz financiera que ve el usuario.
- Django ↔ Supabase/correo: proveedores externos con sus propios controles y retención.
- UI remota ↔ Electron: renderer sin Node ni preload; formulario local con IPC limitado y validado.
- Repositorio/build ↔ instalador: dependencias y proceso de distribución son parte de la confianza.

## Amenazas, controles y evidencia pendiente

| Amenaza | Control observado | Límite o comprobación pendiente |
|---|---|---|
| Acceso a otra empresa manipulando IDs | Membresía desde sesión; consultas por empresa; roles; matriz transversal de 25 GET y 26 escrituras rechaza empresa ajena/sesión ausente; saldo/cobertura/nombre autorizan antes de validar | Ampliar objetos ajenos existentes, cuerpos válidos, todos los roles y recorrido remoto; matriz con IDs de prueba y cuerpo vacío no cubre todo IDOR |
| Operación en cola tras revocar permiso | Tareas financieras revalidan rol/consentimiento; creación atómica en modo BD | Ensayo de revocación durante ejecución y cortes reales de procesos |
| CSRF incluido login/recuperación | Protección explícita en endpoints públicos mutantes; sesión DRF en financieros | Validación de Origin/cookies en el proxy y dominio definitivos |
| Robo de credenciales o sesión en tránsito | HTTPS exigido en escritorio empaquetado; cookies Secure en producción; proxy configurado | TLS real y comportamiento de redirects todavía sin comprobar |
| XSS y abuso de navegador | Escape React; CSP self para scripts, restricciones de objetos/frames y navegación | No se ha completado corpus XSS, QA ni auditoría CSP; estilos inline permitidos |
| Ejecución local desde contenido remoto | Electron sandbox, contextIsolation, Node desactivado, permisos/popups denegados | Smoke aislado de configuración comprobado; flujo remoto y actualizaciones pendientes |
| Cambio a servidor malicioso | Origen HTTPS sin credenciales/rutas/query; detiene página anterior y borra almacenamiento/caché incluso sin ventana; regresión de cookie sintética pasa empaquetada | HTTPS no demuestra legitimidad; usar URL publicada. Borrar cookies locales no revoca sesión del servidor |
| Exposición accidental de BD | Esquema `horizonte` y acceso mediante Django; sin claves Supabase del cliente | Verificar esquemas expuestos/permisos en la cuenta real; aún sin credenciales |
| Persistencia efímera por mala configuración | Producción rechaza fallback SQLite y clave local; Render y Supabase desplegados, migraciones y recorridos HTTP comprobados | Ensayar cortes de procesos y migraciones de actualización; falta recorrido visual completo del cliente instalado |
| Fuerza bruta y abuso de correo | Login 10/min por IP anónima o usuario autenticado; recuperación/reset 5/h con contadores persistentes en BD y ventanas fijas; respuesta genérica | Bloqueo transaccional PostgreSQL implementado; concurrencia real y confianza en cabeceras IP del proxy pendientes. Ventanas fijas permiten ráfagas cerca de su renovación. La limitación no garantiza bloqueo global por cuenta objetivo |
| Reutilizar enlace de recuperación | Token Django, vencimiento 1 h, invalida tras cambio de contraseña; bloqueo de usuario al reset | Entrega real y sesión remota tras reset no comprobadas; revisar filtración en logs/historial |
| Lectura de enlace/secretos en errores de correo | Backend HTTPS sanitiza errores; no devuelve respuesta del proveedor ni enlace privado | Proveedor y cliente de correo pueden conservar contenido; no afirmar cifrado extremo a extremo |
| Archivo malicioso o demasiado grande | Límites 2 MB/10.000 filas, UTF-8, validación y rechazo de fórmulas XLSX; parsers restringidos | Ampliar corpus XML/XLSX adversarial y límites de tiempo/memoria bajo carga |
| Duplicación de dinero por reintentos | IDs estables y restricciones BD, transacciones, tareas idempotentes, vínculos de recurrencia | Probar interrupciones reales PostgreSQL; una entrega de correo puede duplicarse |
| Trabajo perdido o bloqueado tras suspensión | Trabajo/mensaje atómicos, lease 15 min, tres intentos, cierre terminal y borrado de payload | No hay procesamiento mientras Render duerme; health no comprueba worker |
| Borrado o pérdida de datos | Respaldo manual de Supabase y restore aislado nativo PostgreSQL comprobados sin Docker, incluyendo Client Django | Copia local sin cifrar autorizada; retención/cifrado/copia externa pendientes. Respaldo diario excluido por usuario |
| Filtración por logs/backups/auditoría | Secretos excluidos de Git; contenido eliminado de importaciones terminadas | Controlar acceso, retención, copias y redacción transversal; auditoría financiera no cubre todos los accesos |
| Manipulación o falsa interpretación de pronóstico | Evidencia/digest, ejecuciones inmutables, labels experimentales, separación puntual/P50 | Datos falsos de entrada no se detectan automáticamente; cobertura sintética inferior a nominal, no calibrada |
| Dependencia comprometida o instalador sustituido | Locks de dependencias, pruebas/build y versiones explícitas | Firma de instalador, distribución verificable, revisión de dependencias y actualizaciones pendientes |
| Denegación de servicio/cuotas gratuitas | Límites de cargas y fallos explícitos | Sin garantía 99 %, carga/p95 ni protección antiabuso integral; no cron de keepalive configurado |

## Decisiones actuales

- Presupuesto 0 USD: aceptar suspensión y límites de proveedor, sin afirmar disponibilidad alta.
- El cliente es en línea: evita Docker en el equipo de prueba, pero necesita un servidor operativo.
- No guardar tokens bancarios reales; Mock Bank únicamente simula consentimiento y movimientos.
- El instalador es unsigned y no ofrece actualización automática. No desactivar protecciones del
  sistema como requisito de prueba; revisar distribución antes de entregar a terceros.
- Los cuantiles son experimentales condicionados a compromisos puntuales. La banda diaria no
  representa probabilidad de déficit ni cobertura conjunta de toda la trayectoria.

## Pasos pendientes para revisar antes de cierre

- Completar revisión de permisos/esquema de las cuentas Free ya desplegadas y recuperación con correo real; TLS, cookies y CSRF tienen evidencia HTTP, no aceptación visual completa.
- Validar concurrencia de límites persistentes y configuración de IP detrás del proxy; ampliar límites globales por cuenta objetivo.
- Ejecutar corpus adversarial de archivos y pruebas de carga con límites de recursos definidos.
- Ensayar caída/reanudación de web y cola, y restauración remota aislada con evidencia de integridad.
- Ejecutar revisión de dependencias y verificar instalador en Windows limpio, distribución y firma.
- Completar matriz ASVS según versión y nivel acordados, sin presentar este documento como cumplimiento.
- Revisar protección de datos, consentimiento, retención y autorizaciones antes de usar empresas reales.

Evidencia disponible: pruebas en `backend/tests`, contrato de origen en `desktop/tests`, smoke
de configuración en `.local-logs/desktop-smoke`, estado en `IMPLEMENTATION_STATUS.md` y reportes
sintéticos de investigación. Una prueba unitaria o build aprobado no demuestra el despliegue remoto.
