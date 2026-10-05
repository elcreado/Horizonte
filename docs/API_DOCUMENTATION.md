# Documentación API: inventario parcial

`openapi-inventory.json` registra las rutas reales de Django en formato OpenAPI 3.0.3.

Historial de alertas GET/POST documentado con paginación de 10, evidencia congelada,
resultado determinístico del umbral y distinción 200 reutilizada/201 creada. Solo propietario
y contador guardan evaluaciones; todos los roles consultan. No representa probabilidad de déficit.

Auditoría GET `/api/companies/{company_id}/audit/`: páginas de 20 registros, filtro exacto
de acción, orden fecha/ID descendente y acceso exclusivo para propietario/contador.
Los snapshots before/after dependen del evento y no tienen un esquema uniforme.

El histórico GET `/api/companies/{company_id}/history/` documenta sus doce meses,
importes decimales como texto, categorías, primera fecha anulable y errores 403/404/409.
La respuesta diferencia meses sin registros y mes de corte parcial; no interpreta el neto
como saldo bancario. El contrato permite consulta a todos los roles de la empresa.

Los contratos de equipo GET/POST, miembro PATCH/DELETE y nombre de empresa PATCH
incluyen entradas derivadas de serializadores, campos de respuesta, páginas de 20 miembros,
capacidades por rol y protección del último propietario activo. Mutaciones reservadas a
propietarios; no se envían invitaciones ni se eliminan datos financieros al retirar membresía.
Las respuestas exitosas están descritas; los cuerpos detallados de errores aún están pendientes.
Actualmente contiene 48 rutas y 61 operaciones, identificadores únicos, parámetros de ruta,
distinción entre acceso público y cookie de sesión, y cabecera CSRF para métodos mutantes.

```powershell
.venv\Scripts\python.exe backend/manage.py export_api_inventory
```

Las pruebas detectan diferencias entre el archivo guardado y las rutas/métodos actuales.
Regenerar y revisar cuando cambie la API. No se consultan datos financieros ni servicios externos.

- Inicio `/` es público y no forma parte del inventario `/api/`.
- Obtener el token mediante GET `/api/auth/csrf/`; conservar cookies y enviar `X-CSRFToken`
  junto a un Origin permitido en operaciones mutantes. Las cookies de sesión son HttpOnly.
- El login/registro establece sesión. Las rutas financieras además requieren membresía y
  autorización de rol; un ID de empresa no autoriza acceso por sí mismo.
- Los endpoints públicos mutantes conservan CSRF y límites de intentos. Público no significa
  escritura sin protección ni acceso financiero anónimo.
- No hay URL remota publicada en el contrato; el frontend usa el mismo origen del backend.

Contratos de campos/respuesta exitosa implementados para CSRF, me, login, logout, recuperación
y reset, registro, consulta/actualización de perfil y creación de empresas. Los campos toman
longitudes, obligatoriedad, patrones, fechas y precisión decimal de sus serializadores; también se
documentan validadores adicionales y límites. Logout 204 no declara cuerpo. Errores mantienen
respuesta genérica: sus formatos y códigos específicos requieren ampliación.

Saldo PATCH y cobertura POST de cuentas manuales incluyen entrada derivada de sus
serializadores, salida 200 con fechas de cobertura anulables y códigos 400/403/404/409.
Documentan permisos owner/accountant, conflicto de cuenta conectada, límite temporal
de cobertura y retirada de cobertura al cambiar el corte. La confirmación del usuario no
demuestra la integridad del historial. Usan `banking-fields-documented`; los cuerpos de
error todavía no tienen esquemas completos. En JSON enviar `confirmed` como booleano;
para importes decimales se recomienda cadena para conservar precisión.

Importación bancaria GET/POST incluye formulario multipart (`account_id`, `file`), salida
202 del trabajo y listado de los últimos 20 trabajos. Estados y formatos proceden del modelo.
202 significa aceptado para procesamiento, no completado; consultar GET y comprobar
`status`, `created_count`, `duplicate_count` y `error`. Los originales no aparecen en la API.
Se documentan extensión CSV/XLSX, UTF-8, 2 MiB, límite de filas validado por el worker,
cuenta manual, roles y errores 400/403/404/409/503. No hay paginación en este listado.

Consulta GET de cuentas documenta identificación, vínculo de conexión anulable, moneda COP,
saldo decimal en cadena, corte y cobertura anulable. `can_import` indica capacidad por rol;
las cuentas conectadas conservan sus restricciones de fuente. No tiene paginación ni orden
garantizado. El saldo se serializa explícitamente en texto para evitar pérdida de céntimos
por conversión a float en JSON; la prueba del importe máximo requiere PostgreSQL.

