# Manual de uso y pruebas de Horizonte

Revisión documental: 16 de octubre de 2026. Describe la versión funcional de pruebas;
no certifica el cierre académico ni disponibilidad remota actual. [Estado y pendientes](ESTADO_Y_PENDIENTES.md).
Utilizar empresas, archivos y correos de prueba. No cargar información bancaria real.

## Probar la web localmente desde CMD (Windows)

Abre **dos ventanas de Símbolo del sistema (CMD)**: una para Django y otra para React/Vite. Necesitas Python 3.13 y Node.js con npm instalados. Esta modalidad usa SQLite local y no requiere Docker ni configurar el alojamiento.

### 1. Preparación inicial (solo la primera vez)

En CMD, entra a la raíz del proyecto y prepara las dependencias:

```bat
cd /d C:\Users\elcre\Desktop\Programas\Proyecto
py -3.13 -m venv .venv
.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
cd frontend
npm ci
```

Si `.venv` y las dependencias ya están preparadas, puedes omitir este paso. Repite la instalación de dependencias cuando cambien sus archivos de requisitos. Si guardas el proyecto en otra carpeta, sustituye la ruta en los comandos.

### 2. Ventana CMD 1: encender el backend

```bat
cd /d C:\Users\elcre\Desktop\Programas\Proyecto
set DJANGO_DEBUG=1
set POSTGRES_HOST=
set BACKGROUND_MODE=database
.venv\Scripts\python.exe backend\manage.py migrate
.venv\Scripts\python.exe backend\manage.py runserver 127.0.0.1:8000
```

Espera a que aparezca `Starting development server at http://127.0.0.1:8000/` y deja esta ventana abierta. `migrate` prepara o actualiza la base SQLite en `backend\db.sqlite3`; los datos se conservan entre arranques. No cargues `.env.hosted` en esta sesión. Los comandos usan el Python del entorno virtual directamente, por lo que no necesitas activarlo.

### 3. Ventana CMD 2: encender el frontend

```bat
cd /d C:\Users\elcre\Desktop\Programas\Proyecto\frontend
npm run dev -- --port 5173 --strictPort
```

