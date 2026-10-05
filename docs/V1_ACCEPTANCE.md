# Aceptación de la primera versión funcional

Estado: incompleta. Este listado conserva RF-01 a RF-16 y RNF de README/SPECS;
no declara cierre por tener CI verde. Respaldo diario excluido por decisión del usuario.

## Pasos de cierre

- [x] Publicar servidor HTTPS con base persistente, sin herramientas locales para el usuario:
  Render Free + Supabase. Evidencia: despliegue live y recorridos HTTP documentados en HOSTING_FREE.md.
- [x] Generar instalador Windows x64 con Inicio accesible sin sesión:
  Electron/NSIS en `desktop/release/session-isolation/`. Configuración del binario comprobada;
  no sustituye la prueba del usuario instalado.
- [ ] Instalar, iniciar, cerrar, reabrir y desinstalar en Windows limpio. Probar registro,
  CSRF/sesión, empresa, CSV/XLSX, XML, Mock Bank, obligaciones, conciliación y dashboard.
  No hay evidencia visual fiable: herramienta de navegador falla al iniciar en Windows.
- [ ] Completar entrega real de recuperación de contraseña (RF-01): integración HTTPS preparada,
  pero falta cuenta/clave/remitente Resend y comprobar recepción y reset de un solo uso.
  Sin dominio verificado, Resend de prueba limita destinatarios al correo de su propia cuenta.
  Integración local adicional: fallo HTTP 503 simulado conserva la tarea para reintentar;
  aceptación HTTPS posterior completa la tarea y borra argumentos privados. El enlace
  generado permite cambiar la contraseña una sola vez. Proveedor simulado: esta prueba
  no demuestra entrega ni recepción real en un buzón.
- [ ] Revisar aceptación de empresas/roles (RF-02), conectores sintéticos (RF-03/RF-16),
  importaciones (RF-04/RF-05), normalización/clasificación/correcciones (RF-06/RF-07/RF-08)
  con corpus representativo. Las pruebas de fixtures no demuestran exactitud general.
  La carga CSV/XLSX rechaza localmente extensión distinta, archivo vacío o tamaño superior
  a 2 MiB antes de consultar CSRF/enviar; el backend conserva su validación independiente.
  Pérdida de conexión al enviar advierte consultar trabajos antes de repetir, porque la
  recepción puede haber ocurrido. Controles se deshabilitan durante el envío; QA visual pendiente.
- [ ] Completar validación temporal del híbrido y recurrencias (RF-09/RF-10): implementación
  experimental y evaluación sintética existentes; falta corpus independiente y reconstrucción
  de evidencia pasada antes de evaluar datos reales corregidos después del corte.
  Se eliminan consultas por cada ocurrencia del GET de recurrencias: vínculos y pendientes
  se leen por lote, conservando filtros por empresa. Ensayo sintético de diez patrones:
  antes 84 consultas a 30 días y 264 a 90; después igual cantidad en ambos y máximo diez,
  con más de cien ocurrencias expandidas. Suite posterior: 209 pruebas, 204 aprobadas,
  5 omitidas. No certifica p95 remoto, concurrencia ni rendimiento visual.
- [ ] Validar pronósticos probabilísticos y confianza (RF-11/RF-15). Cuantiles experimentales
  y candidato de intervalos reservados existen; cobertura agregada sintética no demuestra
  calibración por perfil. Los límites corregidos no son P10/P90 calibrados ni probabilidad de déficit.
  Cobertura muestra las cuatro etapas BN-06 según amplitud observada por cuenta
  (0–29, 30–89, 90–364 y 365 días en su ventana anual), distinguiendo días activos.
  Las etiquetas no prueban completitud ni precisión y no cierran por sí solas RF-15.
- [ ] Verificar alertas, dashboard y gráficos exigidos (RF-12/RF-13/RF-14): escenarios contractuales,
  históricos, categorías y calendario implementados; riesgo probabilístico/factores y confianza
  deben cumplir el alcance original con evidencia, sin confundir umbral determinístico y probabilidad.
