# Roadmap de implementación: dificultad, paralelismo y bloqueos

Fecha: **16 de octubre de 2026**. Objetivo actual: una **aplicación web útil y presentable**
que demuestre la idea con datos sintéticos y permita registrar transacciones manualmente.
Escritorio y Android/iOS están aplazados. Presupuesto inicial 0 USD; respaldo manual únicamente.

Referencias: [plan de demo](PLAN_DEMO_FUNCIONAL.md), [matriz de objetivos y requisitos](ESTADO_Y_PENDIENTES.md),
[convenciones](../CODESTYLE.md) y [pruebas](TESTING.md).

Este documento conserva la planificación del 16 de octubre anterior a la implementación. Para el estado actual consultar [IMPLEMENTATION_STATUS](IMPLEMENTATION_STATUS.md). Sus casillas no son una matriz vigente.
Organiza paquetes delegables a distintos agentes; **no se han iniciado agentes ni implementaciones**.

## Cómo interpretar el orden

- **Dificultad y prioridad no son lo mismo.** Las tablas están ordenadas de fácil a difícil;
  el orden de ejecución lo determinan las dependencias y las oleadas siguientes.
- Dificultad 1: documentación/textos; 2: cambios locales acotados; 3: contratos/interfaz;
  4: integridad financiera e integración; 5: investigación o cambios estructurales amplios.
- Una dependencia indicada es **obligatoria**: si aparecen varias, deben terminar **todas**.
- «Puede empezar» no significa «puede darse por terminado». Un formulario con respuestas
  simuladas permite avanzar en diseño, pero no acredita que guarde en el servidor.
- Para terminar una tarea hacen falta cambios revisables, comprobaciones pertinentes y evidencia
  del criterio de aceptación. No basta que un agente diga que terminó o que el build pase.

## Base que ya existe y no hay que rehacer

- Inicio público, registro/login/logout, empresas y roles propietario/contador/lector.
- El alta de empresa **ya crea una cuenta manual con saldo y corte** en
  `backend/apps/accounts/onboarding.py`; revisar su uso, no implementar otra alta equivalente.
- CSV/XLSX/XML, Mock Bank, reglas/corrección de categorías, obligaciones, conciliación y reversión.
- Dashboard contractual 30/60/90, calendario, histórico de flujos y pronósticos experimentales.
- El formulario/API de alta manual fue implementado en `codex/v1-manual-transactions`; consultar contrato y verificaciones vigentes.

## 1. Tareas fáciles

| ID | Dificultad | Trabajo concreto | Dependencias obligatorias | Paralelismo y resultado esperado |
|---|---|---|---|---|
| T01 | 1/5 | Fijar el punto de partida: cambios locales, funciones existentes y comandos de comprobación. | Ninguna. | Paralela a T02/T03. Entregar una lista de archivos/contratos que ya existen y pendientes reales; no borrar cambios previos del usuario. |
| T02 | 1/5 | Escribir guion de presentación y cifras esperadas con fechas relativas al corte. | Ninguna. | Paralela a T01/T03. Entregar caso 500.000 +119.000 −700.000 = −81.000 COP y pasos de uso, sin afirmar que la captura manual funciona todavía. |
| T03 | 2/5 | Preparar textos para diferenciar saldo al corte, movimiento ocurrido y obligación futura. | Ninguna. | Paralela a T01/T02. Entregar textos y ubicación propuesta, sin cambiar cálculos ni reglas financieras. |

## 2. Tareas de dificultad media

