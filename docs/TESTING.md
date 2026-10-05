# Arranque y pruebas

## Pronóstico híbrido con recurrencias (corte vigente)

En «Pronóstico híbrido experimental», el método «Patrón semanal y recurrencias confirmadas» estima
las fechas futuras de patrones confirmados vigentes. Requiere cobertura del historial. Revisa primero
Recurrencias: una confirmación antigua ya no sirve si cambió la evidencia. La tabla separa obligaciones,
recurrencias estimadas y flujo variable; consultar o guardar no crea obligaciones ni cambia saldo.
Si hay una obligación sin vínculo de igual fecha/sentido, el cálculo pide revisarla. Una obligación
vinculada parcialmente pagada aporta solo su pendiente; cancelada o saldada no se estima otra vez.
El escenario principal de obligaciones conserva su contrato; estos métodos siguen experimentales.
No requieren credenciales externas para el cálculo local. 123 pruebas SQLite ejecutadas (2 omitidas)
y build aprobados; el entorno remoto y la revisión visual completa siguen pendientes.

## Estado actual de la demo local (octubre de 2026)

Con Docker Desktop abierto, ejecuta `./scripts/start-dev.ps1` desde la raíz. El script deja
PostgreSQL, Redis, backend, worker Celery y frontend activos. Abre
`http://127.0.0.1:5173/#/dashboard` e inicia sesión. Para probar Mock Bank no necesitas una
cuenta bancaria, credenciales ni acciones externas adicionales: en «Fuente bancaria de prueba»
marca la autorización local y pulsa «Conectar Mock Bank». La carga de 120 movimientos sintéticos
se procesa en segundo plano; la tabla muestra su estado. Puedes sincronizar de nuevo (sin duplicar
movimientos) y revocar el acceso. Tras revocarlo, el historial permanece; puedes autorizar una
reconexión que reutiliza la misma cuenta y no duplica su saldo. Si Docker/Redis o el worker no están activos, la
sincronización no se completa; vuelve a ejecutar `start-dev.ps1`.

Las secciones históricas de este archivo documentan cortes anteriores. El estado funcional vigente
está en [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md).

## Respaldo local y ensayo de recuperación

`scripts/db-backup.py --restore-check` guarda un archivo PostgreSQL binario y un manifiesto con
SHA-256 en `.local-backups/`, carpeta ignorada por Git. La comprobación crea una base temporal,
restaura el archivo, consulta migraciones/empresas/movimientos y elimina esa base temporal. **Nunca
sobrescribe `liquidity`**. El 2 de octubre se verificó la restauración de 34 migraciones, 2 empresas
y 65 movimientos. El script se puede ejecutar manualmente:

```powershell
.\.venv\Scripts\python.exe scripts\db-backup.py --restore-check
```

En este equipo quedó registrada la tarea de Windows `Horizonte Local Backup`, diaria a las 02:00,
mediante `scripts/register-backup-task.ps1`. Se ejecutó manualmente desde el Programador de tareas
y terminó con código 0; la próxima ejecución queda programada. Si cambias la hora o reinstalas el
proyecto, vuelve a ejecutar el script de registro. La tarea requiere una sesión de Windows abierta,
Docker Desktop en marcha y espacio disponible. Puedes consultar su último resultado con
`Get-ScheduledTaskInfo -TaskName 'Horizonte Local Backup'`.

Estos respaldos permanecen **en el mismo equipo y sin cifrado**; utiliza solo datos sintéticos o de
desarrollo. Para datos reales faltan almacenamiento externo cifrado, política de retención,
supervisión de fallos y un procedimiento de recuperación de producción probado.

## Comercios identificados

En el dashboard, «Comercios identificados» agrupa los movimientos cuya descripción contiene
una etiqueta explícita como `Comercio: Café 24`. CSV/XLSX y fuentes conectadas usan alias propios
por empresa y proveedor. El texto original y la etiqueta extraída permanecen en el movimiento.
Para probarlo sin datos externos, importa un CSV con la columna `description` que incluya esa
etiqueta; después pulsa «Actualizar» en la lista de comercios. Las descripciones ambiguas no se
asignan automáticamente.

## Qué debes hacer fuera de la aplicación