- [ ] Finalizar contratos OpenAPI de las operaciones restantes, cuerpos de error y ejemplos.
  El inventario sigue parcial; no se acepta como especificación completa para generar clientes.
  `forecast-runs` documenta envolvente, paginación, parámetros, roles, códigos de idempotencia
  e instantáneas versionadas `evidence`/`result`. Sus campos se contrastan con respuestas reales
  en `test_forecast_runs`, incluidas entradas de cuantiles de 270 días y 90 flujos futuros.
  El resultado interno ya documenta flujos diarios, alerta y las variantes de cuantiles
  `unavailable`/`experimental`, comprobadas con respuestas reales (incluido híbrido 90 días).
  Campos añadidos posteriormente son opcionales para leer ejecuciones antiguas. La evidencia
  interna describe flujos conocidos, digest, serie residual y recurrencias estimadas/vinculadas;
  este contrato no prueba calibración ni exactitud predictiva.
  Se corrigió el truncamiento de horizontes JSON fraccionarios: 30.5/60.75/90.01 devuelven
  400 sin guardar una ejecución. Suite local posterior: 203 pruebas, 198 aprobadas y 5 omitidas.
  La consulta `experimental-forecast` reutiliza el esquema del resultado y documenta
  parámetros, permisos y errores 400/403/404/409; campos actuales requeridos comprobados
  contra respuesta real. No guarda ejecuciones ni demuestra eficacia predictiva.
  Listado/creación/edición de obligaciones tienen campos, paginación, estados, entradas derivadas
  de serializers y errores documentados. La edición excluye referencia, dirección e importe
  pendiente; creación/listado se contrastan con respuestas reales. Conciliaciones/reversiones
  documentan campos, importe/UUID derivados del serializer y reintentos idempotentes, incluido
  repetir una conciliación ya revertida sin afectar el pendiente. Candidatos e historial por
  obligación documentan filtros, disponible, roles y paginación; prueba real comprueba reducción/
  restitución del disponible y lectura con rol lector. Instantáneas before/after por acción y
  otras operaciones aún requieren completar sus contratos.
  Ocho formularios (saldos/cobertura, conexiones, reglas, empresa, umbral, movimientos,
  perfil y recurrencias) comparten validación de HTTP/JSON/token CSRF antes de mutar.
  Helper comprobado con HTTP fallido, JSON null/malformado, token vacío y token válido;
  compilación aprobada. Falta reproducir fallos en la interfaz instalada.
  Empresas, salud y sugerencias de categoría documentan respuestas; pruebas contrastan campos,
  abstención y fallo de BD sin diagnóstico privado. Recurrencias GET/POST y desvinculación
  documentan estados, ocurrencias, revisión, materialización e idempotencia. Ninguna operación
  queda como inventario de rutas; esto no equivale a completar errores/ejemplos ni revisar
  todos los esquemas históricos. Se corrigió el pendiente candidato para serializar Decimal
  como cadena, comprobado contra JSON real. Suite posterior: 205 pruebas, 200 aprobadas, 5 omitidas.
  Errores de autenticación documentan 400/403/415/429 y 503 de recuperación; CSRF público
  puede responder HTML, mientras sesión DRF responde JSON. Pruebas reales contrastan 400,
  ambas formas de 403 y 415. Falta revisión equivalente de otras familias y ejemplos completos.
- [ ] Verificar accesibilidad, móvil web, tiempos de renderizado/p95, carga concurrente,
  disponibilidad controlada y seguridad conforme a los criterios del README/SPECS.
  HTTP 200 y una importación rápida no prueban estos requisitos.
  El dashboard ofrece una tabla desplegable de fecha/saldo para todos los puntos del
  escenario, con dos decimales, caption y encabezados de fila/columna. Es una alternativa
  textual al gráfico; compilación comprobada, recorrido real con Narrador aún pendiente.
  La matriz `tests.test_read_access_matrix` recorre las consultas y escrituras de empresa
  del inventario actual: exige rechazo de otra empresa y sesión ausente, incluso con cuerpo
  vacío. Se corrigió autorización previa a validación en saldo, cobertura y nombre de comercio.
  Suite local posterior: 199 pruebas, 194 aprobadas y 5 omitidas. No sustituye pruebas con
  objetos existentes ajenos, todos los roles, XSS, carga ni una auditoría ASVS completa.
  Ampliación posterior: saldo, cobertura, nombre de comercio y categoría rechazan IDs de
  objetos ajenos existentes bajo empresa propia y conservan los datos originales. Las 26
  escrituras también rechazan sesión real con cookie sin CSRF (403 con detalle CSRF), sin
  `force_authenticate`. Cuatro pruebas de la matriz aprobadas; faltan los demás objetos/roles.
  La ampliación financiera comprueba objetos ajenos existentes bajo empresa propia:
  lectura de candidatos, conciliaciones e historial, edición de obligación, conciliación
  con movimiento ajeno y reversión con pago ajeno (incluido anidarlo bajo obligación propia).
  Todos responden 404 y mantienen pendientes, descripción y pago sin revertir.
  Esta evidencia no sustituye la revisión de otras familias ni todos los roles.
- [x] Ensayar respaldo manual y restauración aislada sin Docker: 32 tablas, restricciones,
  migraciones y recorrido Client Django comprobados. Archivos privados fuera de Git;
  no acredita UI, cifrado ni copia externa. No activar respaldo diario.
- [ ] Consolidar manuales, matriz de evidencias, resultados de investigación y demostración
  académica. Notas históricas no deben presentarse como estado vigente.

## Acciones externas del usuario

- Para probar el cliente actual: ejecutar el instalador con Windows x64 e internet.
- Para cerrar correo: crear Resend Free y guardar clave/remitente en `.env.hosted`, sin compartir
  la clave en chat. Para otros destinatarios hará falta un dominio propio verificado.
- Para instalación limpia: disponer de Windows de prueba aislado; no sustituir esta prueba
  por el ejecutable desempaquetado del equipo de desarrollo.
- Para corpus/usabilidad: proporcionar datos autorizados o participantes de prueba según
  la metodología académica. No se exige banco real de producción para el sandbox V1.

El port Android/iOS sigue en V2; no se incorpora silenciosamente como requisito de V1.