| ID | Dificultad | Trabajo concreto | Dependencias obligatorias | Paralelismo y resultado esperado |
|---|---|---|---|---|
| T04 | 3/5 | Cerrar reglas y contrato del alta manual: campos, cuenta, fecha, signo, categoría, saldo, origen, permisos, idempotencia y errores. | T01. | Puede coincidir con T02/T03/T05. Entregar un contrato único y casos de aceptación; es el desbloqueo principal. |
| T05 | 3/5 | Revisar onboarding y elección de empresa/cuenta manual; corregir solo faltas de usabilidad detectadas. | T01. | Paralela a T04. Registro/alta debe conducir a una cuenta utilizable sin editar BD ni código. No depende de rehacer la creación de cuenta existente. |
| T06 | 3/5 | Construir el formulario de movimiento contra el contrato: cuenta, fecha, ingreso/egreso, importe, descripción y categoría opcional. | T04. | Paralela a T09/T10 con respuestas simuladas o adaptador acordado. Entregar componente aislado con carga/error/éxito; su guardado real queda bloqueado por T10. |
| T07 | 3/5 | Preparar casos y fixtures de QA: permisos, fechas, importes, doble envío, cuenta ajena, fallos de red y saldo inalterado. | T02 y T04. | Paralela a T06/T09. Escribir pruebas/casos contra el contrato; las pruebas que necesiten la API no pueden aprobarse antes de T10. |
| T08 | 3/5 | Verificar el escenario de obligaciones existente, conciliación/reversión y resultado esperado de la demo. | T01 y T02. | Paralela al alta manual: estas funciones ya existen. Entregar comprobación de cifras y fallos reales encontrados, sin sustituir la prueba manual futura. |
| T15 | 3/5 | Corregir problemas de uso que encuentre QA y cerrar guía corta de presentación. | T14 ejecutada y hallazgos registrados. | Puede dividirse por componentes sin archivos compartidos. Volver a ejecutar los casos afectados y cerrar los bloqueantes; no limitarse a cambiar textos si falla la persistencia. |

T15 aparece aquí por dificultad, pero se ejecuta al final de la integración. No comenzar
por ella solo porque sea más fácil que el backend.

## 3. Tareas difíciles de la demo

| ID | Dificultad | Trabajo concreto | Dependencias obligatorias | Paralelismo y resultado esperado |
|---|---|---|---|---|
| T09 | 4/5 | Preparar persistencia e idempotencia del movimiento manual; decidir si necesita migración y separar origen de captura de origen de clasificación. | T04. | Paralela a T06/T07/T08. Entregar estrategia/implementación con restricciones necesarias y pruebas. Si no hace falta migración, justificar cómo se preservan las garantías. |
| T10 | 4/5 | Implementar API/servicio de alta: validación, permisos, Decimal, normalización, clasificación, auditoría y retirada de cobertura cuando corresponda. | T09. | Paralela a T06/T07/T08, con un único propietario de modelos/rutas. Entregar alta persistente y reintento idempotente, sin modificar silenciosamente el saldo ni cuentas conectadas. |
| T11 | 4/5 | Integrar formulario y API reales; refrescar movimientos, histórico, categorías y vistas experimentales afectadas. | T05, T06 y T10. | Paralela a T13. Entregar flujo real con la empresa/cuenta correctas y mensajes ante respuesta perdida; nunca simular éxito local. |
| T12 | 4/5 | Preparar datos/caso repetible y herramienta o procedimiento seguro de preparación de la demo. | T02, T08 y T11. | Paralela a T13 cuando esas dependencias terminen. Entregar escenario aislado con fechas relativas; no borrar datos existentes ni ejecutar seeds de desarrollo en producción. |
| T13 | 4/5 | Verificar seguridad e integridad del flujo nuevo: roles, tenant, CSRF, concurrencia/reintentos, clasificación, auditoría y cobertura. | T07 y T10. | Paralela a T11/T12 según disponibilidad. Entregar pruebas significativas, incluyendo PostgreSQL para garantías de concurrencia; identificar lo que no se pudo ejecutar. |
| T14 | 4/5 | Ejecutar QA de navegador con escenario real: ingreso/egreso manual, clasificación, obligaciones, conciliación, dashboard, red, logout y persistencia. | T08, T11, T12 y T13. | No adelantar la aceptación completa usando mocks. Entregar resultados y lista de fallos; encontrar fallos no convierte el recorrido en aprobado. Desbloquea T15. |
| T16 | 4/5 | Publicar y comprobar la versión demostrable: integración, CI, migraciones, despliegue y prueba de humo sobre la versión publicada. | T12, T13, T14 y T15. | Publicación serializada por el integrador. CI y casos bloqueantes deben pasar; dejar plan de recuperación, sin restauraciones destructivas ni recursos de pago. |

## 4. Contrato mínimo que desbloquea el alta manual — T04