**Demo local: no requiere registro bancario, API keys, suscripciones, SMTP, Redis ni Docker.**
Necesitas Python 3.13 y Node.js 24 con npm; ambos se detectaron en este equipo. La primera instalación
necesita internet para descargar dependencias. Debes elegir una contraseña local y abrir dos terminales.
SQLite es una alternativa de desarrollo; no demuestra compatibilidad concurrente con PostgreSQL.

Desde la carpeta raíz, en PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
.\.venv\Scripts\python backend\manage.py migrate
$env:DEMO_PASSWORD = 'Elige-una-clave-local-larga'
.\.venv\Scripts\python backend\manage.py seed_demo
.\.venv\Scripts\python backend\manage.py runserver 127.0.0.1:8000
```

En otra terminal, desde la raíz:

```powershell
cd frontend
npm ci
npm run dev
```

Abre http://127.0.0.1:5173: aparece Inicio sin necesidad de sesión. Pulsa Iniciar sesión y entra con usuario `demo` y la contraseña elegida.
Usa la dirección exacta mostrada por Vite si el puerto está ocupado. El proxy `/api` mantiene
sesión y CSRF en el mismo origen. No abras `index.html` directamente.

`seed_demo` es idempotente: no cambia contraseñas ni desplaza la fecha del saldo existente.
Si ya existe `demo`, cambia su contraseña con `python backend/manage.py changepassword demo`
usando el ejecutable del entorno virtual. No utiliza credenciales bancarias.

## Verificación automatizada

```powershell
.\.venv\Scripts\python backend\manage.py check
.\.venv\Scripts\python backend\manage.py test backend/tests
.\.venv\Scripts\ruff check backend
.\.venv\Scripts\ruff format --check backend
cd frontend
npm run build
```

Las pruebas usan una base temporal y cubren sesión/CSRF, aislamiento entre empresas, idempotencia
de transacciones, horizontes inválidos, ausencia de saldos y precisión decimal con vencidos.

## Prueba manual de aceptación

1. Entrar con contraseña incorrecta: aparece un error. Entrar con la correcta: aparece el dashboard.
2. Saldo inicial de la demo: $8.500.000 COP; cobros a 30 días: $5.500.000; pagos: $12.800.000.
3. Déficit inicial: día 23 desde el corte; mínimo: −$1.200.000; saldo final: $1.200.000.
4. Cambiar 30/60/90 días. Después del último compromiso la línea es plana porque no se estiman flujos variables.
5. Recargar mantiene sesión; cerrar sesión impide consultar `/api/companies/`.
6. Comprobar pantalla móvil y teclado, estados vacíos y error al detener el backend.

## Servicios externos para fases posteriores

| Prueba | Acción externa necesaria | Estado |
|---|---|---|
| PostgreSQL + Redis | Iniciar Docker Desktop y ejecutar `docker compose up -d`; configurar variables de `.env.example` en la terminal del backend. | Infraestructura opcional; worker todavía sin pipeline. |
| Sandbox bancario | Crear cuenta de desarrollador, solicitar acceso, confirmar cobertura de movimientos/saldos y registrar redirect URI cuando proceda. | Adaptador pendiente; no hace falta para v0.1. |
| Facturación por XML | Obtener archivos UBL 2.1 sintéticos o anonimizados autorizados. | Importador pendiente. |
| Alegra/Siigo | Cuenta de pruebas, acceso autorizado a API y credenciales de backend. | Opcional, alternativa a XML. |
| Recuperación de contraseña | Configurar correo de pruebas/SMTP. | Funcionalidad pendiente. |
| HTTPS y acceso remoto | Dominio/certificado, proxy y secretos de despliegue; revisar hardening. | No desplegar esta configuración local con datos reales. |
| Investigación | Generar dataset de 100 empresas × 24 meses y acordar protocolo de validación. | No confundir con los 60 movimientos de esta demo. |

`.env.example` es una referencia: Django no carga automáticamente archivos `.env`.
Docker Compose arranca solo PostgreSQL y Redis; el backend/frontend se inician con los comandos anteriores.
Para probar sobre PostgreSQL configura POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER y POSTGRES_PASSWORD,
ejecuta las migraciones y las mismas pruebas. La contraseña local del Compose no sirve para producción.

## Estado del entregable

No están implementados: registro público, recuperación de contraseña, edición de empresas/roles,
CSV/XLSX, XML, correcciones de clasificación, auditoría completa, jobs ETL, OAuth bancario,
ARIMA/Prophet, cuantiles, backtesting, backups y despliegue de producción.
Celery está configurado como base, sin tareas financieras. Las categorías de la demo son fixtures,
no resultados de un clasificador. Ningún endpoint modifica movimientos ni efectúa pagos.

## Verificación en este equipo

- Python 3.13.12, Node 24.13.0 y npm 11.6.2 detectados.
- Migraciones SQLite aplicadas; 9 pruebas Django aprobadas, Ruff lint/formato aprobados y build TypeScript/Vite completado. Docker Compose validó su configuración sin iniciar servicios.
- Prueba HTTP real por el proxy Vite aprobada: HTML, CSRF, login, cookie de sesión, listado de empresas y dashboard. Mínimo confirmado: −$1.200.000 COP.
- Vite informó un bundle de aproximadamente 521 kB sin comprimir; la división de carga queda como optimización posterior.
- Docker CLI disponible, pero Docker Desktop/motor Linux no estaba iniciado. No se ejecutaron pruebas PostgreSQL/Redis.
- El navegador automatizado no pudo iniciarse por un error del sandbox de Windows (`apply deny-read ACLs`). La revisión visual y los pasos manuales siguen pendientes; no se afirma haber probado el dashboard en navegador.
- Los servidores locales se iniciaron en 127.0.0.1:8000 y 127.0.0.1:5173 durante la entrega; si se cierran, usar los comandos de esta guía.

## Actualización: Inicio público y Docker operativo

La comprobación posterior confirmó Docker Desktop activo. PostgreSQL y Redis están arrancados,
las migraciones fueron aplicadas, la demo cargada y las 9 pruebas aprobaron también con PostgreSQL.
Redis respondió PONG. La API activa utiliza PostgreSQL; SQLite conserva la demo anterior por separado.

Para próximos arranques, con Docker Desktop abierto, ejecutar desde la raíz:

```powershell
.\scripts\start-backend.ps1
```

En otra terminal:

```powershell
cd frontend
npm run dev
```

El script configura las variables de PostgreSQL automáticamente y conserva los datos del volumen.
No vuelve a crear usuarios ni cambia contraseñas. Si es una instalación nueva, seguir primero la instalación de dependencias.

Rutas de interfaz:
- `http://127.0.0.1:5173/#/`: Inicio público, disponible con y sin sesión.
- `http://127.0.0.1:5173/#/login`: formulario de acceso (o área privada si ya hay sesión).
- `http://127.0.0.1:5173/#/dashboard`: área privada; sin sesión muestra acceso.

