# Horizonte: resumen de estado y pendientes

Revisión del alcance académico: **15 de octubre de 2026**. Avance web actualizado el **16 de octubre de 2026**. Alcance base: objetivos,
RF-01 a RF-16, RNF-01 a RNF-10 y entregables de [README](../README.md) y
[SPECS](../SPECS.md). No se modifican ni se dan por cumplidas las metas originales.

## Resumen ejecutivo

**Prioridad posterior acordada:** centrarse en una aplicación web útil y presentable,
dejando escritorio y Android/iOS pendientes. El [plan de demostración](PLAN_DEMO_FUNCIONAL.md)
documenta el alta manual ya implementada y la estimación inicial basada en siete días completos confirmados. La evidencia vigente está en [IMPLEMENTATION_STATUS](IMPLEMENTATION_STATUS.md).
La matriz inferior conserva el alcance completo, pero no fija por sí sola el orden de esta etapa.

Existe una **primera versión de escritorio funcional para pruebas**: Electron/NSIS en
Windows x64 consume React y Django alojados, con PostgreSQL en Supabase. Inicio es público;
hay sesiones, empresas/roles, importaciones, Mock Bank, obligaciones, conciliaciones,
calendario y dashboard. El usuario final necesita Windows e internet, **sin Docker local**.

Esto no equivale al cumplimiento completo del proyecto académico. Las brechas principales
son recuperación real por correo, aceptación del instalador en Windows limpio, validación
predictiva y probabilística, administración ampliada, contrato API completo y comprobaciones
de rendimiento, accesibilidad, disponibilidad y seguridad. Parte del trabajo falta implementarlo;
otra parte existe pero aún necesita evidencia de aceptación.

Se respeta la decisión de **presupuesto inicial 0 USD y respaldo manual únicamente**.
No se propone reactivar respaldos diarios, ni hacer llamadas para impedir la suspensión.
Android/iOS continúa como V2; no bloquea la entrega de escritorio inicial.

## Qué evidencia respalda este informe

- Código inspeccionado: `backend/apps`, `backend/config`, `frontend/src`, `desktop`,
  `compose.yaml`, scripts y `.github/workflows/ci.yml`.
- Build React/TypeScript y las tres pruebas de configuración de escritorio aprobados
  de nuevo en esta revisión. Backend: 215 pruebas, 210 aprobadas y 5 omitidas con SQLite;
  migraciones sin cambios. La primera ejecución restringida encontró errores de permisos
  al limpiar temporales; la repetición autorizada fuera del sandbox pasó.
- Existe configuración CI con SQLite, PostgreSQL 16, frontend y pruebas Node del escritorio;
  esta última no instala Electron ni ejecuta la interfaz.
- Evidencia histórica del 5 de octubre: servicio Render operativo, recorridos HTTP con
  sesión/CSV/XML/Mock Bank, arranque empaquetado, respaldo/restauración aislada y mediciones
  HTTP limitadas. Se conserva en documentación de operación y aceptación.
- **No se ha certificado de nuevo el servicio remoto, el instalador completo ni una sesión
  visual el 15 de octubre.** Las pruebas locales no prueban su disponibilidad actual.
- La carpeta no versionada `Proyecto/` contiene documentos/plantillas/modelos del usuario:
  permanece intacta y sus DOCX/ZIP no se han auditado como entregables académicos terminados.

Estados usados: **implementado** = hay código y pruebas del comportamiento;
**parcial** = falta parte del requisito o su validación; **pendiente** = falta el entregable
o no se encontró evidencia suficiente. No se calcula un porcentaje artificial de avance.

## Objetivos planteados

| Objetivo | Estado y brecha que falta cerrar |
|---|---|
| General: integrar finanzas y anticipar déficit mediante un híbrido | Parcial. Producto utilizable con datos sintéticos e híbrido experimental; falta demostrar eficacia con datos independientes y resultados predictivos validados. |
| OE-1: arquitectura modular, segura y extensible | Implementada como base Django/React, conectores y cola. Falta validación integral de seguridad y operación ante fallos. |
| OE-2: ETL asíncrono, normalización, deduplicación y clasificación | Implementado para CSV/XLSX/XML/Mock. Falta corpus representativo, medición de precisión/cobertura y validación de casos adversos. |
| OE-3: modelo híbrido de obligaciones y series temporales | Implementación experimental disponible. Falta validación temporal independiente y reconstrucción fiable de la información disponible en cada corte histórico. |
| OE-4: comparar Naive, ARIMA, Prophet e híbrido | Hay baselines, rolling-origin y evaluación ARIMA sobre datos sintéticos. No se encontró implementación/evaluación Prophet: evaluarlo o justificar formalmente su exclusión; no declararlo comparado. |
| OE-5: P10/P50/P90 y alertas explicables | Parcial. Cuantiles experimentales y alertas por obligaciones/umbral; faltan calibración por perfil, riesgo probabilístico y validación de comprensión del usuario. |
| OE-6: ASVS, OAuth/PKCE y cifrado | Sesión + CSRF y controles de aislamiento implementados; threat model disponible. Falta matriz ASVS y pruebas; OAuth/PKCE y ciclo de secretos de un proveedor externo siguen sin integrarse. No sustituir sesión de aplicación por OAuth sin necesidad. |