Deja también esta ventana abierta. Abre **[http://127.0.0.1:5173](http://127.0.0.1:5173)** en el navegador. Usa esta dirección para probar la interfaz: Vite envía automáticamente las solicitudes `/api` al backend en el puerto 8000. No hace falta ejecutar `npm run build` para este modo de desarrollo.

### 4. Probar movimientos y predicciones

Desde Inicio, elige crear cuenta y empresa; declara la cuenta manual, el saldo y su corte. Luego registra ingresos y egresos y sigue el apartado «Primera versión web» de este manual. Para ver la estimación inicial, registra toda la actividad de siete días y confirma ese periodo en Saldos de cuentas. Puedes reproducir las cifras del [guion de prueba](PLAN_DEMO_FUNCIONAL.md).

### 5. Cola de importaciones y Mock Bank

Con `BACKGROUND_MODE=database`, `runserver` inicia automáticamente el worker local: las dos ventanas anteriores bastan también para importar CSV/XLSX/XML y sincronizar Mock Bank. Reinicia el backend después de actualizar esta versión. La consola debe indicar «Cola local activa».

Solo si decides operar el worker por separado, define `set DJANGO_LOCAL_WORKER=0` en la ventana del backend antes de iniciarlo y abre una tercera ventana CMD:

```bat
cd /d C:\Users\elcre\Desktop\Programas\Proyecto
set DJANGO_DEBUG=1
set POSTGRES_HOST=
set BACKGROUND_MODE=database
.venv\Scripts\python.exe backend\manage.py run_background
```

No inicies ese worker adicional si `runserver` ya muestra «Cola local activa». La cola de BD no necesita Redis. Una importación ya en cola se procesa al arrancar el worker; consulta el resultado antes de volver a subirla.

### Apagar y resolver problemas básicos

- Para detener cada servidor o el worker, pulsa **Ctrl+C** en su ventana CMD. Para volver a encenderlos, repite los pasos 2 y 3 (y el 5 si lo necesitas).
- Si CMD no reconoce `py`, `node` o `npm`, comprueba su instalación y abre una ventana CMD nueva.
- Si aparece un error de módulo de Python o faltan paquetes de Vite, repite la preparación de dependencias.
- Si el puerto 8000 o 5173 está ocupado, detén la instancia anterior con Ctrl+C y vuelve a iniciar. Conserva estos puertos para mantener el proxy y la configuración local de CSRF.
- Si la interfaz abre pero no puede consultar datos, comprueba que el backend siga abierto en el puerto 8000 y que estés entrando por `http://127.0.0.1:5173`.

## Secciones del dashboard

La barra lateral separa las herramientas; cada opción abre su propia vista y conserva la empresa seleccionada. Los enlaces permiten volver atrás o recargar directamente una sección. En pantallas pequeñas la navegación se adapta a una franja horizontal.

| Grupo | Secciones |
|---|---|
| Operación | Resumen; Movimientos; Cobros y pagos con calendario; Facturas |
| Análisis | Predicciones y recurrencias; Historial y categorías; Alertas de liquidez |
| Configuración | Cuentas y saldos; Fuentes de datos (archivos o Mock Bank); Reglas y comercios |

La conexión bancaria es opcional. Para llevar el registro por tu cuenta, entra en **Movimientos**. La fecha comienza en **hoy, hora de Colombia**, y vuelve a hoy después de guardar. Cámbiala cuando registres una operación pasada. Puedes guardar varios ingresos y egresos el mismo día, incluso con la misma descripción e importe; cada guardado confirmado representa una operación nueva. Reintentar un envío sin confirmar conserva su identidad para evitar duplicados.

Puedes registrar operaciones de hoy aunque el corte de la cuenta sea anterior. Esos movimientos se guardan y afectan inmediatamente el Resumen. Para incorporarlos a los pronósticos avanzados al corte, actualiza la fecha y el saldo en **Cuentas y saldos**. El saldo no cambia automáticamente: debe representar el dinero disponible al corte, incluidos los movimientos de ese día.

La **estimación inicial** considera todos los movimientos registrados anteriores o iguales al corte, desde el primero, y no solo los últimos siete días. Confirma la cobertura completa de ese intervalo, con un mínimo de siete días. Los movimientos posteriores al corte se excluyen hasta actualizarlo. Las conciliaciones siguen evitando contar pagos dos veces; los métodos estadísticos avanzados conservan sus ventanas y requisitos de historial.

## Primera versión web: movimientos y predicciones

1. Entrar desde el navegador y crear usuario/empresa con cuenta manual, saldo COP y corte.
2. En Movimientos elegir cuenta, fecha (hoy por defecto o un día pasado), ingreso/egreso, importe positivo y descripción. La categoría es opcional; vacía usa reglas automáticas.
3. Guardar y revisar el historial. El saldo declarado ya incluye el historial y no cambia por el alta. Ajustarlo explícitamente si es necesario.
4. Si falla la conexión, usar Reintentar guardado con los mismos datos; no recargar la página antes de confirmar el resultado. La clave de reintento se conserva mientras el formulario siga abierto.
5. Registrar toda la actividad hasta el corte. En Cuentas y saldos abrir Confirmar historial completo y elegir el inicio del historial registrado, como mínimo seis días antes del corte. Días sin movimientos se consideran cero solo bajo esa confirmación.
6. En Predicciones consultar la estimación inicial y cambiar 30/60/90 días. Registrar compromisos futuros en Obligaciones para incorporarlos con sus fechas.
7. Guardar el pronóstico para conservarlo. Un movimiento nuevo dentro del periodo retira la confirmación: revisar y confirmar de nuevo. Los métodos más amplios requieren 90 días completos; la estimación inicial no ofrece cuantiles ni probabilidades.

El lector consulta; propietario y contador registran. Una cuenta conectada se actualiza desde su fuente y no acepta captura manual. [Guion con cifras esperadas](PLAN_DEMO_FUNCIONAL.md).

## Referencia de escritorio (entrega anterior)

### Instalar y conectar el escritorio

Huella y alcance de verificación del binario: [DESKTOP_RELEASE.md](desktop/DESKTOP_RELEASE.md).

- Ejecutar el instalador Windows `desktop/release/session-isolation/Horizonte Setup 0.1.0.exe`.
  El ejecutable se generó y su arranque se comprobó; instalación, actualización y desinstalación
  en un equipo limpio siguen pendientes. No está firmado.
- Abrir Horizonte y escribir el origen HTTPS del servidor, sin rutas ni credenciales.
  El formulario ofrece `https://horizonte-demo.onrender.com`, servidor de pruebas disponible.
  El instalador no incluye una base de datos ni un backend local.
- Conectar. La pantalla Inicio debe estar disponible sin haber iniciado sesión.
- Para cambiar de servidor usar el menú Servidor. El cambio borra la sesión del origen anterior.
- El usuario final necesita Windows y acceso a Internet. No necesita Docker, Python ni Node.
  El modo empaquetado exige HTTPS; HTTP de localhost solo está disponible en desarrollo.
- En Render Free el primer acceso puede tardar mientras despierta el servicio. Si falla, esperar
  y volver a intentar. Una aplicación instalada no evita la suspensión del servidor.

## Cuenta, empresa y permisos

- Desde Inicio elegir crear cuenta y empresa. Completar el formulario con una identidad de prueba
  y una contraseña que cumpla la validación indicada. Se crea la membresía de propietario.
- Entrar con el usuario y contraseña creados. El usuario `demo` solo existe si el administrador
  preparó los datos de desarrollo; no es una cuenta garantizada del servicio remoto.
- En Empresa y equipo crear otra empresa, cambiar el nombre y administrar las membresías.
  El propietario administra; el contador puede operar datos financieros; el lector consulta.
- En Mi cuenta editar los datos disponibles. Para comprobar aislamiento crear otra cuenta sin
  membresía en la primera empresa: sus datos financieros no deben aparecer.
- Cerrar sesión y verificar que Inicio sigue visible y el dashboard requiere autenticación.
- La recuperación de contraseña necesita correo configurado en el servidor. La respuesta de la
  solicitud no confirma que el usuario exista ni que el mensaje haya llegado. El enlace enviado
  vence en una hora y deja de servir al cambiar la contraseña.

## Preparar los datos financieros

- Seleccionar la empresa antes de cada operación. Todas las cifras se presentan en COP.
- Revisar el saldo de cada cuenta y su fecha de corte. El saldo representa una observación
  disponible; importar movimientos históricos no lo recalcula automáticamente.
- Declarar cobertura histórica únicamente cuando se tenga el historial completo del período.
  La declaración no rellena movimientos ausentes ni demuestra que el archivo sea completo.
- En Importar movimientos seleccionar la cuenta manual y cargar CSV o XLSX de hasta 2 MB y
  10.000 filas. Ingresos positivos y egresos negativos; decimales con punto; fechas AAAA-MM-DD.
- Las columnas son `external_id,date,amount,description`. El ID debe ser estable por cuenta.
  XLSX admite una hoja, columnas A–D, IDs de texto y ninguna fórmula.
- Esperar el resultado: en cola, completado o fallido. Repetir el mismo archivo debe omitir
  duplicados; reutilizar IDs para movimientos distintos no es un modo de editar historial.
- Recargar el panorama para consultar movimientos. Si falla, leer el error y corregir el archivo.
  No repetir compulsivamente una carga que aún figura pendiente.
- Mock Bank permite probar consentimiento, sincronización y revocación con datos sintéticos.
  No conecta con una entidad bancaria real. Sus cuentas se actualizan desde esa fuente y no
  permiten cargas manuales.

## Revisar categorías, facturas y obligaciones

- En Movimientos revisar categorías y corregir las equivocadas. Las reglas de corrección se
  aplican por empresa; revisar las coincidencias antes de reutilizar una regla.
- En Clasificar puedes consultar Sugerir categoría. El modelo usa etiquetas manuales de esta
  empresa y puede abstenerse. Seleccionar la propuesta rellena la categoría; revisarla y pulsar
  Guardar categoría para aplicarla. Cancelar conserva el movimiento original. La sugerencia no
  representa una probabilidad de acierto validada.
- Los comercios identificados corresponden a etiquetas explícitas y alias por fuente. No se
  presupone reconocimiento automático completo de nombres bancarios.
- Cargar un XML de factura UTF-8 de hasta 2 MB y esperar su procesamiento. Revisar los datos
  extraídos y confirmar el pendiente antes de generar una obligación. No es validación DIAN.
- En Obligaciones crear o editar cobros y pagos con referencia, fecha y valor. Registrar pagos
  parciales reduce el pendiente; cancelar evita incluir ese compromiso como flujo futuro.
- No registrar dos veces un compromiso como factura, obligación manual y recurrencia. Cuando
  ya exista una obligación, vincularla al evento recurrente correspondiente.
- Revisar vencidos: los compromisos anteriores o iguales al corte necesitan una fecha estimada
  actualizada y no se desplazan automáticamente al futuro.

## Recurrencias, escenarios y pronósticos

- Actualizar patrones y revisar la evidencia semanal o mensual. Confirmar los que siguen
  vigentes, rechazar falsos positivos y reabrir si hace falta otra revisión.
- Expandir las fechas previstas de 30/60/90 días. Vincular un compromiso existente o crear una
  obligación desde un patrón confirmado. Desvincular conserva la obligación.
- El gráfico principal representa saldo y obligaciones registradas. No equivale a P50 ni a una
  predicción con intervalos de confianza.
- El pronóstico híbrido experimental separa compromisos conocidos, recurrencias confirmadas
  y flujo variable estimado. Si detecta ambigüedad con una obligación, revisarla y vincular antes
  de repetir. Si falta cobertura o evidencia, puede no estar disponible.
- Comparar los horizontes y métodos; guardar una ejecución para conservar sus entradas y
  resultados. Una edición posterior no altera el resultado histórico guardado.
- Ajustar el umbral de liquidez como propietario y revisar el historial de alertas. Un resultado
  sin déficit no garantiza solvencia: depende de los datos y supuestos registrados.
- Con 270 días completos por cuenta, el híbrido muestra banda P10–P90 y mediana P50 en el gráfico,
  además de P10/P50/P90 experimentales en la tabla
  diaria. P50 es una mediana estimada y puede diferir del saldo puntual. Los cuantiles dependen
  de errores históricos del flujo variable y tratan compromisos futuros como puntuales.
- Las ejecuciones guardadas muestran su gráfico y cuantiles originales; las anteriores que
  no tenían cuantiles conservan únicamente el saldo puntual. Una banda de un día no expresa
  la probabilidad de cubrir toda la trayectoria.
- P10/P50/P90 calibrados y riesgo probabilístico siguen pendientes. Los resultados sintéticos
  de investigación no prueban precisión con empresas reales.

## Recorrido de aceptación pendiente

Para una prueba con cifras exactas, seguir [ensayo de escritorio](acceptance/DESKTOP_ACCEPTANCE.md).

Registrar fecha, versión del instalador, servidor, resultado y evidencia de cada paso. Esta
lista es un procedimiento pendiente; no representa pruebas de usuario ya ejecutadas.

- Instalar en un Windows limpio, abrir Inicio sin sesión y crear una cuenta.
- Entrar, registrar un saldo y cargar un CSV; esperar completado y revisar movimientos.
- Repetir el CSV y comprobar duplicados; cargar un archivo inválido y verificar rechazo.
- Cargar XML, revisar factura, confirmar obligación y registrar un pago parcial.
- Confirmar una recurrencia y vincular su compromiso; comprobar que no se suma dos veces.
- Cambiar 30/60/90 días, guardar un pronóstico y consultarlo después de cerrar y abrir la app.
- Probar propietario, contador, lector y un usuario de otra empresa.
- Conectar Mock Bank, sincronizar dos veces y revocar el consentimiento.
- Cerrar sesión y comprobar que ningún dato financiero queda accesible desde Inicio.
- Probar contraseña olvidada con un correo propio autorizado, caducidad y enlace ya utilizado.
- Comprobar un arranque en frío, interrupción/reanudación de cola y persistencia tras suspensión.
- Cambiar el origen del servidor y verificar separación de sesiones; probar indisponibilidad.
- Ejecutar el simulacro de restauración del servidor y revisar los datos recuperados.

## Acciones externas necesarias

- Solo para recrear u operar el alojamiento: cuentas Render/Supabase, repositorio accesible
  y credenciales fuera de Git. El usuario que consume el servidor existente no necesita
  crear esas cuentas. Ver `operations/HOSTING_FREE.md`.
- Correo real: cuenta y credencial del proveedor HTTPS, remitente permitido y un destinatario
  de prueba autorizado. Para destinatarios generales hace falta un dominio verificado; no se
  contratará uno con el presupuesto de 0 USD.
- Equipo Windows limpio para comprobar el instalador completo. El arranque aislado ya realizado
  no sustituye este ensayo.
- Proveedor bancario real: sandbox, credenciales y consentimiento; Mock Bank no los sustituye.
- Evaluación de precisión y usabilidad: empresas/participantes y datos autorizados, anonimizados.
  No se han realizado esas pruebas con el dataset sintético.

Para fallos, informar el paso, mensaje, hora y si ocurre en web o escritorio. No enviar
contraseñas, claves API, enlaces de recuperación ni archivos financieros privados en capturas.
# Corregir el nombre visible de un comercio

En **Comercios identificados**, propietario y contador pueden pulsar **Editar nombre**,
escribir hasta 250 caracteres y elegir **Guardar** o **Cancelar**. El guardado queda auditado.
El nombre visible cambia sin modificar descripciones originales, alias ni vínculos de movimientos.
Los usuarios de consulta no ven la acción. Esto no consolida comercios duplicados ni cambia
la asignación de alias de una fuente. La asignación de etiquetas implementada se explica abajo;
la consolidación de comercios duplicados permanece fuera de esa función.
## Asignar etiquetas de comercios

En Comercios, un propietario o contador puede seleccionar un comercio de la página actual
y asignarle una etiqueta de la fuente CSV/XLSX o Mock Bank. Introduce el nombre explícito del
comercio que aparece en la fuente, no toda la descripción del movimiento. Se normalizan las
mayúsculas y los acentos. La asignación sustituye la anterior para esa etiqueta y fuente dentro
de la empresa; afecta las próximas importaciones, sin modificar los movimientos ya guardados.
El listado «Etiquetas por fuente» muestra las asignaciones vigentes, incluidas las detectadas
automáticamente, en páginas de veinte filas. Se actualiza al guardar una asignación o pulsar
Actualizar. Si falla la consulta, utiliza Reintentar.


## Gráfica del resumen y pagos mensuales

El Resumen ahora combina movimientos registrados y compromisos futuros. Cada ingreso/egreso adicional modifica el promedio diario orientativo y recalcula la gráfica, sin exigir confirmación de cobertura para esa vista. La caja disponible parte del saldo declarado y suma solo los movimientos posteriores a ese corte; los anteriores ya están incluidos. Si faltan registros, completa el historial: los días vacíos se asumen cero en esta estimación, que no es un modelo validado. Los pronósticos avanzados mantienen sus controles de cobertura.

En **Cobros y pagos → Pagos y cobros mensuales**, introduce concepto (por ejemplo «Sueldos»), valor, día 1 y fecha inicial; pulsa **Programar todos los meses**. Deja vacía la fecha final para que continúe cada mes. Cada vencimiento aparece en calendario y proyecciones; febrero y los meses cortos usan el último día si elegiste 29–31. No realiza transferencias. Para cambiar importe o frecuencia, detén la programación y crea otra. Detener cancela vencimientos futuros sin conciliaciones y conserva historial. Cuando el pago ya ocurra, concílialo con su movimiento para no contarlo de nuevo como pendiente ni como flujo variable.

Para probar la importación, reinicia el backend, entra en **Fuentes de datos**, descarga el ejemplo y súbelo a la cuenta manual. Debe terminar con dos movimientos nuevos; una segunda carga muestra duplicados omitidos. Los estados y errores aparecen bajo el formulario. Si el archivo contiene fechas posteriores al saldo declarado, actualiza primero el corte. No se necesita ejecutar manualmente un tercer proceso con el arranque local estándar de esta versión.


## Preparar una demostración local repetible

Con el entorno local instalado y las migraciones aplicadas, abre CMD en la raíz. Sustituye `TU_USUARIO` por tu usuario ya registrado en esta web:

```bat
.venv\Scripts\python.exe backend\manage.py prepare_web_demo --username TU_USUARIO --dry-run
.venv\Scripts\python.exe backend\manage.py prepare_web_demo --username TU_USUARIO
```

La primera orden solo muestra el plan. La segunda crea **dos empresas nuevas**, con identificador de lote y fecha de hoy, sin modificar empresas existentes ni la contraseña. Cada nueva ejecución crea otro lote y conserva el anterior. El comando se limita a SQLite local con `DJANGO_DEBUG=1`; no puede preparar datos en PostgreSQL ni producción. `--as-of AAAA-MM-DD` permite fijar un corte pasado para reproducir un ensayo.

Entra con ese usuario y selecciona:

- **Demo V1 Obligaciones**: saldo 500.000 COP, cobro 119.000 a corte+10 y pago 700.000 a corte+15, sin historial variable. Resumen: −81.000 desde el pago; umbral 100.000, diferencia al mínimo 181.000 COP.
- **Demo V1 Historial manual**: saldo declarado 500.000, ingreso 70.000 y egreso 140.000 en siete días sintéticos completos. Ya tiene cobertura confirmada para Predicciones → Estimación inicial. Saldos finales 30/60/90: 200.000, −100.000 y −400.000 COP. No hay compromisos en este caso.

Los movimientos se identifican como capturas manuales sintéticas y cada lote queda auditado. Para ensayar la captura tú mismo, crea una tercera empresa desde la interfaz; no agregues esos mismos movimientos de nuevo esperando que la curva conserve las cifras iniciales.