Prueba manual: visitar Inicio en ventana privada, ir a Iniciar sesión, volver a Inicio,
entrar, visitar Inicio con sesión y regresar al dashboard. Cerrar sesión debe volver a Inicio.
La pantalla de Inicio no depende de que la API responda para mostrar su contenido.

Verificación: build TypeScript/Vite aprobado; HTTP real de página y módulo público, rechazo de
API sin sesión, login y dashboard aprobado. La automatización visual continúa bloqueada por el
error de sandbox de Windows; no se afirma validación visual en navegador.

## Corrección del acceso desde navegador

La API autoriza explícitamente los orígenes de Vite en desarrollo: http://127.0.0.1:5173 y
http://localhost:5173. CSRF continúa activo y exige token; otros orígenes se rechazan.
En otros entornos configurar DJANGO_CSRF_TRUSTED_ORIGINS con los orígenes exactos separados por coma.
Se verificó login HTTP con Origin/Referer y cookie de sesión en ambas direcciones; las 10 pruebas
sobre PostgreSQL pasan, incluida regresión de origen permitido, origen ajeno y token ausente.
La contraseña del usuario demo local se acortó a petición del usuario; no se utiliza fuera de la demo.

## Importación CSV implementada

En el dashboard, abrir **Importar movimientos**, descargar el CSV de ejemplo, seleccionar la cuenta y cargar el archivo.
Formato UTF-8 con coma como separador y encabezado exacto:

```csv
external_id,date,amount,description
prueba-001,2026-09-01,150000.00,Venta de prueba
prueba-002,2026-09-02,-45000.00,Compra de insumos
```