- [ ] El movimiento representa dinero **ya ocurrido**, con fecha no posterior al corte ni
  futura respecto al día de registro. Los flujos futuros se crean como obligaciones.
- [ ] La cuenta pertenece a la empresa autenticada y es manual. No permitir inyectar datos
  en cuentas de Mock Bank/proveedor; propietario y contador escriben, lector consulta.
- [ ] La interfaz solicita importe positivo y sentido ingreso/egreso. Definir una sola
  conversión al signo persistido para no invertirlo dos veces entre cliente y servidor.
- [ ] Usar Decimal y cadenas JSON. Definir longitudes, precisión y categorías compatibles.
- [ ] Mantener saldo declarado al corte: **registrar historial no lo vuelve a sumar/restar**.
  Explicar cómo actualizar el saldo explícitamente. No adoptar actualización automática sin
  redefinir antes esta regla y los casos de conciliación.
- [ ] Generar identidad de movimiento sin pedir un ID técnico al usuario. El reintento de
  una misma solicitud debe reutilizar su clave; una operación nueva debe generar otra.
- [ ] Definir respuesta para solicitud repetida y para misma clave con contenido distinto.
  No deduplicar solo por importe/fecha/descripción: dos movimientos legítimos pueden coincidir.
- [ ] Reutilizar normalización/clasificación y reglas de empresa. El origen «capturado
  manualmente» no equivale a «categoría corregida manualmente».
- [ ] Auditar autor, fecha y acción. Creación, idempotencia, auditoría y retirada de confirmación
  de cobertura deben tener límites transaccionales claros para no dejar resultados parciales.
- [ ] Definir endpoint, cuerpos, códigos HTTP, permisos y ejemplos antes de integrar frontend,
  pruebas e inventario OpenAPI. El agente no debe inventar una API diferente por su cuenta.

**NO pueden implementarse con garantías T09/T10 antes de cerrar T04.** Sí se puede investigar
código, proponer alternativas o preparar bocetos; no consolidar decisiones contradictorias.

## 5. Oleadas de ejecución y agentes en paralelo

Ejemplo para **cuatro agentes**, sin exigir un modelo concreto ni una duración prometida.
Un agente integrador puede asumir tareas cuando no está integrando.

| Oleada | Agente A: integración/backend | Agente B: interfaz | Agente C: pruebas | Agente D: producto/demo |
|---|---|---|---|---|
| 0: preparar | T01, después T04. | T03; revisar T05 sin invadir archivos de A. | Inspeccionar pruebas existentes; casos preliminares sin dar por aprobado el endpoint nuevo. | T02. |
| 1: contrato cerrado | T09 → T10, secuenciales. | T05 → T06, según disponibilidad del contrato. | T07 y T08 cuando sus dependencias estén listas. | Borrador de guía/datos, sin ejecutar todavía T12. |
| 2: API terminada | Integrar cambios de modelos/contrato y apoyar fallos de API. | T11, solo con T05/T06/T10 terminadas. | T13 sobre la API real. | T12 solo después de T11 y T08; antes puede revisar el guion. |
| 3: demostrar | Resolver hallazgos backend asignados. | Resolver hallazgos UI asignados. | T14; tras correcciones, repetir casos afectados. | Guía final y cifras de T15; coordinar resultado con QA. |
| 4: publicar | T16 como responsable único del despliegue. | Comprobar la UI publicada. | Prueba de humo y sesión sobre la versión publicada. | Ensayar la presentación y documentar límites. |

No confundir la oleada 3 con cuatro tareas independientes: T14 primero produce los hallazgos;
T15 los corrige y exige repetir las pruebas. T16 espera el cierre de todos los bloqueantes.

### Qué sí puede avanzar sin esperar toda la implementación

- Guion y cifras esperadas mientras se define la API.
- Revisión del onboarding y textos mientras se prepara persistencia.
- Formulario contra contrato mientras backend implementa el servicio.
- Casos de prueba y verificación de obligaciones existentes mientras se crea el alta manual.
- Pruebas de API/aislamiento mientras frontend conecta el formulario.
- Investigación offline y documentación del alcance académico en una vía separada de la demo.

### Qué NO puede darse por hecho ni ejecutarse antes

