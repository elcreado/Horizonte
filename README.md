# Plataforma de Inteligencia de Liquidez para Microempresas

> **Estado consolidado vigente:** [matriz de implementación](docs/IMPLEMENTATION_STATUS.md). Incluye obligaciones, conciliación e importación XML; el objetivo completo sigue en desarrollo. La [hoja de ruta de entregables](docs/ROADMAP_ENTREGABLES.md) detalla los pasos para la primera versión funcional, la viabilidad de escritorio y las metas de una segunda versión móvil.

> **Prueba vigente sin Docker:** servidor Render Free con PostgreSQL en Supabase y cliente Windows Electron/NSIS. Inicio es público. Importaciones CSV/XLSX/XML, Mock Bank, obligaciones, conciliaciones y escenarios de caja están implementados; los modelos estadísticos siguen experimentales. [Manual de uso](docs/USER_MANUAL.md), [instalador y huella](docs/DESKTOP_RELEASE.md) y [aceptación pendiente](docs/V1_ACCEPTANCE.md). El objetivo completo todavía no está cerrado.
>
> **Arranque y acciones externas:** [docs/TESTING.md](docs/TESTING.md). **Convenciones:** [CODESTYLE.md](CODESTYLE.md). **Revisión:** [docs/REVISION.md](docs/REVISION.md). La demo no requiere claves bancarias ni servicios de pago.


**Diseño e implementación de una plataforma web de inteligencia de liquidez para microempresas mediante agregación de datos financieros y modelos predictivos de flujo de caja.**

> Variante investigativa del título:
> *Plataforma de inteligencia de liquidez basada en Open Finance y modelos de series temporales para la predicción de déficit de caja en microempresas colombianas.*

---

## 1. El Problema

La supervivencia de las microempresas colombianas motiva estudiar herramientas para anticipar riesgos de caja. Las cifras definitivas deben acompañarse del informe original, cohorte y período en la bibliografía. No se atribuye causalmente la mortalidad empresarial a la falta de software financiero sin evidencia específica.

La mayoría de los dueños de microempresas gestionan su liquidez con hojas de cálculo manuales, que se desactualizan rápidamente, son propensas a errores humanos y no integran la información bancaria real ni la facturación electrónica.

**La oportunidad:** el Open Finance (Finanzas Abiertas) permite, mediante APIs estandarizadas y seguras, que un software de terceros lea los movimientos bancarios de un usuario con su consentimiento. Esto habilita la construcción de un "Director Financiero como Servicio" para microempresas.

## 2. La Solución

Una aplicación web que se conecta a las cuentas bancarias de la empresa (modo solo lectura) y a sus sistemas de facturación electrónica. La plataforma:

1. **Agrega** datos bancarios y de facturación.
2. **Categoriza automáticamente** ingresos y egresos.
3. **Proyecta el flujo de caja** a 30, 60 y 90 días.
4. **Alerta tempranamente** al dueño si existe riesgo de quedarse sin liquidez.

La pregunta que el producto responde es concreta y diferenciadora:

> **¿Con el dinero disponible actualmente, los ingresos esperados, las cuentas por cobrar y las obligaciones futuras, en qué momento existe riesgo de que la empresa no pueda cubrir sus pagos?**

El enfoque prioriza anticipar déficit y explicar obligaciones. La diferenciación frente a Siigo, Alegra o QuickBooks requiere comparar sus funciones vigentes; no se asume que carezcan de proyecciones.

## 3. Justificación

- **Baja supervivencia de microempresas:** las microempresas colombianas muestran una baja tasa de supervivencia a cinco años, y la falta de herramientas de proyección financiera es un factor relevante.
- **Brecha de mercado entre los ERP/contables y los gestores de finanzas personales:** los primeros son complejos y miran al pasado; los segundos no entienden lógica empresarial. Existe un espacio claro para una herramienta centrada en flujo de caja.
- **Evidencia académica:** investigaciones colombianas (p. ej., en Revista CEA) han estudiado modelos analíticos de flujo de caja para mipymes y concluyen que este tipo de herramientas puede contribuir a identificar períodos futuros de déficit o superávit.
- **Actualidad regulatoria:** la tesis se desarrolla durante la transición colombiana hacia el **Sistema de Finanzas Abiertas** del Decreto 368 de 2026, cuya hoja de ruta técnica sigue en construcción por la Superintendencia Financiera de Colombia. Esto da actualidad y pertinencia al proyecto.