Ingresos positivos, egresos negativos, máximo dos decimales sin separadores de miles. Máximo 2 MB y 10.000 filas.
Las fechas deben ser válidas y no posteriores al corte del saldo. Solo propietario/contador pueden importar.
La clave estable es cuenta + external_id. Una segunda carga omite movimientos idénticos; un ID con datos
distintos rechaza el archivo completo, sin actualizar ni cargar parcialmente. El saldo disponible no cambia
porque el historial ya está representado en el corte. Las categorías nuevas quedan en Otros; clasificación pendiente.

**Servicio adicional local:** mantener abierto el worker, además del backend y frontend:

```powershell
.\scripts\start-worker.ps1
```

Ya se dejó iniciado durante esta entrega. No requiere cuenta ni claves externas: usa Redis/PostgreSQL del Docker local.
El worker utiliza pool solo para desarrollo Windows. No es la configuración de despliegue de producción.
Si la importación permanece en cola, comprobar el worker. Si Redis no acepta el envío se indica el fallo y hay que
volver a cargar el archivo. El estado en cola también cubre procesamiento activo; no muestra porcentaje de avance.

Las últimas 20 importaciones muestran resultado, nuevos y duplicados. El registro almacena usuario, cuenta,
fecha, checksum, resultado y error; el contenido del CSV se borra al terminar. No es aún la auditoría completa del MVP.
Recargar el panorama al completarse muestra los movimientos recientes; la tabla solo contiene los últimos 20.

Verificación: 16 pruebas PostgreSQL aprobadas, build aprobado y carga HTTP multipart con CSRF y worker real:
primera carga 1 nuevo; segunda carga 0 nuevos y 1 duplicado. Quedó un movimiento sintético de QA en la demo.
Prueba visual automatizada no realizada (bloqueo de sandbox documentado anteriormente).

## Clasificación y corrección manual implementadas

En **Movimientos y categorías** se muestran todos los movimientos por páginas de 20. Pulsa
**Actualizar movimientos** después de importar, o usa Anterior/Siguiente. Propietario y contador
pueden pulsar **Clasificar**, seleccionar una categoría y guardar; Consulta solo puede leer.

La opción **Recordar** crea o reemplaza una regla de esta empresa para la misma descripción
normalizada y sentido (ingreso/egreso). Se normalizan acentos, mayúsculas y espacios, conservando
números de referencia. No es un clasificador ML ni una coincidencia aproximada de comercios.
Sin marcar Recordar, solo cambia ese movimiento; no elimina una regla guardada anteriormente.
Para reemplazar una regla, guardar otra categoría con Recordar marcado. Los movimientos antiguos
no se reclasifican masivamente y las importaciones repetidas conservan las correcciones manuales.

Las nuevas importaciones aplican primero reglas de empresa y después reglas de palabras completas
para ventas, nómina, arriendo, software, servicios públicos, impuestos y proveedores. Coincidencias
ambiguas/desconocidas quedan en Otros; no se afirma una precisión predictiva medida. Las categorías
se restringen según el signo del monto. No cambia dinero, obligaciones ni proyecciones.
Cada corrección registra usuario, fecha, categoría anterior/nueva y si se recordó.

No hay pasos externos adicionales. API y worker se reiniciaron y siguen disponibles.
Verificado: 22 pruebas PostgreSQL, lint/formato y build; HTTP real con CSRF y Celery comprobó:
Software automático → corrección a Marketing → nueva importación con regla de empresa.
Quedaron dos movimientos sintéticos ADOBE QA CLASIFICACION y su regla para esta comprobación.
La comprobación visual automatizada continúa pendiente por el bloqueo de Windows ya documentado.

## Arranque conjunto

Con Docker Desktop listo, ejecutar desde la raíz:

```powershell
.\scripts\start-dev.ps1
```

Inicia backend, frontend y worker en segundo plano; reutiliza los puertos del proyecto si ya están activos.
Los logs están en `.local-logs/` (ignorados por Git). Si actualizas código Python con procesos activos,
reinicia esos procesos para cargar los cambios. Para instalaciones nuevas, instalar primero las dependencias
bloqueadas con pip y npm ci. Defusedxml es ahora una dependencia del backend.

## Obligaciones y conciliación