## Requisitos funcionales

| ID | Estado comprobado y pendiente concreto |
|---|---|
| RF-01 | Parcial. Registro/login/logout/perfil y reset de un solo uso implementados; falta proveedor/remitente y recepción real del correo alojado. |
| RF-02 | Parcial. Empresas y roles propietario/contador/lector implementados. Administrador de plataforma tiene consulta restringida de usuarios; falta gestión ampliada y auditable de usuarios/empresas si se conserva ese actor original. No asumir que ser administrador permite leer finanzas ajenas. |
| RF-03 | Implementado en Mock Bank: consentimiento, saldos, sincronización/revocación. No hay integración externa bancaria real; no se exige banca de producción para el sandbox inicial. Si se promete sandbox de proveedor, falta contratar/conectar ese entorno. |
| RF-04 | Implementado CSV/XLSX, cola, idempotencia y límites de archivo. Falta aceptación visual con archivos representativos y fallos de conexión/worker. |
| RF-05 | Implementado XML UBL, emitida/recibida, revisión de pendiente y vínculo único con obligación. Falta corpus documental más amplio. No valida firma ni certificación DIAN; API de proveedor no es obligatoria si XML satisface el alcance elegido. |
| RF-06 | Parcial. Normalización y comercios/alias disponibles; falta medir resolución de comercios bancarios representativos. No hay evidencia de resolver genéricamente todos los ejemplos del requisito. |
| RF-07 | Reglas y sugerencias TF-IDF con abstención implementadas. Falta demostrar cobertura y exactitud de clasificación en corpus etiquetado independiente. |
| RF-08 | Correcciones, reglas recordadas por empresa y auditoría implementadas. Falta evaluación longitudinal del aprendizaje, sin mezclar empresas ni incorporar etiquetas futuras. |
| RF-09 | Detección semanal/mensual, revisión y materialización/vínculos implementados. Falta validar precisión/recall, cambios de patrón y falsos positivos en corpus independiente. |
| RF-10 | Escenario determinístico y métodos Naive/estacional/SES/híbrido disponibles a 30/60/90 días. Falta validar eficacia del híbrido y coherencia en distintos perfiles. El dashboard contractual no debe presentarse como P50. |
| RF-11 | Parcial. P10/P50/P90 experimentales y candidato offline de intervalos. Falta calibración y evaluación por perfil/horizonte. Una banda no acredita probabilidad de déficit. |
| RF-12 | Parcial. Umbral, fecha de déficit, días bajo umbral, saldo mínimo y pagos hasta el déficit explicados. Falta nivel de riesgo `low/medium/high` con metodología explícita y evaluación de sus factores; la explicación actual no es riesgo probabilístico validado. |
| RF-13 | Dashboard de saldos COP, cobros/pagos y escenario de liquidez implementado. Falta aceptar visualmente el recorrido y completar la interpretación del riesgo según RF-12. |
| RF-14 | Parcial. Gráficos de proyección, banda experimental, ingresos/egresos, categorías y calendario; tablas CxC/CxP/recurrencias/alertas disponibles. Falta serie de saldo histórico real verificada: el histórico mensual actual muestra flujos y no saldos bancarios. Revisar si se exigen gráficos específicos además de tablas para todas las vistas enumeradas. |
| RF-15 | Parcial. Cuatro etapas de amplitud observada y avisos de datos insuficientes. Falta demostrar confianza predictiva; dos extremos temporales no prueban historial completo ni exactitud. |
| RF-16 | Implementado procesamiento asíncrono de importaciones y Mock Bank. Facturas por carga XML, no sincronización periódica con proveedor. Falta ensayo de concurrencia y recuperación real durante cargas en el alojamiento. |

## Requisitos no funcionales