## 4. Objetivos

### 4.1. Objetivo general

Diseñar e implementar una plataforma web de inteligencia de liquidez para microempresas que integre datos bancarios y de facturación electrónica, y utilice un modelo predictivo híbrido para detectar con anticipación riesgos de déficit de caja.

### 4.2. Objetivos específicos

1. Diseñar una arquitectura de software modular, segura y extensible mediante adaptadores de integración financiera.
2. Implementar un pipeline ETL asíncrono que normalice, deduplique y categorice transacciones bancarias y documentos de facturación.
3. Desarrollar un modelo predictivo híbrido que combine obligaciones financieras conocidas (cuentas por cobrar y por pagar) con técnicas de series temporales.
4. Comparar experimentalmente modelos de predicción (Naive, ARIMA, Prophet, híbrido) bajo validación rolling-origin.
5. Implementar un dashboard con pronósticos probabilísticos (P10/P50/P90) y alertas tempranas de liquidez en lenguaje natural.
6. Aplicar estándares de seguridad web financiera (OWASP ASVS, OAuth 2.0 + PKCE, cifrado de datos sensibles).

## 5. Alcance

El proyecto cubre:

- Autenticación y gestión de empresas y usuarios con roles.
- Conexión de cuentas bancarias en modo **solo lectura** mediante adaptadores (Mock, CSV, sandbox, proveedor Open Finance).
- Importación manual de movimientos (CSV/XLSX).
- Integración de facturación electrónica (API de proveedor o XML DIAN UBL 2.1).
- Normalización, deduplicación y categorización automática de transacciones con corrección manual y aprendizaje.
- Identificación de gastos recurrentes.
- Proyección de flujo de caja a 30/60/90 días (pronóstico diario) con salidas probabilísticas.
- Dashboard y alertas tempranas de liquidez.
- Plan de pruebas, seguridad, CI/CD y documentación.

## 6. Exclusiones (fuera de alcance)

El sistema **NO**:

- Mueve, transfiere o paga dinero (modo **read-only**).
- Almacena CVV o maneja tarjetas.
- Concede créditos ni realiza credit scoring.
- Lleva contabilidad oficial ni prepara declaraciones tributarias.
- Genera estados financieros certificados ni reemplaza a un contador.
- Realiza inversiones.
- Pronostica más allá de 90 días como función principal.
- Incluye aplicación móvil nativa (Android/iOS).
- Se integra con bancos reales en producción (usa entornos sandbox y datos sintéticos).

## 7. Requerimientos Funcionales

