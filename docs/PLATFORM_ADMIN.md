# Provisión y administración de plataforma

Actualmente no hay interfaz administrativa Django configurada. Los permisos owner/accountant/viewer
pertenecen a empresas y no conceden administración transversal de usuarios. El requisito de gestión
de plataforma sigue pendiente: no confundirlo con la administración de membresías de una empresa.

La API GET `/api/platform/users/` ofrece consulta paginada de 20 usuarios, por ID ascendente,
solo para sesión de usuario activo con `is_staff` e `is_superuser`. Devuelve ID, nombre, correo,
banderas de estado/privilegios y número de membresías; no contraseña/hash ni historial de acceso.
Es una consulta transversal de datos personales para administración autorizada. No permite
crear, borrar, activar o desactivar usuarios; no completa la gestión administrativa requerida.

React incorpora `#/platform`, con tabla, actualización y paginación. El enlace Administración
aparece en el dashboard cuando `/api/auth/me/` informa `platform_admin=true`; el endpoint de
usuarios comprueba permisos aunque se abra la ruta manualmente. Muestra errores 403 y cancela
consultas al salir. Backend y compilación aprobados; QA visual/teclado y provisión pendientes.

Comprobar provisión sin imprimir identificadores ni datos personales:

```powershell
.venv\Scripts\python.exe backend/manage.py platform_admin_status
```

Salida no cero indica que no existe un usuario activo con `is_staff` e `is_superuser`.
El diagnóstico local del 4 de octubre confirmó ausencia de esa cuenta. No modifica usuarios.
Incluso una comprobación positiva no demuestra UI, operaciones, auditoría ni recuperación.

Cuando el responsable prepare una cuenta propia, puede ejecutar interactivamente:

```powershell
.venv\Scripts\python.exe backend/manage.py createsuperuser
```

No incluir contraseña en argumentos, documentación ni instalador. En el servicio alojado,
ejecutar contra la conexión autorizada y migrada. No reutilizar la cuenta demo para administración.
La provisión por sí sola no habilita `/admin/`: requiere configuración adicional.

Pendientes para la interfaz: acceso reservado a administrador de plataforma, CSRF y límite
persistente de login, archivos estáticos, operaciones explícitas con auditoría, conservación
de invariantes de último propietario y pruebas de rechazo de usuarios de empresa. No registrar
tablas financieras con CRUD genérico que eluda validaciones de la aplicación.

Referencia de configuración: [administración Django](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/).
