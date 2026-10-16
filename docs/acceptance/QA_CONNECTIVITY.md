# Aceptación de conexión y recuperación del cliente

Estado: **pendiente de ejecución**, 5 de octubre de 2026. La compilación no demuestra estos
recorridos. El navegador de automatización no pudo arrancar: `apply deny-read ACLs` del
sandbox Windows. No se obtuvieron capturas ni resultados visuales.

Requisitos del ensayo: servidor HTTPS publicado con PostgreSQL y cola configurados; cuenta
de prueba autorizada; instalador actual en un Windows de prueba. No necesita Docker, Python
ni PostgreSQL en el equipo del usuario. Para simular fallos, usar un entorno de prueba y
coordinar cortes con su administrador; no interrumpir datos reales.

- **Inicio público**
  - Abrir el cliente con servidor configurado, sin sesión.
  - Confirmar que Inicio aparece y permite llegar a registro/acceso.
  - Abrir `#/dashboard` sin sesión: debe mostrar acceso, sin información financiera.
- **Consulta inicial de sesión**
  - Provocar fallo de red/503 durante GET `/api/auth/me/`.
  - En una ruta de aplicación debe aparecer aviso de comprobación y Reintentar conexión;
    no afirmar que la sesión se cerró ni mostrar el fallo como credenciales incorrectas.
  - Volver a Inicio: debe seguir disponible sin sesión.
  - Restablecer servicio y reintentar: sesión vigente se reconoce; 403 muestra acceso.
- **Cuentas para importar**
  - Con sesión y empresa, provocar fallo de la primera consulta de cuentas.
  - Confirmar aviso independiente y ausencia de opciones de cuentas conectadas.
  - Restablecer consulta: un reintento debe llenar cuentas manuales y retirar solo ese aviso.
  - Usuario viewer no debe disponer de escritura; el servidor debe rechazarla aunque se
    intente directamente. No interpretar una lista vacía como pérdida de movimientos.
- **Consulta de trabajos CSV/XML**
  - Provocar fallo temporal al consultar trabajos, luego restablecerlo.
  - Aviso de consulta se retira con respuesta exitosa; error de carga/confirmación permanece
    hasta una nueva operación o acción correspondiente.
  - Un 202 queda en cola hasta resultado terminal: no anunciar importación completada antes.
  - Cambiar empresa o salir durante una consulta: no deben aparecer datos de la anterior.
- **Conexión de escritorio**
  - Configurar un origen HTTPS inalcanzable en el entorno de prueba.
  - Verificar aviso con Reintentar, Configurar servidor y Cerrar aviso.
  - Cambiar a origen operativo y comprobar Inicio; al cambiar origen se elimina almacenamiento
    anterior. Reabrir cliente y comprobar persistencia de la dirección y sesión esperadas.
  - Página HTTP de error del proveedor puede cargar sin disparar el aviso nativo: verificar
    recuperación mediante menú Servidor → Reintentar. Esta limitación está documentada.
- **Reactivación de servicio gratuito**
  - Con servicio suspendido por el proveedor, abrir el cliente y registrar tiempo observado
    hasta disponibilidad. No prometer tiempo fijo ni disponibilidad continua.
  - Importar una muestra autorizada y comprobar el trabajo, movimientos y ausencia de
    duplicados tras repetirla. Comprobar XML y confirmar obligación por separado.

Registrar para cada caso: versión del instalador, fecha, URL de prueba, pasos, resultado real,
captura sin datos personales y si aprobó/falló. No copiar cookies, contraseñas, claves ni enlaces
de recuperación. No marcar V1 completa mientras estos resultados sigan pendientes.
