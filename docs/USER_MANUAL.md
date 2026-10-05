# Manual de uso y pruebas de Horizonte

Estado: 5 de octubre de 2026. Describe las funciones actuales; no certifica el cierre del
entregable. Utilizar empresas, archivos y correos de prueba. No cargar información bancaria real.

## Instalar y conectar el escritorio

Huella y alcance de verificación del binario: [DESKTOP_RELEASE.md](DESKTOP_RELEASE.md).

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

Para una prueba con cifras exactas, seguir [ensayo de escritorio](DESKTOP_ACCEPTANCE.md).

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

- Administrador: cuentas Render Free y Supabase Free, repositorio accesible por Render y
  credenciales guardadas fuera de Git. Ver `HOSTING_FREE.md`.
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
la asignación de alias de una fuente; esa gestión todavía está pendiente.
## Asignar etiquetas de comercios

En Comercios, un propietario o contador puede seleccionar un comercio de la página actual
y asignarle una etiqueta de la fuente CSV/XLSX o Mock Bank. Introduce el nombre explícito del
comercio que aparece en la fuente, no toda la descripción del movimiento. Se normalizan las
mayúsculas y los acentos. La asignación sustituye la anterior para esa etiqueta y fuente dentro
de la empresa; afecta las próximas importaciones, sin modificar los movimientos ya guardados.
El listado «Etiquetas por fuente» muestra las asignaciones vigentes, incluidas las detectadas
automáticamente, en páginas de veinte filas. Se actualiza al guardar una asignación o pulsar
Actualizar. Si falla la consulta, utiliza Reintentar.