| ID | Requerimiento | Prioridad |
|---|---|---|
| RF-01 | Registro, inicio/cierre de sesión y recuperación de contraseña de usuarios. | Alta |
| RF-02 | Gestión de empresas y membresías con roles: Administrador, Propietario, Contador, Consulta. | Alta |
| RF-03 | Conexión de una fuente financiera (cuenta bancaria), consulta de cuentas, saldos, sincronización de movimientos y revocación de la conexión. El sistema nunca permite transferencias. | Alta |
| RF-04 | Importación manual de movimientos desde CSV y XLSX. | Alta |
| RF-05 | Integración de facturas emitidas y recibidas con fechas de vencimiento, valor pendiente y cliente/proveedor. | Media |
| RF-06 | Normalización de descripciones bancarias ("PSE*SERVPUB*EE202889" → Proveedor: CENS, Categoría: Servicios públicos). | Alta |
| RF-07 | Categorización automática de transacciones en una taxonomía empresarial (ingresos/egresos). | Alta |
| RF-08 | Aprendizaje mediante correcciones manuales del usuario (si Adobe se reclasifica a "Software", la próxima clasificación lo usa). | Media |
| RF-09 | Detección de transacciones recurrentes (p. ej., internet cada 3 del mes, nómina cada 30). | Alta |
| RF-10 | Proyección de saldo diario a 30, 60 y 90 días usando el modelo híbrido. | Alta |
| RF-11 | Pronósticos probabilísticos: escenarios optimista (P90), esperado (P50) y conservador (P10). | Media |
| RF-12 | Generación de alertas de liquidez en lenguaje natural con: nivel de riesgo, período en riesgo, saldo mínimo esperado y factores principales. | Alta |
| RF-13 | Dashboard con: saldo consolidado, dinero esperado a recibir, obligaciones a pagar y estado de riesgo. | Alta |
| RF-14 | Gráficos mínimos: saldo histórico real, saldo proyectado, intervalos de confianza, ingresos vs egresos, distribución por categorías, calendario de obligaciones, CxC, CxP, gastos recurrentes y alertas. | Media |
| RF-15 | Niveles de confianza de la proyección según volumen de historial (cold start). | Alta |
| RF-16 | Sincronización asíncrona de cuentas y facturas sin bloquear peticiones web. | Alta |

## 8. Requerimientos No Funcionales

| ID | Requerimiento | Detalle |
|---|---|---|
| RNF-01 | Seguridad | Ningún secreto bancario o token se almacena en texto plano. |
| RNF-02 | Disponibilidad | Meta académica: ≥ 99 % durante pruebas controladas. |
| RNF-03 | Rendimiento | Dashboard en < 2 s para consultas normales. |
| RNF-04 | Concurrencia | Una sincronización no bloquea las peticiones web (procesamiento asíncrono). |
| RNF-05 | Escalabilidad | Los workers de procesamiento deben poder ampliarse horizontalmente. |
| RNF-06 | Trazabilidad | Toda sincronización registra usuario, integración, fecha, resultado y errores. |
| RNF-07 | Aislamiento | Una empresa nunca puede visualizar información de otra (multi-tenant seguro). |
| RNF-08 | Recuperación | Respaldo manual y restauración verificada. El usuario excluyó el respaldo diario automático para esta entrega. |
| RNF-09 | Portabilidad | Despliegue reproducible con Docker / Docker Compose. |
| RNF-10 | Accesibilidad | SPA responsiva para escritorio y móvil (web). |

## 9. Actores

| Actor | Descripción |
|---|---|
| Administrador | Gestiona la plataforma, empresas y usuarios. |
| Propietario | Dueño de la empresa; configura fuentes de datos y ve alertas. |
| Contador | Visualiza y ajusta clasificaciones; herramientas de conciliación. |
| Consulta | Solo lectura de dashboard y alertas. |
| Proveedor Open Finance | Suministra datos bancarios vía API sandbox (adaptador). |
| Usuario anónimo | No autenticado; solo accede a páginas públicas de la app. |

## 10. Reglas de Negocio

- **BN-01:** El sistema opera en modo solo lectura: jamás inicia transferencias ni pagos.
- **BN-02:** Toda conexión bancaria requiere consentimiento previo, expreso e informado del titular.
- **BN-03:** Una transacción importada debe ser idempotente (no se duplica ante reintentos).
- **BN-04:** Una factura emitida no equivale a dinero recibido; el saldo proyectado distingue caja, cuentas por cobrar y cuentas por pagar.
- **BN-05:** La clasificación automática puede ser corregida por el usuario; las correcciones se usan para aprendizaje por empresa.
- **BN-06:** El pronóstico muestra nivel de confianza según la cantidad de historial disponible:
  - 0–29 días → "Datos insuficientes".
  - 30–89 días → "Proyección experimental".
  - 90–364 días → "Historial intermedio".
  - ≥365 días → "Historial extendido".