En Cuentas por cobrar y pagar: crear una obligación con referencia única, contraparte, vencimiento,
sentido y pendiente; abrir Ver detalle para editar metadatos, cancelar/reactivar, conciliar o deshacer.
Cancelar excluye la obligación del pronóstico sin borrar historial. La conciliación solo vincula un
movimiento ya importado del mismo tenant y sentido, dentro del corte bancario: no mueve dinero.
Puede ser parcial y repartirse entre obligaciones sin superar la capacidad total del movimiento.
El importe pendiente no se edita directamente; la conciliación/reversión lo actualiza con auditoría.
El dashboard se refresca tras las modificaciones. Una obligación de QA quedó cancelada y su conciliación revertida.

## Facturas XML

Descarga el ejemplo sintético desde Facturas XML y cárgalo. Se procesa en el worker; un CUFE ya
existente no crea otra factura. El NIT debe coincidir con emisor o receptor de la empresa activa.
El ejemplo corresponde a SYNTHETIC-001. Se aceptan Invoice UBL 2.1 y AttachedDocument con Invoice
embebida en Description; UTF-8, COP, hasta 2 MB. Se rechazan DTD/entidades externas, fechas inválidas,
monedas no soportadas y CUFE repetido con contenido financiero diferente.

Pulsa Revisar y confirma una fecha y el pendiente conocido: el XML por sí solo no prueba cobro/pago.
Si falta fecha en XML, debes ingresarla. Se crea una única obligación; volver a confirmar no la duplica.
Si ya registraste manualmente la misma factura, usa Vincular sin crear otra obligación al revisarla. El enlace conserva pendiente, fecha y conciliaciones.
No se validan firmas, XSD completo ni aceptación DIAN; el ejemplo es de extracción, no un documento fiscal válido.
No se procesan notas crédito, ZIP ni PDF en esta fase. Se conserva el contenido financiero normalizado y
se elimina el XML temporal tras el procesamiento. La factura QA-XML-001 se confirmó con pendiente cero durante la prueba.

Evidencia actual: 38 tests PostgreSQL aprobados, lint/formato y compilación aprobados; pruebas HTTP
reales de obligaciones y XML con Celery aprobadas. La verificación visual de estos nuevos paneles sigue pendiente.

