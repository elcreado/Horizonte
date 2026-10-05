# Horizonte: primera versión de escritorio funcional

Alcance acordado el 5 de octubre de 2026: primera versión utilizable de escritorio,
sin exigir todavía perfección ni cierre de todas las metas académicas y de producción.
El alcance ampliado y sus validaciones siguen registrados en `V1_ACCEPTANCE.md`.

## Cómo probarla sin Docker

- Instalar `desktop/release/session-isolation/Horizonte Setup 0.1.0.exe` en Windows x64.
- Abrir Horizonte y conectar con `https://horizonte-demo.onrender.com`.
- Inicio funciona sin sesión. Registrarse o acceder con una cuenta de prueba.
- Crear o seleccionar una empresa; utilizar datos sintéticos. Seguir `USER_MANUAL.md`
  para saldos, importaciones, obligaciones y calendario.
- Mantener conexión a internet. El backend y PostgreSQL están alojados; no instalar
  Docker, Python, Node, PostgreSQL ni Redis para usar este cliente.
- Para actualizar la interfaz alojada, usar Vista → Recargar. Los cambios del cliente
  Electron requieren otro instalador, pero las actualizaciones web no.

## Funciones disponibles

- Inicio público, registro, sesión y empresas con propietario, contador y lector.
- Importación CSV/XLSX, XML con revisión y Mock Bank con consentimiento/revocación.
- Clasificación y corrección de movimientos; obligaciones, conciliación y reversión.
- Dashboard, saldos diarios, calendario, alertas por umbral y registros históricos.
- Pronóstico híbrido y cuantiles experimentales, expresamente sin precisión garantizada.

## Evidencia de esta entrega

- Instalador x64 disponible; tamaño y SHA-256 coinciden con `DESKTOP_RELEASE.md`.
- Cliente empaquetado arrancó de nuevo con código 0 en perfil aislado: configurador,
  aislamiento de Node, permisos denegados y borrado de sesión persistente comprobados.
- Las tres pruebas de configuración de escritorio pasan.
- Backend alojado y base persistente operativos; recorridos HTTP y suite automatizada
  documentados en `V1_ACCEPTANCE.md`. El usuario ha confirmado funcionamiento de la aplicación.
- Esta evidencia no certifica instalación/desinstalación en Windows limpio ni revisión
  visual completa: la herramienta de navegador falla al aplicar ACL en este equipo.

## Limitaciones y acciones externas

- Render Free puede suspenderse por inactividad. La primera conexión puede tardar;
  esperar y reintentar. No hay funcionamiento financiero sin conexión.
- Recuperación por correo requiere configurar un proveedor y comprobar recepción real;
  todavía no está disponible como función alojada verificada. Para probar lo demás,
  no hace falta configurar correo ni credenciales bancarias reales.
- Instalador sin firma de editor. No desactivar las protecciones de Windows.
- Validaciones de precisión/calibración, accesibilidad completa, concurrencia,
  disponibilidad y seguridad de producción quedan para mejoras posteriores.
- Respaldo manual únicamente; no activar respaldo diario automático.
- El port móvil nativo pertenece a una segunda versión.

El paso externo necesario para probar escritorio es ejecutar el instalador en Windows
x64 con internet. `DESKTOP_ACCEPTANCE.md` ofrece un recorrido con datos sintéticos y
resultados esperados para reportar fallos concretos.