- **BN-07:** El horizonte principal de pronóstico es de 30 a 90 días (corto plazo).
- **BN-08:** Cualquier actualización de datos que implique procesamiento pesado se ejecuta de forma asíncrona.

## 11. Legislación y Normativa Colombiana Aplicable

- **Decreto 368 de 2026:** establece un **Sistema de Finanzas Abiertas** obligatorio para entidades vigiladas y permite la participación de terceros no vigilados bajo ciertos esquemas. Sustituye el enfoque voluntario anterior. El consentimiento previo, expreso e informado del titular es central. La Superintendencia Financiera de Colombia continúa desarrollando la hoja de ruta técnica e implementación con la industria (septiembre de 2026).
- **Decreto 1297 de 2022:** marco previo de Open Banking / transacciones abiertas (referencia histórica).
- **Ley 1581 de 2012 y Decreto 1377 de 2013:** protección de datos personales; el tratamiento de información bancaria y financiera exige autorización del titular.
- **Ley 1266 de 2008:** *habeas data* financiero.
- **Ley 527 de 1999:** comercio electrónico y mensajes de datos (marco de la facturación electrónica).
- **Facturación electrónica DIAN:** Anexo Técnico de Factura Electrónica de Venta versión 1.9, documentos electrónicos estructurados, UBL 2.1 y CUFE.
- **Referencias técnicas de seguridad (sugeridas):** OWASP ASVS 5.0 (2025), RFC 9700, RFC 10017 (buenas prácticas OAuth 2.0 para aplicaciones web).

> **Nota:** el modo solo lectura reduce el riesgo regulatorio, pero no exime del cumplimiento de las normas de protección de datos ni del tratamiento seguro de tokens de acceso. El MVP trabaja con **sandbox, datos sintéticos y datos anonimizados**, lo que hace el cumplimiento manejable para una tesis académica.

## 12. Riesgos y Mitigación

| Riesgo | Impacto | Mitigación |
|---|---|---|
| API bancaria no disponible | Alto | Capa de adaptadores + sandbox + importación CSV. |
| Poco historial de datos | Alto | Mostrar nivel de confianza del pronóstico. |
| Datos incorrectos | Alto | Validación y limpieza en el ETL. |
| Facturas emitidas no cobradas | Alto | Probabilidad/estado de cobro y modelo de CxC/CxP. |
| Transacciones duplicadas | Medio | Idempotencia con clave lógica (proveedor, cuenta, id externo). |
| Clasificación errónea | Medio | Corrección manual + reentrenamiento. |
| Modelo impreciso | Alto | Comparación experimental de múltiples modelos. |
| Filtración de tokens bancarios | Crítico | Cifrado autenticado + gestor de secretos + TLS. |
| API externa caída | Medio | Jobs programados con reintentos. |
| Scope creep | Alto | MVP cerrado y alcance estricto. |

## 13. Metodología

- Metodología ágil adaptada al contexto académico con fases:
  1. **Investigación:** estado del arte, Open Finance, flujo de caja, APIs, seguridad, modelos predictivos.
  2. **Diseño:** casos de uso, arquitectura, modelo entidad-relación, APIs, UI.
  3. **Data Pipeline:** importación, normalización, deduplicación, categorización.
  4. **Forecast:** Naive, ARIMA, Prophet y modelo híbrido con validación rolling-origin.
  5. **Aplicación:** dashboard, alertas, configuración.
  6. **Seguridad:** OAuth, RBAC, cifrado, auditoría.
  7. **Evaluación:** precisión predictiva, rendimiento, seguridad, usabilidad.

## 14. Plan Aproximado (24 semanas)

| Semanas | Actividad |
|---|---|
| 1–3 | Investigación |
| 4–5 | Requerimientos y arquitectura |
| 6–8 | Backend |
| 9–10 | Frontend |
| 11–13 | ETL |
| 14–16 | Modelos predictivos |
| 17 | Clasificación |
| 18 | Alertas |
| 19 | Seguridad |
| 20 | Integraciones |
| 21 | Pruebas |
| 22 | Experimentos |
| 23 | Resultados |
| 24 | Documento y sustentación |