Comercios GET documenta paginación de 20, orden por nombre/ID, conteo, enlaces de página,
capacidad `can_edit` y campos del comercio. PATCH de nombre documenta entrada de 250
caracteres derivada del serializador, salida 200 y errores 400/403/404. Usa
`merchant-fields-documented`. Cambia la etiqueta visible y conserva alias e identidad;
no representa una operación de consolidación. Los esquemas completos de error siguen pendientes.

Movimientos GET y categoría PATCH usan `movement-fields-documented`. Se documentan importes
en texto, comercio anulable, opciones según signo, capacidad de edición y veinte filas por página
en orden fecha/ID descendente. No hay filtros adicionales implementados. PATCH requiere categoría;
`remember` es booleano JSON opcional false, con regla por empresa/descripción/dirección y rechazo
de reglas para cero. La corrección registra cada solicitud aceptada; no se promete auditoría
idempotente como en el cambio de nombre de comercio. Cuerpos de error completos pendientes.

Consulta de usuarios de plataforma documenta salida paginada, campos personales/privilegios,
orden y requisito de superusuario activo staff (`platform-fields-documented` y
`x-required-role`). La cookie de sesión por sí sola no autoriza esta consulta transversal.
Sin escrituras ni contraseñas/hashes en la respuesta; errores 403/404 descritos.

Importación XML GET/POST documenta carga multipart de un archivo, UTF-8, 2 MiB,
202 con ID/estado y consulta de últimos veinte trabajos con factura anulable/duplicado/error.
Usa `invoice-import-fields-documented`. La carga no valida inmediatamente el documento ni
crea obligación; revisión y confirmación siguen separadas. Errores 400/403/404/503 descritos;
esquemas completos de error pendientes.

Confirmación XML POST tiene ahora entrada documentada con fecha/pendiente decimal y mínimo
cero del serializador. Describe límite al importe pagadero, fecha no anterior a emisión,
200 si ya estaba confirmada y 201 al crear obligación. Ambas respuestas documentan `invoice_data`:
identidad/CUFE, partes/NIT, fechas, importes y vínculo/pendiente/cancelación. Listado GET incluye
ese mismo esquema, paginación de veinte, orden descendente y `can_edit`. Usan
`invoice-fields-documented`. Una factura ya vinculada no vuelve a validar el cuerpo de confirmación.
Errores con cuerpos completos siguen pendientes.

Vínculo manual XML GET/POST documenta candidatas paginadas, requisitos de compatibilidad,
ID positivo derivado del serializador, respuesta de factura y repetición del mismo vínculo.
Usa `invoice-link-fields-documented`. Crear un vínculo no crea otro compromiso. La lista
de candidatas no verifica equivalencia comercial; el usuario debe revisar la selección.

Reglas de clasificación GET/DELETE documentan campos, paginación/orden, capacidad por rol
y eliminación auditada sin modificar categorías existentes. DELETE no requiere cuerpo y
devuelve 204 sin contenido; CSRF sigue requerido. Usan `classification-rule-fields-documented`.

**Pendiente:** cuerpos JSON/multipart financieros, campos, validaciones, códigos de respuesta específicos,
paginación/filtros y ejemplos de todos los endpoints. Las respuestas genéricas y extensiones
`x-contract-status` / `x-request-schema-pending` marcan esa ausencia; las diez operaciones de
autenticación cubiertas usan `auth-fields-documented`. No usar este inventario
para generar un cliente completo o afirmar que el entregable OpenAPI está terminado.

El inventario excluye HEAD/OPTIONS implícitos. La autorización por roles, throttles y comportamiento
financiero debe verificarse mediante contratos y pruebas, no se infiere del archivo de rutas.

Formato basado en la [especificación oficial OpenAPI 3.0.3](https://spec.openapis.org/oas/v3.0.3.html).
## Contrato de Mock Bank

El inventario incluye campos de consulta de conexiones/jobs, autorización `provider=mock`
y `consent=true`, sincronización 202 y revocación 200. Documenta roles owner/accountant,
conflictos 409, indisponibilidad 503, alcance sintético y diferencia entre aceptación y
ejecución. Crear una conexión devuelve `{connection, job}`, no un ID en la raíz.
El contrato no acredita integración con un banco externo; los cuerpos detallados de error
y contratos restantes del inventario siguen pendientes. Exportación y siete pruebas de
inventario aprobadas después del cambio.
