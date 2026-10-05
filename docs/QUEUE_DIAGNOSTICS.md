# Diagnóstico administrativo de cola

Los resultados operativos de un entorno privado deben conservarse localmente, fuera de Git.
No publicar conteos ni marcas temporales de la cola alojada en este documento.

Con la configuración del entorno que se quiere inspeccionar:

```powershell
python backend/manage.py background_status
```

En modo `database`, informa conteos de pendientes, disponibles, ejecuciones, leases vencidos,
fallidos y completados, más fecha del pendiente más antiguo y última finalización.
Solo consulta: no reclama tareas, no envía correo y no imprime argumentos, enlaces ni usuarios.
La observación es global para administradores del entorno; no se expone como API a empresas.

No verifica un heartbeat ni demuestra worker vivo. Una tarea running con lease vencido puede
ser recuperada por `run_background`; un lease vigente puede corresponder a un proceso caído
que todavía no alcanzó su vencimiento. Una cola vacía no demuestra que el worker esté arrancado.
En modo Celery se informa que la herramienta no inspecciona sus workers.
Comprobar conectividad con la configuración alojada requiere cargar sus variables privadamente;
ejecutar el comando con la configuración local predeterminada no inspecciona Render/Supabase.
