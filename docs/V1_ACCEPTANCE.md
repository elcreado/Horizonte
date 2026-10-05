# Aceptación de la primera versión funcional

Estado: incompleta. Este listado conserva RF-01 a RF-16 y RNF de README/SPECS;
no declara cierre por tener CI verde. Respaldo diario excluido por decisión del usuario.

## Pasos de cierre

- [x] Publicar servidor HTTPS con base persistente, sin herramientas locales para el usuario:
  Render Free + Supabase. Evidencia: despliegue live y recorridos HTTP documentados en HOSTING_FREE.md.
- [x] Generar instalador Windows x64 con Inicio accesible sin sesión:
  Electron/NSIS en `desktop/release/hosted/`. Configuración del binario comprobada;
  no sustituye la prueba del usuario instalado.
- [ ] Instalar, iniciar, cerrar, reabrir y desinstalar en Windows limpio. Probar registro,
  CSRF/sesión, empresa, CSV/XLSX, XML, Mock Bank, obligaciones, conciliación y dashboard.
  No hay evidencia visual fiable: herramienta de navegador falla al iniciar en Windows.
- [ ] Completar entrega real de recuperación de contraseña (RF-01): integración HTTPS preparada,
  pero falta cuenta/clave/remitente Resend y comprobar recepción y reset de un solo uso.
  Sin dominio verificado, Resend de prueba limita destinatarios al correo de su propia cuenta.
- [ ] Revisar aceptación de empresas/roles (RF-02), conectores sintéticos (RF-03/RF-16),
  importaciones (RF-04/RF-05), normalización/clasificación/correcciones (RF-06/RF-07/RF-08)
  con corpus representativo. Las pruebas de fixtures no demuestran exactitud general.
- [ ] Completar validación temporal del híbrido y recurrencias (RF-09/RF-10): implementación
  experimental y evaluación sintética existentes; falta corpus independiente y reconstrucción
  de evidencia pasada antes de evaluar datos reales corregidos después del corte.
- [ ] Validar pronósticos probabilísticos y confianza (RF-11/RF-15). Cuantiles experimentales
  y candidato de intervalos reservados existen; cobertura agregada sintética no demuestra
  calibración por perfil. Los límites corregidos no son P10/P90 calibrados ni probabilidad de déficit.
- [ ] Verificar alertas, dashboard y gráficos exigidos (RF-12/RF-13/RF-14): escenarios contractuales,
  históricos, categorías y calendario implementados; riesgo probabilístico/factores y confianza
  deben cumplir el alcance original con evidencia, sin confundir umbral determinístico y probabilidad.
- [ ] Finalizar contratos OpenAPI de las operaciones restantes, cuerpos de error y ejemplos.
  El inventario sigue parcial; no se acepta como especificación completa para generar clientes.
  `forecast-runs` documenta ahora envolvente, paginación, parámetros, roles y códigos de
  idempotencia; sus instantáneas `evidence`/`result` versionadas siguen con esquema interno
  pendiente. Los campos exteriores se contrastan con respuestas reales en `test_forecast_runs`.
  El resultado interno ya documenta flujos diarios, alerta y las variantes de cuantiles
  `unavailable`/`experimental`, comprobadas con respuestas reales (incluido híbrido 90 días).
  Campos añadidos posteriormente son opcionales para leer ejecuciones antiguas. La evidencia
  interna sigue pendiente; este contrato no prueba calibración ni exactitud predictiva.
- [ ] Verificar accesibilidad, móvil web, tiempos de renderizado/p95, carga concurrente,
  disponibilidad controlada y seguridad conforme a los criterios del README/SPECS.
  HTTP 200 y una importación rápida no prueban estos requisitos.
  La matriz `tests.test_read_access_matrix` recorre las consultas y escrituras de empresa
  del inventario actual: exige rechazo de otra empresa y sesión ausente, incluso con cuerpo
  vacío. Se corrigió autorización previa a validación en saldo, cobertura y nombre de comercio.
  Suite local posterior: 199 pruebas, 194 aprobadas y 5 omitidas. No sustituye pruebas con
  objetos existentes ajenos, todos los roles, XSS, carga ni una auditoría ASVS completa.
  Ampliación posterior: saldo, cobertura, nombre de comercio y categoría rechazan IDs de
  objetos ajenos existentes bajo empresa propia y conservan los datos originales. Las 26
  escrituras también rechazan sesión real con cookie sin CSRF (403 con detalle CSRF), sin
  `force_authenticate`. Cuatro pruebas de la matriz aprobadas; faltan los demás objetos/roles.
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