| ID | Estado comprobado y pendiente concreto |
|---|---|
| RNF-01: secretos | No se incluyen credenciales de BD en Electron; HTTPS, sesión HttpOnly/CSRF y variables de servidor. Falta auditoría de secretos/logs/retención; el ciclo de tokens bancarios cifrados de proveedor real no está implementado. No confundir archivos locales privados con cifrado. |
| RNF-02: disponibilidad ≥99 % | No acreditada. Definir ventana de ensayo, monitorización y registro de caídas. Render Free admite suspensión; no prometer disponibilidad permanente con la evidencia existente. |
| RNF-03: dashboard <2 s | No acreditado de extremo a extremo. Hay muestras HTTP secuenciales calientes de aproximadamente 0,4–0,6 s; faltan dataset, concurrencia, p95 representativo, arranque frío y renderizado de interfaz. |
| RNF-04: no bloquear web | Arquitectura asíncrona implementada. Falta medir navegación/consultas mientras se importan archivos o sincroniza en el servicio real. |
| RNF-05: escalabilidad de workers | Cola con leases, reintentos y pruebas PostgreSQL de concurrencia. Falta ensayo operativo de varios workers y recuperación; despliegue gratuito actual no demuestra escalado horizontal en producción. |
| RNF-06: trazabilidad | Jobs y auditorías instrumentados. Falta revisar exhaustivamente usuario/fuente/fechas/errores en cada operación y definir retención sin datos sensibles en logs. |
| RNF-07: aislamiento | Amplia matriz de sesiones/roles y objetos ajenos; no es garantía absoluta. Ampliar cobertura de objetos/roles, casos de concurrencia y auditoría de seguridad. |
| RNF-08: recuperación | Respaldo manual y restauración aislada ya ensayados. Falta cifrado, retención, copia externa y ensayo de fallos. Respaldo diario excluido expresamente: no es una tarea pendiente. |
| RNF-09: portabilidad | Instalador Windows para consumo sin Docker disponible. Compose solo contiene PostgreSQL/Redis: no es un despliegue completo reproducible de frontend/backend/workers en contenedores. Falta completar ese paquete si se mantiene el entregable Docker Compose original; no es requisito para probar el escritorio. |
| RNF-10: accesibilidad/responsive | CSS responsive, tablas y foco/atajo de contenido implementados. Faltan teclado/Narrador, zoom, contraste y tamaños móviles con evidencia visual; compilar no prueba accesibilidad. |

## Reglas de negocio y entregables

- BN-01 a BN-05 y BN-07/08 tienen implementación para el sandbox: no transferencias,
  consentimiento, deduplicación, factura distinta de cobro, correcciones, horizontes y cola.
  Mantener pruebas de regresión y completar aceptación visual. BN-06 sigue parcial por RF-15.
- Entregables 2–6 y 13: frontend, backend, BD, ETL, motor y pruebas presentes; el motor
  conserva límites experimentales. Presencia de código no demuestra cierre de todos los RF.
- Entregable 7: reporte sintético de 100 empresas ×24 meses y generador presentes;
  los archivos generados son locales y debe prepararse su distribución/reproducción final.
- Entregable 8: reportes de experimentos presentes; falta corpus independiente, comparación
  completa acordada y conclusiones sin extrapolar resultados sintéticos a empresas reales.
- Entregables 9–11: threat model, manual de usuario y manual técnico presentes; actualizar
  junto a cada cambio y validar que un tercero puede seguirlos.
- Entregable 12: completar despliegue reproducible de toda la aplicación si sigue exigido;
  Compose actual levanta dependencias, no todos los componentes.
- Entregable 14: OpenAPI todavía parcial en errores, ejemplos y algunos snapshots históricos.
  Tener todas las rutas inventariadas no lo convierte en un contrato completo para clientes.
- Entregable 1: documento final de tesis, bibliografía y demostración académica no acreditados
  por este análisis de código. Revisar por separado los archivos académicos del usuario y
  modelos/diagramas frente al esquema vigente. No se movieron ni se borraron esos originales.

## Criterios de éxito del MVP

- **10.000 transacciones sin degradación relevante:** hay límite y ensayo previo de importación;
  falta definir degradación admisible y medir mientras se usa la interfaz con carga representativa.
- **Clasificar automáticamente al menos el 80 %:** no acreditado en corpus independiente.
  Medir cobertura automática y exactitud por separado; no convertir abstenciones en aciertos.