## 15. Criterios de Éxito del MVP

- Importar ≥ 10 000 transacciones sin degradación relevante.
- Detectar y evitar duplicados (operación idempotente).
- Clasificar ≥ 80 % de las transacciones automáticamente.
- Permitir corrección manual de clasificación.
- Sincronizar facturas desde API o XML.
- Generar forecast 30/60/90 días.
- Detectar futuro saldo negativo y mostrarlo como riesgo.
- Mostrar explicación de cada alerta.
- Procesar actualizaciones de forma asíncrona.
- Garantizar separación estricta entre empresas.
- Mantener auditoría de conexiones y accesos.

> Los porcentajes definitivos se establecen tras el experimento piloto.

## 16. Entregables

1. Documento de tesis (anteproyecto + documento final).
2. Aplicación web (frontend React).
3. Backend REST (Django).
4. Base de datos (PostgreSQL).
5. Pipeline ETL.
6. Motor predictivo híbrido.
7. Dataset sintético (100 empresas, 24 meses con patrones distintos).
8. Experimentos y resultados comparativos de modelos.
9. Threat model.
10. Manual de usuario.
11. Manual técnico.
12. Docker Compose.
13. Pruebas automatizadas.
14. API documentada con OpenAPI.

## 17. Pregunta de Investigación e Hipótesis

**Pregunta:** ¿En qué medida un modelo híbrido que combine obligaciones financieras conocidas con técnicas de predicción de series temporales mejora la detección anticipada de riesgos de liquidez en microempresas frente a métodos tradicionales basados exclusivamente en información histórica?

- **H1:** Un modelo híbrido compuesto por flujos financieros determinísticos y estimaciones estadísticas permitirá reducir el error de predicción del saldo futuro respecto a un modelo basado exclusivamente en series históricas.
- **H2:** La integración automática de transacciones bancarias y documentos de facturación reducirá la intervención manual requerida para mantener actualizada la proyección de liquidez.

## 18. Estructura del Repositorio

```text
proyecto/
├── README.md          # Este documento
├── SPECS.md           # Especificación técnica completa
├── docs/
│   ├── anteproyecto/  # Documento de tesis (problema, marco teórico, bibliografía)
│   └── diagramas/     # Arquitectura, modelo E-R, casos de uso
├── backend/           # Django + DRF
│   ├── apps/
│   │   ├── accounts/  # Autenticación, empresas, roles
│   │   ├── banking/   # Conexiones, cuentas, transacciones
│   │   ├── invoices/  # Facturación recibida/emitida
│   │   ├── classify/  # Categorización
│   │   ├── forecast/  # Modelo predictivo y alertas
│   │   └── integrations/  # Adaptadores Open Finance
│   └── tests/
├── workers/           # Celery tasks (ETL, forecast)
├── frontend/          # React + TypeScript + Vite
├── data/              # Datasets sintéticos y scripts de generación
├── ml/                # Notebooks y experimentos predictivos
├── deploy/            # Docker Compose, Nginx, CI/CD
└── CODESTYLE.md       # Convenciones de implementación
```

---

**Pipeline implementado:** carga CSV/XLSX idempotente, validación y procesamiento asíncrono con registro de resultado; XML con revisión, obligaciones y conciliación reversible. El servidor gratuito utiliza cola persistente en PostgreSQL; Celery sigue como alternativa de despliegue. La estructura anterior es objetivo. La antigüedad del historial no garantiza precisión: se requieren calidad, cobertura y resultados fuera de muestra.

La aplicación alojada y el instalador permiten probar las importaciones sin Docker ni Redis local. Ver [manual de uso](docs/USER_MANUAL.md); para desarrollo local, [arranque y pruebas](docs/TESTING.md).

**Clasificación implementada:** reglas automáticas en nuevas importaciones, lista paginada, corrección manual por rol, reglas recordadas por empresa y sugerencias TF-IDF experimentales. La validación con corpus representativo y la exactitud general siguen pendientes.