| Trabajo bloqueado | Debe existir antes | Motivo |
|---|---|---|
| API financiera final | Contrato T04 y persistencia T09. | Evitar reglas de saldo, identidad y clasificación incompatibles. |
| Guardado real desde el formulario | API T10 y formulario T06, con cuenta utilizable T05. | Un mock no guarda datos ni prueba autorización. |
| Refresco validado y persistencia entre sesiones | T11 conectado a servidor real. | Cambiar estado React no demuestra persistencia ni actualización de todas las vistas. |
| Garantía de no duplicación concurrente | T09/T10 y pruebas pertinentes de T13. | Deshabilitar un botón no evita dos solicitudes o procesos simultáneos. |
| Preparación ejecutable de la demo completa | T08 y T11 terminadas. | Las cifras del guion deben corresponder al flujo implementado. |
| Aceptación integral en navegador | T11, T12 y T13. | Necesita integración, datos reproducibles y controles de seguridad. |
| Publicar como demo comprobada | T14/T15 sin bloqueantes y CI de la misma versión. | Publicar no reemplaza probar; pasar unitarias no prueba navegador. |
| Prometer riesgo/probabilidad/confianza validada | Corpus temporal y calibración de la vía posterior. | Cuantiles experimentales y etiquetas de historial no son validación científica. |

## 6. Reparto de archivos para evitar que los agentes se pisen

| Responsable | Área principal | Puntos de coordinación obligatoria |
|---|---|---|
| A: backend/integrador | Nuevo servicio/serializer de alta en `backend/apps/banking/`; modelos/migraciones solo si T09 los necesita. | Propietario único de `backend/config/urls.py`, modelos compartidos y registro central de contratos. Coordinar reutilización con `banking/tasks.py`, clasificación y normalización existentes. |
| B: frontend | Nuevo componente de alta; `frontend/src/Movements.tsx` y refresco de vistas. | Acordar quién integra `frontend/src/main.tsx`, `style.css`, cuentas y helper CSRF. No cambiar contrato o cálculos financieros desde React. |
| C: QA | Nuevos tests específicos y recorrido de navegador; fixtures aisladas. | No modificar modelos/API para forzar expectativas propias. Registrar defectos; el responsable del área cambia implementación y C verifica. |
| D: producto/demo | Guion, datos sintéticos y aceptación en `docs/acceptance/`; propuesta de preparación de datos. | No modificar el seed compartido, modelos ni datos remotos por su cuenta. A integra cualquier comando ejecutable de preparación tras T12. |

- Trabajar en ramas/worktrees separados cuando el entorno lo permita. Aislar también BD,
  archivos temporales y empresas de prueba; un checkout distinto no aísla la BD.
- En una carpeta compartida, asignar archivos concretos antes de escribir. Si dos agentes
  necesitan el mismo archivo, uno entrega el cambio propuesto y el propietario lo integra.
- No permitir migraciones simultáneas sin coordinar dependencias y nombres. Integrarlas
  y verificarlas antes de que otros agentes basen trabajo sobre ellas.
- Solo el integrador actualiza dependencias/lockfiles, el inventario OpenAPI generado y
  configuración de despliegue compartida. Los demás proponen cambios delimitados.
- No ejecutar la suite destructiva contra Supabase ni resetear datos de terceros.
  No publicar credenciales, respaldos ni archivos financieros en commits o conversaciones.

## 7. Paquete mínimo para encargar una tarea a otro agente

Entregar a cada agente una tarjeta con estos campos; no basta «encárgate del backend»:

```text
Tarea: ID y nombre de este roadmap.
Objetivo: comportamiento observable que debe quedar funcionando.
Dependencias: IDs terminados y ubicación del contrato vigente.
Archivos propios: rutas que puede modificar; propietario de archivos compartidos.
Fuera de alcance: lo que no debe implementar ni cambiar en esta tarea.
Invariantes: saldo al corte, Decimal, empresa/rol, CSRF, idempotencia y auditoría.
Aceptación: casos concretos y evidencia que debe entregar.
Entorno: BD aislada, datos sintéticos, sin nuevos costes ni cambios remotos no acordados.
Entrega: archivos/commit, pruebas ejecutadas, resultados, límites y bloqueos reales.
```