- **Idempotencia, corrección manual, XML, forecast 30/60/90 y procesamiento asíncrono:**
  implementados y probados en escenarios delimitados; falta aceptación integral del instalador.
- **Detectar déficit y explicar alertas:** implementado para obligaciones conocidas;
  no demuestra anticipación estadística ni explicación del riesgo probabilístico completo.
- **Aislamiento y auditoría:** controles/pruebas presentes; completar auditoría transversal,
  no prometer garantía absoluta por una suite verde.
- El plan académico de 24 semanas y los porcentajes sujetos al piloto son planificación,
  no evidencia de ejecución. Estado del arte, referencias regulatorias y bibliografía deben
  revisarse con fuentes primarias al cerrar la tesis; no se han revalidado en este informe.

## Próximos pasos, en orden

1. **Escritorio aplazado: retomar aceptación después de estabilizar la web.**
   - [ ] Instalar/abrir/cerrar/reabrir/desinstalar en Windows limpio; registrar versión y resultado.
   - [ ] Recorrer Inicio sin sesión → registro/login → empresa → CSV/XLSX/XML/Mock →
     obligaciones/conciliación → dashboard → logout, con [caso esperado](acceptance/DESKTOP_ACCEPTANCE.md).
   - [ ] Ensayar corte de internet, servicio dormido, reintento y persistencia de sesión.
2. **Resolver funciones incompletas de uso.**
   - [ ] Configurar correo y comprobar recepción, vencimiento y uso único del enlace.
   - [ ] Completar administración de plataforma según RF-02 o acordar formalmente su alcance.
   - [ ] Completar saldo histórico real y definir los gráficos que faltan de RF-14.
   - [ ] Completar riesgo/factores de RF-12 con reglas explicables y sin fingir calibración.
3. **Cerrar la parte predictiva y académica.**
   - [ ] Preparar corpus independiente autorizado y etiquetas fechadas para clasificación/recurrencias.
   - [ ] Reconstruir evidencia disponible al corte y evaluar modelos sin información futura.
   - [ ] Calibrar/evaluar cuantiles y cold start por perfil y horizonte.
   - [ ] Evaluar Prophet o justificar su cambio de alcance; consolidar resultados y tesis.
4. **Cerrar calidad y operación.**
   - [ ] Medir rendimiento/concurrencia/disponibilidad y accesibilidad con condiciones explícitas.
   - [ ] Completar ASVS y revisión de dependencias/privacidad/secretos.
   - [ ] Completar OpenAPI y despliegue reproducible; revisar distribución/firma/actualización.
   - [ ] Completar política de respaldo manual: cifrado, retención y recuperación aislada.
5. **V2, después de estabilizar lo anterior.**
   - [ ] Port Android/iOS y QA en dispositivos; backend HTTPS compartido.
   - [ ] Proveedor financiero/facturación autorizado, consentimiento y tokens seguros.
   - [ ] Notificaciones, observabilidad y actualizaciones de cliente. Ver [roadmap](ROADMAP_ENTREGABLES.md).

## Qué requiere acciones externas del usuario

- **Prueba básica:** Windows x64, internet e instalar el ejecutable. No requiere Docker,
  claves bancarias, Redis, Python ni Node en el equipo de uso.
- **Correo real:** cuenta de proveedor, credenciales guardadas de forma privada, remitente
  permitido y buzón de prueba. Si exige dominio propio o pago, no activarlo sin autorización.
- **Windows limpio:** equipo o VM aislada para aceptación; no equivale al equipo de desarrollo.
- **Investigación/usabilidad:** datos autorizados o corpus sintético independiente y participantes;
  decidir formalmente cambios en objetivos académicos, no eliminarlos por conveniencia.
- **Banca externa y móvil V2:** accesos del proveedor y herramientas/dispositivos de compilación;
  verificar requisitos y costes al ejecutar esa fase. No son requisitos de uso de la V1.

## Documentación ordenada en esta revisión

- Guías vigentes y resumen en la raíz de `docs/`, con [índice](README.md).
- `desktop/`, `acceptance/`, `operations/`, `security/`: referencia por tarea.
- `research/`: métodos y resultados experimentales; se conservan, no son basura documental.
- `archive/2026-10-05/`: cortes originales de estado, pruebas, manual técnico, despliegue,
  roadmap y revisión que mezclaban etapas. Llevan aviso de archivo y no son instrucciones vigentes.
- Se actualizan enlaces/rutas y las salidas predeterminadas de comandos de investigación
  para que los reportes nuevos se guarden en `docs/research/`.
