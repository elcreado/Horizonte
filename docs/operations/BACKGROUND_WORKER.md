# Prueba y operación de la cola persistente

El alojamiento gratuito usa `BACKGROUND_MODE=database`: tareas y trabajos se guardan en
la misma base de datos. No requiere Redis ni Docker. La base y sus migraciones sí deben
estar disponibles. En producción se inicia desde `scripts/start-hosted.py`, junto a Gunicorn.

Para procesar como máximo una tarea disponible y terminar, desde la raíz del proyecto:

```powershell
$env:BACKGROUND_MODE = 'database'
.venv\Scripts\python.exe backend/manage.py run_background --once
```

En Render/Linux usar `python backend/manage.py run_background --once` con las variables
del servicio. Este comando **ejecuta la tarea**: puede importar archivos, sincronizar la fuente
o enviar recuperación de contraseña. Usarlo con los datos/cuentas de prueba autorizados.
No imprime contenidos financieros, destinatarios ni enlaces de recuperación.

- Si no hay tareas disponibles, termina sin esperar. No significa que no existan tareas
  retrasadas o con lease vigente.
- Las excepciones de una tarea se gestionan con los reintentos de la cola; salida del comando
  sin error no prueba que la tarea de dominio haya terminado correctamente. Revisar su estado
  en la aplicación y `BackgroundTask` en una consulta administrativa autorizada.
- Sin `--once`, el worker consulta periódicamente y espera diez segundos cuando no encuentra
  trabajo. SIGTERM/SIGINT interrumpen esa espera; una tarea ya iniciada termina su ejecución.
  El supervisor puede forzar su cierre tras veinte segundos.
- Un trabajo interrumpido puede recuperarse al vencer su lease de quince minutos. Máximo
  tres intentos, con espera progresiva de reintento. No garantiza entrega exactamente una vez
  para efectos externos como correo.
- Al dormir Render, no se procesa la cola. Al reactivarse, el supervisor vuelve a arrancarla.
  Los ensayos reales de suspensión y recuperación en PostgreSQL remoto siguen pendientes.

Las pruebas automatizadas ejecutan CSV mediante este comando, verifican una sola tarea por
invocación y ausencia de movimientos duplicados. Son pruebas locales; no certifican carga,
apagado Linux ni entrega real de correo.

También se verifica una intercalación controlada de intentos: vence el lease del primero y
un segundo intento recupera la tarea. El resultado tardío del primero no puede sobrescribir
ni la finalización del segundo ni su estado de reintento/payload. La prueba usa la base local
y ejecución anidada, no dos procesos PostgreSQL concurrentes; ese ensayo sigue pendiente.

Recuperación tiene prueba integrada HTTP con CSRF, mensaje persistente, comando worker,
correo en memoria y cambio de contraseña mediante el enlace generado. El token no se puede
reutilizar y el mensaje terminal elimina sus argumentos. También se comprueba rechazo 503
genérico al fallar inserción, sin mensaje ni correo. El backend de correo en memoria evita
envíos externos: la prueba no demuestra entrega mediante Resend ni funcionamiento remoto.