Fuentes del parser: [UBL 2.1 OASIS](https://www.oasis-open.org/standard/ublv2-1/) y
[defusedxml](https://pypi.org/project/defusedxml/). El estado de todo el alcance se mantiene en IMPLEMENTATION_STATUS.md.

## Enlace de facturas a obligaciones existentes

Revisar factura permite elegir una obligación compatible ya registrada. La selección es explícita, por referencia y contraparte; no se infiere igualdad por monto. Se conserva pendiente/vencimiento y se audita el vínculo. Una obligación no puede enlazarse a dos facturas. 41 pruebas SQLite/PostgreSQL y build aprobados.

## Registro y alta inicial

En Inicio o Iniciar sesión, abrir Crear cuenta y empresa. Introducir usuario, correo, contraseña,
nombre/NIT de prueba y cuenta manual con saldo/corte. La operación crea propietario y sesión sin
privilegios de plataforma. Los datos nuevos no acceden a empresas ajenas. Si el usuario/NIT existe,
la operación se revierte completa. Contraseña nueva: mínimo 10 caracteres, no común ni solo numérica.
El correo todavía no se verifica ni se envía ningún mensaje. El saldo es declarado, no leído de un banco.
La demo conserva su contraseña corta existente. Recuperación de contraseña y gestión posterior de
membresías siguen pendientes. 45 pruebas PostgreSQL y build aprobados.

## Recuperación de contraseña

Desde Iniciar sesión, abrir Olvidé mi contraseña. Introducir usuario y correo registrados.
La respuesta no confirma existencia de la cuenta. Celery genera el correo solo si ambos coinciden
con una cuenta activa. Por defecto local se escribe un archivo en `.local-logs/emails/`;
abre el archivo más reciente y copia el enlace a tu navegador. No se envía correo real ni se muestra
el token en la API. Los archivos del buzón contienen enlaces privados y se ignoran en Git.
La cuenta demo original no tiene correo: prueba con una cuenta registrada desde el formulario.

El enlace vence en 1 hora y se invalida tras restablecer contraseña. Se exige mínimo 10 caracteres
y los validadores configurados; las sesiones con la contraseña anterior dejan de ser válidas.
Se exige CSRF en solicitud y confirmación y se limita a 5 solicitudes por hora/IP o usuario.
El worker debe estar activo para generar los correos locales.

Para envío real (no verificado en esta entrega), configurar en backend y worker: EMAIL_BACKEND=
django.core.mail.backends.smtp.EmailBackend, EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER,
EMAIL_HOST_PASSWORD, EMAIL_USE_TLS, DEFAULT_FROM_EMAIL y FRONTEND_URL. No uses la dirección
localhost al enviar a usuarios remotos. Se requiere acceso a un proveedor SMTP y URL pública.
51 pruebas PostgreSQL aprobadas: enlace válido, expirado, usado, correo incorrecto, usuario inactivo,
CSRF, contraseña débil y cierre de sesiones previas. No se ha probado un proveedor SMTP externo.

## Empresa y equipo

Abrir Empresa y equipo en la barra privada. El propietario puede renombrar su empresa, añadir un
usuario ya registrado (por su username exacto), asignar Propietario/Contador/Consulta y retirar acceso.
No se envían invitaciones externas. El NIT no se cambia desde este formulario para mantener la
coherencia de facturas importadas. Consulta/Contador pueden ver el equipo, pero no modificarlo.
La empresa debe conservar al menos un propietario activo; primero promueve a otro miembro si
quieres retirarte. La autorización se vuelve a evaluar en cada petición, sin confiar en el rol del frontend.
Se auditan altas, bajas, roles y cambio de nombre. Retirar acceso no borra al usuario ni el historial.
56 pruebas PostgreSQL y build aprobados. No se modificaron miembros de la demo durante las pruebas.


## Importación Excel

Se admiten archivos .xlsx de hasta 2 MB, una sola hoja y hasta 10.000 movimientos. Usa las columnas A–D con encabezados external_id, date, amount, description. Guarda identificadores y descripciones como texto; las fechas pueden ser celdas de fecha sin hora o texto ISO. No se admiten fórmulas, macros ni enlaces externos. Puedes guardar la plantilla CSV como XLSX conservando los identificadores como texto.

El procesamiento usa el mismo worker y las mismas reglas de corte y duplicados del CSV. Para probar localmente basta con Docker Desktop y scripts/start-dev.ps1; no necesitas cuentas ni claves externas. La prueba automatizada de 10.000 filas valida el parser, no el rendimiento de inserción en base de datos.


## Normalización de movimientos

En Movimientos puedes desplegar la descripción normalizada. Por ejemplo, `Pago; Comercio: Café 24; REF: 123` conserva su texto original, muestra comercio `CAFE 24` y elimina la referencia etiquetada de su versión normalizada. Los números sin etiqueta se conservan. No se infiere un comercio para descripciones ambiguas. El historial se migra sin modificar importes, categorías ni saldos. Esta función no necesita servicios externos; la resolución de comercios de proveedores bancarios sigue pendiente.


## Recurrencias sugeridas

El dashboard muestra patrones con al menos tres fechas distintas por cuenta, descripción normalizada y signo. Semanal: intervalos de 6–8 días. Mensual: meses consecutivos, día similar (diferencia máxima 3) o últimos tres días del mes. Cada monto debe estar a ±10% de la mediana. Se utiliza hasta 370 días anteriores al corte bancario y se descartan patrones cuya siguiente fecha ya pasó. Las sugerencias no modifican saldos ni proyecciones; su conciliación e integración en proyecciones siguen pendientes. No requieren servicios externos.

Los roles owner/accountant pueden confirmar, rechazar o reabrir un patrón desde el dashboard; viewer solo consulta. La decisión persiste por empresa y evidencia exacta. Al cambiar montos, fechas, frecuencia o movimientos de soporte, se exige nueva revisión. Las decisiones anteriores se conservan para auditoría. Confirmar por sí solo no crea una obligación. Después puedes crear o vincular la próxima ocurrencia; esa obligación sí participa en la proyección.


### Próxima ocurrencia y obligaciones

Tras confirmar una recurrencia, vincula una obligación existente del mismo sentido y fecha, o crea la próxima obligación por el monto estimado. Repetir la creación devuelve la misma obligación. Si existe una obligación pendiente de igual fecha y sentido, la creación se bloquea para revisarla primero. Vincular conserva el monto pendiente real (incluidos pagos parciales). La proyección suma únicamente la obligación. Rechazar o reabrir el patrón no cancela una obligación ya creada: se gestiona desde Obligaciones. El calendario permite gestionar cada ocurrencia del horizonte seleccionado. La desvinculación está disponible desde cada fecha vinculada. No se requieren servicios externos.


### Calendario de recurrencias 30/60/90

Selecciona el horizonte del dashboard y abre «Fechas previstas» en una recurrencia. Puedes vincular o crear una obligación para cada fecha tras confirmar el patrón. No se crean automáticamente al cambiar de horizonte. Las fechas semanales avanzan siete días; las mensuales conservan el día de referencia o fin de mes, sin desplazarse por febrero. Cambiar de horizonte conserva los vínculos y no duplica obligaciones. Las obligaciones canceladas continúan identificadas como tales, sin volver a crearse.

Pruebas: 13 ocurrencias semanales en 90 días, totales correspondientes a cada horizonte, repetición idempotente, rechazo de fechas ajenas al patrón y calendario mensual cruzando febrero.


### Corregir vínculos de recurrencias

Usa «Desvincular conservando la obligación» en una fecha vinculada. Se elimina solo la asociación: obligación, pagos, importe pendiente y proyección permanecen. Puedes vincularla de nuevo si es compatible. Un usuario viewer no puede desvincular. La auditoría conserva la asociación anterior; una petición antigua no elimina una asociación posterior. Si la obligación fue cancelada o cambió de fecha, revísala en Obligaciones: no se recrea automáticamente.


## Histórico de ingresos y egresos

El dashboard muestra doce meses naturales hasta el corte bancario, incluido el mes parcial actual. Se agregan solo movimientos de la empresa entre el primer día del periodo y el corte, ambos inclusive. Los egresos se muestran positivos y el neto es ingresos menos egresos, no un saldo reconstruido. La tabla por categorías usa el mismo periodo y categorías vigentes. Después de importar o reclasificar, usa Actualizar histórico. Los meses sin registros están identificados como sin datos; no prueban ausencia de actividad. No requiere servicios externos.

Verificado con PostgreSQL: importes decimales, límites de periodo, exclusión de movimientos futuros y de otras empresas, estado vacío y rechazo de cortes incompatibles. Build aprobado; no sustituye la revisión visual en navegador.


## Gestión de reglas de clasificación

En el dashboard, «Reglas de clasificación guardadas» lista las reglas de la empresa con paginación. Owner/accountant pueden eliminarlas; viewer solo consulta. La eliminación queda auditada y afecta únicamente a futuras clasificaciones, que vuelven a usar las reglas automáticas o la categoría Otros. Los movimientos históricos conservan sus categorías. Para volver a crear una regla, corrige un movimiento marcando Recordar. Usa Actualizar reglas para ver cambios recientes. No requiere servicios externos.


## Empresas adicionales

En Empresa y equipo abre Crear otra empresa. Indica nombre, NIT, cuenta manual, saldo COP y corte no futuro. El usuario actual recibe el rol propietario exclusivamente en la nueva empresa, y esta aparece seleccionada en el formulario de equipo. El alta es atómica y queda auditada. Los NIT se comparan sin distinguir mayúsculas, incluidos registros antiguos. No se conectan bancos ni se requiere un servicio externo.


## Mi cuenta

Desde Mi cuenta puedes actualizar el correo de recuperación y cambiar la contraseña indicando la actual. La nueva requiere al menos 10 caracteres y los validadores de Django. La sesión actual se conserva y las demás se invalidan cuando vuelvan a realizar una petición. Un cambio inválido no guarda el correo parcialmente. No se envía correo de verificación; SMTP externo sigue pendiente de configuración para probar recuperación con entrega real. Editar la cuenta local no requiere servicios externos. Las pruebas usan usuarios temporales y no cambian demo/demo1234.


## Cobertura del historial

El dashboard revisa los últimos 365 días hasta el corte y muestra métricas separadas por cuenta. Sin movimientos, amplitud menor de 90 días y amplitud de al menos 90 días son etiquetas descriptivas, no requisitos validados de un modelo ni niveles de confianza. Se muestran también días activos para no confundir dos movimientos distantes con historial completo. No se incluyen fechas futuras. La proyección sigue basada en obligaciones incluso sin historial; la selección y calibración de modelos continúa pendiente. No requiere servicios externos.


## Saldos y cortes manuales

Owner/accountant pueden declarar saldo COP y fecha de corte desde el dashboard. El corte no puede ser futuro ni anterior a movimientos registrados. Cambiarlo no modifica movimientos ni concilia obligaciones automáticamente. Usa el saldo real del extracto, incluidos movimientos del día; todas las cuentas deben tener el mismo corte. Los cambios quedan auditados. No requiere conexión bancaria ni servicios externos.


## Umbral de liquidez

El propietario configura un mínimo COP no negativo en el dashboard. La alerta compara saldo al corte y proyección de obligaciones con ese mínimo: igualdad no activa alerta, un saldo menor sí. Muestra primera fecha, días futuros por debajo y brecha máxima (incluido el corte). Contador y Consulta solo leen la configuración. Cambios auditados; no requiere servicios externos. No calcula probabilidades; las evaluaciones se guardan explícitamente en el historial.


## Historial de evaluaciones de liquidez

Owner/accountant pueden guardar evaluaciones de 30/60/90 días desde el dashboard. Se conservan corte, saldo, umbral, cuentas, obligaciones y resultado del método obligations_v1. Datos idénticos reutilizan la misma evaluación; cambios generan otra. Viewer solo consulta el listado paginado de su empresa. No hay evaluación programada ni notificaciones externas; no requiere servicios externos para probar el historial.


## Consulta de auditoría

En Empresa y equipo, propietario y contador consultan fecha, usuario, acción y valores antes/después. La lista está paginada y admite filtro exacto por código de acción, por ejemplo account.balance_updated. Consulta no tiene acceso; no existen endpoints para editar o borrar registros de auditoría. Solo aparecen acciones ya instrumentadas, no todos los accesos. No requiere servicios externos.


## Referencia estadística experimental

Para habilitarla, importa movimientos de cada cuenta y confirma en Saldos de cuentas manuales que los 90 días previos al corte están completos, incluidos días sin actividad. En el dashboard elige horizonte y método. Si falta cobertura o hay menos de cuatro días con flujo variable, la sección explica por qué no muestra resultados. El gráfico y la tabla muestran por separado obligaciones y flujo variable estimado. Este cálculo no produce intervalos ni probabilidades. Cambiar el corte o importar movimientos nuevos dentro del periodo retira la confirmación; tendrás que revisar los datos y confirmarla de nuevo. No requiere servicios externos.
## Incidencia vigente de CI PostgreSQL — 5 de octubre de 2026

**Resuelta en CI:** la ejecución `37324872869`, commit `6fe6ff5`, terminó `success`.
Los cuatro jobs, incluido `backend-postgres`, pasaron. Las notas siguientes conservan el
diagnóstico y los límites previos; ya no falta el resultado PostgreSQL de esta corrección.

El log completo aportado por el usuario identificó `OperationalError: the connection is closed`.
Las pruebas de worker y recuperación llamaban a `run_background` desde `TestCase`; su transacción
envolvente provoca que la limpieza de conexiones cierre PostgreSQL. Se cambiaron ambas clases a
`TransactionTestCase` para ejecutar el comando fuera de esa transacción. No se deshabilitó la
limpieza de conexiones del worker. Suite local: 188 pruebas, 183 aprobadas y 5 omitidas; falta
el resultado del nuevo job PostgreSQL para confirmar la corrección en ese motor.

La ejecución pública `37320630224` de `codex/v1-hosted` pasó frontend, backend SQLite y
desktop, pero falló en el paso de tests de `backend-postgres`. Las anotaciones públicas solo
indican código de salida 1; no identifican el test fallido. No atribuir el fallo a una prueba
concreta sin su traceback ni marcar PostgreSQL verificado por las pruebas HTTP de Render.

No hay daemon Docker local accesible actualmente. La revisión automática rechazó leer una
credencial Git local y publicar automáticamente el texto completo de fallo como anotación,
por falta de autorización y de garantía sobre datos sensibles. Se necesita el fragmento del
paso fallido o un entorno PostgreSQL de pruebas aislado. No ejecutar la suite destructiva de
Django sobre la base de datos de la aplicación alojada.
