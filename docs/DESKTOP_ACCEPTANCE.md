# Ensayo de aceptación del cliente Windows

Procedimiento pendiente de ejecución visual, no certificado de pruebas aprobadas.
Usar una empresa nueva sin otras cuentas, obligaciones ni conexiones. Los importes son COP.
Las fechas son fijas: no sustituirlas por la fecha actual del equipo.

## Preparación sin Docker

- Instalar `desktop/release/session-isolation/Horizonte Setup 0.1.0.exe` en Windows x64.
- Abrir Horizonte y conectar a `https://horizonte-demo.onrender.com`.
- Comprobar que Inicio aparece sin sesión. Si Render está despertando, esperar y usar
  Servidor → Reintentar. No hace falta instalar herramientas de desarrollo.
- Crear un usuario exclusivo de prueba y una empresa con NIT `SYNTHETIC-001`.
  Si ese NIT ya está ocupado en el servicio, crear otro y cambiar únicamente el NIT del
  proveedor del XML de ejemplo en una copia local; no usar una empresa ajena.
- Configurar una única cuenta manual con saldo **500.000**, moneda COP y corte **2026-10-05**.
- Registrar versión, Windows, hora, URL, paso y resultado. No incluir contraseñas en evidencias.

## Importación y persistencia

- Descargar «CSV de ejemplo» desde Importar movimientos y cargarlo en la cuenta manual.
  Debe completar con dos movimientos: +150.000 del 1 de septiembre y −45.000 del 2 de septiembre.
- Repetir exactamente el archivo: deben seguir existiendo dos movimientos, sin duplicados.
- En Histórico, septiembre muestra ingresos 150.000, egresos 45.000 y neto 105.000.
  El saldo declarado sigue siendo 500.000: la importación no lo recalcula.
- Cerrar y abrir Horizonte; comprobar persistencia de cuenta y movimientos.
- Probar un archivo CSV sin columna `amount`: debe rechazarse o terminar fallido, sin
  insertar movimientos parciales. No aceptar un estado «completado» para ese archivo.

## Factura, calendario y alerta

- Descargar el XML de ejemplo desde la sección de facturas. Cargarlo y revisar antes de
  confirmar: `DEMO-XML-001`, cobro 119.000, vencimiento **2026-10-15**, NIT de la empresa
  como proveedor. No es una factura válida para DIAN.
- Confirmar una vez. Debe existir un único cobro pendiente de 119.000. Repetir carga y
  confirmación no debe crear otro compromiso del mismo documento.
- Crear una obligación manual de pago por **700.000**, vencimiento **2026-10-20**,
  referencia `DESKTOP-QA-PAGO-001`; no conciliarla todavía.
- Como propietario, establecer umbral de liquidez en **100.000**.
- En horizonte 30 días: saldo inicial 500.000; cobros 119.000; pagos 700.000; vencidos 0.
  El saldo pasa a 619.000 el 15 de octubre y a **−81.000** el 20 de octubre.
- Primer déficit y primera fecha futura bajo el umbral: **2026-10-20**. Mínimo: **−81.000**;
  insuficiencia frente al umbral: **181.000**. Deben existir 30 puntos del 6 de octubre
  al 4 de noviembre, con 16 días proyectados bajo el umbral.
- Cambiar a 60/90 días: misma primera fecha y mínimo, con 46/76 días bajo el umbral
  respectivamente; los puntos deben ser 60/90. Sin más compromisos, el saldo final sigue −81.000.
- En Calendario, elegir octubre de 2026: día 15 un cobro 119.000 y día 20 un pago 700.000.
- Cancelar el pago manual: saldo final y mínimo futuro 500.000, pagos 0, sin déficit ni
  alerta bajo el umbral; el calendario no debe incluirlo. Reactivarlo recupera los resultados anteriores.
- Guardar la evaluación de alerta y consultarla tras reabrir. Una edición posterior del
  compromiso no debe modificar la evaluación histórica ya guardada.

## Sesión y límites

- Cerrar sesión: Inicio continúa disponible y los datos financieros requieren autenticación.
- Acceder con un segundo usuario sin membresía: la empresa del primero no debe aparecer.
- Probar lector y contador con membresías creadas por el propietario; el lector no modifica
  obligaciones y el contador no cambia el umbral reservado al propietario.
- Desconectar internet y usar Reintentar: debe presentarse un error recuperable; volver a
  conectar y comprobar datos. No afirmar que funciona sin conexión.
- Probar desinstalación en el equipo aislado y reinstalación. Los datos del servidor deben
  conservarse; no se garantiza que desinstalar elimine la sesión local. Cerrar sesión primero.

## Condiciones de cierre

- Con teclado: pulsar Tab al entrar muestra «Saltar al contenido principal»; activarlo
  lleva el foco al contenido sin cambiar la ruta ni cerrar la sesión. Al cambiar de pantalla,
  el foco pasa al contenido principal. Probar Tab/Mayús+Tab, Enter y Escape en formularios
  y diálogos, con un indicador de foco visible y sin atrapamientos.
- Con Narrador de Windows: comprobar que identifica la región principal y anuncia errores,
  estados de importación y cambios de pantalla. La compilación no acredita estas pruebas.

- Cada paso anterior necesita resultado y evidencia del cliente instalado; los ensayos HTTP
  y del configurador no sustituyen esta comprobación.
- Recuperación de contraseña se ensaya aparte cuando haya proveedor HTTPS configurado y
  destinatario permitido. La ausencia de correo no se marca como prueba aprobada.
- La prueba no certifica precisión del modelo probabilístico, carga concurrente, disponibilidad
  ni accesibilidad completa. Consultar `V1_ACCEPTANCE.md` para los demás requisitos.
- No programar respaldo diario; usar únicamente el procedimiento manual autorizado.