La selección de IA depende de capacidad: tareas de texto/revisión acotada pueden usar
modelos más ligeros; integridad, concurrencia, migraciones y conciliación requieren razonamiento
y revisión más cuidadosos. No elegir por velocidad sacrificando pruebas de reglas financieras.

## 8. Puerta de salida: idea demostrable

- [ ] Desde navegador se entra sin sesión a Inicio y luego se registra/inicia sesión.
- [ ] Se crea/elige empresa con cuenta manual, saldo y corte comprensibles.
- [ ] Se registra un ingreso y un egreso sin archivos ni identificadores técnicos visibles.
- [ ] Ambos persisten, se pueden clasificar y no se duplican al reintentar.
- [ ] El usuario entiende por qué el historial no modifica otra vez el saldo declarado.
- [ ] Cobros/pagos pendientes alimentan calendario y escenario 30/60/90 sin doble conteo.
- [ ] Se reproduce el caso −81.000 COP y un cambio de compromiso recalcula el resultado.
- [ ] Lector/empresa ajena no pueden modificar datos; la auditoría conserva autor y operación.
- [ ] Se completa logout/reingreso y un error recuperable sin fingir éxito.
- [ ] QA no tiene defectos que impidan el recorrido y la versión publicada pasa la prueba de humo.
- [ ] La guía distingue escenario contractual de modelo experimental; correo no disponible
  y suspensión del alojamiento gratuito se declaran como límites cuando sigan presentes.

**No bloquean esta puerta** el instalador, Android/iOS, banca de producción, publicación en
tiendas, offline ni demostrar todas las hipótesis científicas. Siguen pendientes, no eliminados.

## 9. Vía posterior: objetivos completos, de menor a mayor dificultad

Puede avanzar en paralelo a la demo en archivos y entornos separados, sin bloquearla.

| ID | Dificultad | Trabajo posterior | Dependencias que NO se pueden saltar |
|---|---|---|---|
| P01 | 2/5 | Completar manuales, ejemplos y aceptación documental. | Para documentar el comportamiento nuevo como implementado: T11 y su evidencia. Borradores pueden empezar antes. |
| P02 | 3/5 | Configurar y comprobar recuperación real por correo. | Proveedor/remitente/buzón autorizados y secretos privados; no depende del formulario manual. No contratar nada de pago. |
| P03 | 3/5 | Completar ejemplos/errores OpenAPI de todas las familias. | Contratos reales de cada familia; para alta manual, T04 y T10. Generación central coordinada. |
| P04 | 4/5 | Administración ampliada de usuarios/empresas. | Contrato de capacidades, autorización/auditoría y pruebas de abuso antes de publicar mutaciones. Independiente del alta manual, pero comparte cuentas/roles y exige coordinación. |
| P05 | 4/5 | Gráfico de saldo histórico real. | Definir fuentes, cobertura y reconstrucción de saldos. No convertir flujo neto mensual en saldo bancario sin esa base. |
| P06 | 4/5 | Rendimiento, concurrencia, accesibilidad y recuperación manual. | Versión estable y condiciones medibles; corpus/entornos aislados para carga y restore. El ensayo completo de nueva UI espera T11. |
| P07 | 4/5 | Evaluación de clasificación y recurrencias. | Corpus independiente autorizado, etiquetas temporales y separación por empresa/grupo; las pruebas sintéticas actuales no bastan. |
| P08 | 5/5 | Validar híbrido/comparación académica y resolver inclusión de Prophet. | Evidencia disponible en cada corte, corpus temporal y protocolo fijado antes de comparar. No atribuir cambios posteriores al pasado. |
| P09 | 5/5 | Calibración de cuantiles, riesgo/factores y confianza por perfil. | Corpus/protocolo de P08 y validación temporal de los modelos evaluados; no deducir probabilidad de déficit de una banda sin metodología. |
| P10 | 5/5 | Revisión de seguridad integral, operación y entrega de tesis. | Alcance ASVS definido, funcionalidades finales verificadas y resultados disponibles. Threat modeling puede avanzar antes; cumplimiento final y conclusiones no. |

Escritorio y port móvil permanecen en la [hoja de entregables](ROADMAP_ENTREGABLES.md) como
etapas aplazadas. Retomarlos requiere una decisión posterior, no una asignación implícita.
