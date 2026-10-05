# SPECS.md — Especificación Técnica

> **Estado consolidado vigente:** [matriz de implementación](docs/IMPLEMENTATION_STATUS.md). Incluye obligaciones, conciliación e importación XML; el objetivo completo sigue en desarrollo.

> **Estado de ejecución vigente:** Django + CSRF y React alojados en Render Free, PostgreSQL en Supabase y cliente Windows Electron/NSIS para pruebas sin Docker. ETL CSV/XLSX/XML, Mock Bank, roles, obligaciones y conciliación reversible implementados. Pronósticos y cuantiles estadísticos experimentales, sin calibración demostrada. [Manual](docs/USER_MANUAL.md) · [Aceptación pendiente](docs/V1_ACCEPTANCE.md). Respaldo manual únicamente: no activar respaldo diario automático.


**Plataforma de Inteligencia de Liquidez para Microempresas**
Documento técnico de referencia: arquitectura, modelo de datos, APIs, integraciones, ETL, predicción, seguridad, pruebas, CI/CD y roadmap.

---

## 1. Visión General

Sistema web que agrega datos financieros (bancos y facturación electrónica) de microempresas en modo solo lectura, los normaliza y categoriza, y genera proyecciones de flujo de caja a 30/60/90 días con pronósticos probabilísticos y alertas tempranas de liquidez.

**Principios de diseño**

- Monolito modular con procesamiento asíncrono (no microservicios).
- Arquitectura extensible mediante **adaptadores de integración** (no depender de un proveedor específico).
- MVP **read-only**, **sandbox** y **datos sintéticos**, con alcance académico controlado.
- Separación estricta entre empresas (multi-tenant).

## 2. Arquitectura de Referencia

```text
                  ┌─────────────────────┐
                  │    React + TS       │
                  │     Frontend        │
                  └─────────┬───────────┘
                            │ HTTPS
                            ▼
                  ┌─────────────────────┐
                  │ Django REST API     │
                  │                     │
                  │ Auth                │
                  │ Empresas            │
                  │ Transacciones       │
                  │ Facturación         │
                  │ Forecast            │
                  │ Alertas             │
                  └───────┬─────┬───────┘
                          │     │
             ┌────────────┘     └────────────┐
             ▼                               ▼
     ┌───────────────┐              ┌────────────────┐
     │ PostgreSQL    │              │ Redis + Celery │
     └───────────────┘              └───────┬────────┘
                                            │
                 ┌──────────────────────────┼──────────────┐
                 ▼                          ▼              ▼
         Bank Connector             Invoice API       ML Engine
         Open Finance              Siigo/Alegra       Forecasting
```

**Características**

- **Web service (Django + DRF):** maneja HTTP, auth, validación; escala, pero el trabajo pesado se delega a workers.
- **Workers (Celery + Redis):** sincronización, ETL, categorización, forecast y alertas. Escalables horizontalmente.
- **Base de datos (PostgreSQL):** almacén relacional de datos normalizados.
- **Frontend (React + TypeScript + Vite + Recharts):** dashboard y alertas.

## 3. Stack Tecnológico

| Capa | Tecnología |
|---|---|
| Frontend | React 18, TypeScript estricto, Vite, Recharts y CSS; Query/Router cuando los flujos lo requieran. Versiones exactas en package-lock.json |
| Backend | Python 3.13, Django 5.2 LTS, Django REST Framework; versiones exactas en requirements.txt |
| Datos | PostgreSQL 16, Redis 7 |
| Procesamiento | Celery 5, Celery Beat |
| Ciencia de datos | Pandas, NumPy, Scikit-learn, Statsmodels, Prophet, Optuna (opcional) |
| Infraestructura | Docker, Docker Compose, Nginx, GitHub Actions, HTTPS obligatorio |
| Documentación API | OpenAPI 3 |

**Decisiones justificadas**

- **Django sobre Flask:** auth, ORM, migraciones, permisos, middleware y panel admin integrados; deja tiempo para la algoritmia de la tesis.
- **Recharts sobre D3.js:** suficiente para dashboards empresariales y menor complejidad.
- **Monolito modular sobre microservicios:** evita complejidad arquitectónica sin beneficio científico; el desacoplamiento por módulos + workers ya permite escalar horizontalmente.
- **Sin LSTM en el MVP:** con pocas empresas y datos, una red neuronal compleja agrega más problemas que beneficios.

## 4. Modelo de Datos

Entidades principales:

```text
User
Company
CompanyMember

FinancialInstitution
BankConnection
BankAccount
BankBalance
Transaction

TransactionMerchant
TransactionCategory
TransactionClassification

Customer
Supplier

Invoice
InvoicePayment
Receivable
Payable

RecurringTransaction

CashFlowForecast
ForecastPoint
ForecastScenario

LiquidityAlert

Consent
AuditLog
IntegrationJob
```

### 4.1. Esquemas clave

```text
User (id, email, password_hash, first_name, last_name, is_active, mfa_enabled_lt)
Company (id, name, nit, industry, created_at)
CompanyMember (id, company_id FK, user_id FK, role ENUM[admin, owner, accountant, viewer])

FinancialInstitution (id, provider_code, name, country)
BankConnection (id, company_id FK, institution_id FK, provider_ref, status, consent_id FK, created_at, revoked_at)
BankAccount (id, connection_id FK, provider_account_id, account_type, currency, last_sync_at)
BankBalance (id, account_id FK, balance, date)
Transaction (id, account_id FK, external_transaction_id, date, amount, currency, raw_description,
            normalized_description, category_id FK, merchant_id FK, status,
            UNIQUE(account_id, external_transaction_id))

TransactionCategory (id, parent_id FK NULL, name, type ENUM[income, expense], is_system_default)
TransactionMerchant (id, name, normalized_name, UNIQUE(normalized_name))
TransactionClassification (id, transaction_id FK, category_id FK, source ENUM[auto, manual], user_id FK, created_at)

Customer (id, company_id FK, name, document, email)   -- sujeto de cuentas por cobrar
Supplier (id, company_id FK, name, document, email)   -- sujeto de cuentas por pagar

Invoice (id, company_id FK, direction ENUM[out, in], provider, number, cufe, issue_date, due_date,
         subtotal, iva, total, status ENUM[pending, partial, paid, cancelled])
InvoicePayment (id, invoice_id FK, transaction_id FK NULL, amount, paid_at)

Receivable (id, company_id FK, counterparty_id FK, amount, due_date, expected_probability, status)
Payable (id, company_id FK, counterparty_id FK, amount, due_date, status)

RecurringTransaction (id, company_id FK, description, amount, category_id FK, frequency,
                      next_expected_date, confidence)

CashFlowForecast (id, company_id FK, generated_at, model_version, horizon_days, method)
ForecastPoint (id, forecast_id FK, date, expected_balance P50, p10, p90, deterministic_in, out, estimated_in, out)
ForecastScenario (id, forecast_id FK, name ENUM[conservative, expected, optimistic], config)

LiquidityAlert (id, forecast_id FK, level ENUM[low, medium, high], window_start, window_end,
                min_expected_balance, message, factors JSONB, status, created_at)

Consent (id, company_id FK, provider_ref, scope[], granted_at, revoked_at, version)
AuditLog (id, company_id FK, user_id FK, action, entity, entity_id, before JSONB, after JSONB, created_at)
IntegrationJob (id, company_id FK, kind, status, started_at, finished_at, result JSONB, error TEXT)
```

### 4.2. Reglas de integridad

- `Transaction` es **idempotente**: clave única `(account_id, external_transaction_id)` para evitar duplicados ante reintentos.
- `Company` es el tenant; **toda** consulta filtra por `company_id` (aislamiento RNF-07).
- Monedas y montos se almacenan como `DECIMAL` con precisión configurable; nunca `FLOAT`.

## 5. Capa de Adaptadores Financieros

Patrón de abstracción para no depender de ningún proveedor:

```python
class FinancialDataProvider(ABC):
    def connect(self) -> None: ...
    def get_accounts(self) -> list[...]: ...
    def get_balances(self) -> list[...]: ...
    def get_transactions(self) -> list[...]: ...

class MockBankProvider(FinancialDataProvider): ...
class CSVProvider(FinancialDataProvider): ...
class BancolombiaSandboxProvider(FinancialDataProvider): ...
class PrometeoProvider(FinancialDataProvider): ...
```

```text
FinancialDataProvider
      │
      ├── MockBankProvider
      ├── CSVProvider
      ├── BancolombiaSandboxProvider
      └── PrometeoProvider
```

**Candidatos de integración: disponibilidad pendiente de verificar**

Prometeo, Bancolombia, Belvo, Fintoc y Plaid requieren confirmar cobertura colombiana de movimientos/saldos, acceso de desarrollador, costos y datos de prueba. No se promete disponibilidad de ningún sandbox antes de obtener acceso.

Estrategia objetivo: Mock Bank + un sandbox + XML UBL 2.1 o API de facturación. Mock/CSV permiten desarrollar sin bloquearse por terceros; v0.1 contiene únicamente fixtures sintéticos.

## 6. Integración de Facturación

Tres caminos contemplados (se implementa al menos uno):

**Opción A — Alegra API REST**
Facturas emitidas, facturas de proveedores, pagos, gastos, cuentas bancarias, contactos y webhooks. Ej.: `/api/v1/invoices`.

**Opción B — Siigo API**
Facturas de venta, compras, recibos, egresos, documentos soporte y reportes de cuentas por pagar.

**Opción C — XML DIAN (UBL 2.1)**
El usuario sube la factura XML y el sistema extrae:

```text
NIT, proveedor, cliente, fecha emisión, fecha vencimiento,
subtotal, IVA, total, CUFE (no determina estado de pago)
```

Adecuada para tesis por no requerir contratos comerciales. El XML no prueba cobro ni saldo pendiente: se necesita conciliación o registro autorizado. Si falta vencimiento, solicitar fecha o dejar pendiente de revisión. Rechazar DTD/entidades externas y limitar tamaño del archivo.

## 7. Fuentes de Información del Motor

```text
Banco       ↓ transacciones reales (sandbox)
Facturación ↓ ventas y compras
Usuario     ↓ obligaciones manuales
Sistema     ↓ patrones recurrentes detectados
```

Todo se convierte a un **modelo financiero único** (transacciones normalizadas + CxC + CxP + recurrencias).

## 8. Pipeline ETL

```text
EXTRACT
   ↓
Bank API  ·  Invoices  ·  CSV
   ↓
TRANSFORM
   ↓
Normalización · Duplicados · Categorías · Comercios · Fechas · Monedas
   ↓
LOAD → PostgreSQL
   ↓
FEATURE ENGINEERING
   ↓
FORECAST
   ↓
ALERTS
```

**Detalles**

- **Normalización:** `uppercase/lowercase`, eliminación de códigos y números irrelevantes, normalización de espacios e identificación de comercio.
- **Deduplicación:** operaciones idempotentes; se reintenta la sincronización sin duplicar registros.
- **Monedas y fechas:** normalización explícita en el transform.

## 9. Categorización Automática

Enfoque por capas (sin LLM en el MVP):

1. **Capa 1 — Normalización:** regex + limpieza de descripciones.
2. **Capa 2 — Reglas:** reglas basadas en tokens:

```python
if "CENS" in description:
    category = "Servicios públicos"
if "NOMINA" in description:
    category = "Nómina"
```

3. **Capa 3 — Machine Learning:** `TF-IDF` + `Logistic Regression` o `Linear SVM`; se validan embeddings como trabajo futuro.

**Aprendizaje por correcciones:** si `Adobe → Otros` es corregido por el usuario a `Adobe → Software`, el sistema lo registra y lo reutiliza para la clasificación futura de esa empresa.

### 9.1. Taxonomía de categorías

```text
Ingresos
 ├ Ventas
 ├ Servicios
 ├ Financiación
 └ Otros

Egresos
 ├ Nómina
 ├ Proveedores
 ├ Arriendo
 ├ Servicios públicos
 ├ Impuestos
 ├ Software
 ├ Transporte
 ├ Marketing
 ├ Deuda
 ├ Inventario
 └ Otros
```

## 10. Modelo Predictivo de Flujo de Caja

### 10.1. Modelo híbrido

Fórmula fundamental:

```
Caja[t+1] = Caja[t] + Entradas_conocidas - Salidas_conocidas
                   + Entradas_estimadas - Salidas_estimadas
```

Componentes:

- **A. Flujos determinísticos (conocidos):** CxC, CxP, nómina, créditos, arriendo, impuestos.
- **B. Gastos recurrentes detectados:** internet cada 3 del mes, arriendo cada 1, Adobe cada 17, nómina cada 30.
- **C. Flujos variables (estadístico):** aquí interviene el modelo de series temporales.
- **D. Saldo bancario actual:** punto de partida.

### 10.2. Modelos a comparar

| Categoría | Modelos |
|---|---|
| Baseline | Naive Forecast, Seasonal Naive |
| Estadísticos | Exponential Smoothing, ARIMA, SARIMA |
| Empresarial | Prophet |
| Opcional | Gradient Boosting / XGBoost |

> No se usa LSTM en el MVP. La literatura reciente muestra que no existe un modelo universalmente ganador; el rendimiento depende de las características del flujo financiero → se justifica la comparación experimental.

### 10.3. Horizonte y salida

- Pronóstico **diario** interno, presentado a **30/60/90 días**.
- Salidas **probabilísticas**: P90 (optimista), P50 (esperado), P10 (conservador).
- Detección de *liquidity breach* cuando el saldo proyectado cruza a negativo.

```text
Fecha        Saldo proyectado
01/10        8.500.000
02/10        8.210.000
03/10        7.970.000
...
21/10        1.230.000
22/10         -340.000   ← LIQUIDITY BREACH
```

### 10.4. Características (feature engineering)

- Montos, catálogo de categorías, recurrencias, estacionalidad (día de mes, día de semana).
- Datos de obligaciones conocidas (CxC/CxP) como características exógenas.
- Variables de calendario (quincenas, nómina, impuestos mensuales).

## 11. Alertas de Liquidez

Ejemplo de alerta generada:

```text
RIESGO ALTO
Existe una probabilidad elevada de que el saldo sea inferior a $0
entre el 21 y el 26 de octubre.

Saldo mínimo esperado: -$2.460.000
Factores principales:
  • Nómina: -$5.800.000
  • Proveedores: -$3.200.000
  • Cobros esperados: +$4.100.000
```

**Reglas de alerta:** umbral configurable por empresa, ventana de días en riesgo, nivel `low|medium|high`, y explicación de factores (trazabilidad del motivo).

## 12. Dashboard

Responde de inmediato:

| Pregunta | Visualización |
|---|---|
| ¿Cuánto dinero tengo? | Saldo consolidado. |
| ¿Cuánto espero recibir? | Ingresos proyectados 30 días. |
| ¿Cuánto debo pagar? | Obligaciones proyectadas 30 días. |
| ¿Tendré problemas? | Indicador "Riesgo de liquidez en N días". |

Gráficos mínimos:

1. Saldo real histórico.
2. Saldo proyectado.
3. Intervalos de confianza (banda P10–P90).
4. Ingresos vs egresos.
5. Distribución por categorías.
6. Calendario de obligaciones.
7. Cuentas por cobrar.
8. Cuentas por pagar.
9. Gastos recurrentes.
10. Alertas.

## 13. Seguridad

### 13.1. Referencias

- **OWASP ASVS 5.0** (2025) como marco de referencia.
- **RFC 9700** y **RFC 10017** (agosto de 2026): buenas prácticas OAuth 2.0 para aplicaciones web en navegador.

### 13.2. Controles mínimos

```text
TLS (obligatorio)         OAuth 2.0 / OIDC + PKCE
CSRF protection           CSP (Content Security Policy)
RBAC                      Rate limiting
Audit logging             Secret management
Database encryption       Token encryption (AES-GCM)
Secure cookies            Input validation
```

### 13.3. OAuth / Open Finance

- **Authorization Code Flow + PKCE**; nunca Implicit Flow.
- Los tokens de acceso del proveedor financiero se cifran en reposo (AES-GCM) y nunca se exponen al frontend.

### 13.4. Protección de secretos

- Las claves de API bancarias existen **únicamente en el backend** (Secret Manager / variables de entorno protegidas).
- Prohibido `REACT_APP_BANK_API_KEY=...` en el frontend.

### 13.5. Contraseñas

- Almacenar con **Argon2id** (primera opción OWASP); Django 5.2 requiere instalar argon2-cffi y configurar Argon2PasswordHasher primero en PASSWORD_HASHERS.
- No usar SHA-256 u otros hashes rápidos.

### 13.6. Datos sensibles en reposo

- Cifrado autenticado con algoritmos estándar (AES-GCM) para: tokens, refresh tokens y credenciales de integración.
- No inventar criptografía propia.

## 14. Procesamiento Asíncrono (Celery)

```text
00:00  Celery Beat
       ↓
sync_bank_accounts.delay()
       ↓
normalize_transactions.delay()
       ↓
classify_transactions.delay()
       ↓
detect_recurring.delay()
       ↓
generate_forecast.delay()
       ↓
evaluate_liquidity_alerts.delay()
```

## 15. Evaluación de Modelos

### 15.1. Métricas

```text
MAE
RMSE
sMAPE
Pinball Loss
```

### 15.2. Métricas empresariales

- **Error de fecha de déficit:** |fecha real − fecha predicha| en días.
- **Detección de crisis (saldo < umbral):** Precision, Recall, F1.

### 15.3. Métrica propia del proyecto (DLDE)

**Days Liquidity Deficit Error:**

```
DLDE = |D_déficit_real − D_déficit_predicho|
```

Número de días de diferencia entre el momento real de iliquidez y el pronosticado.

### 15.4. Validación

- **Rolling-origin validation** (no partición aleatoria):

```text
Ene–Jun → predice Julio
Ene–Jul → predice Agosto
Ene–Ago → predice Septiembre
```

## 16. Datasets de Investigación

| Dataset | Descripción |
|---|---|
| A | Sintético: 100 empresas × 24 meses con patrones distintos. |
| B | Sandbox Open Finance (prometeo/bancolombia). |
| C | Opcional: datos reales anonimizados de 5–20 microempresas (con colaboración). |

## 17. Pruebas

### 17.1. Software

```text
Unitarias · Integración · End-to-end · API · Carga
```

### 17.2. Seguridad

```text
OWASP · SQL Injection · XSS · CSRF · IDOR · JWT/token handling · rate limiting
```

### 17.3. ML

```text
Backtesting · Rolling validation · Baseline comparison · Prediction intervals
```

### 17.4. UX

Pruebas con empresarios: ¿entienden el dashboard?, ¿entienden la alerta?, ¿saben cuánto dinero tendrán?, ¿saben por qué se generó el riesgo?

## 18. CI/CD

- **GitHub Actions:** lint, tests (backend/frontend), análisis de seguridad básico, build de imágenes Docker.
- **Pipeline:** commit → tests → build → imagen → deploy a entorno de prueba (sandbox).
- Despliegue con **Docker Compose** y **Nginx** (proxy inverso + TLS).

## 19. Observabilidad

- Logs estructurados en `IntegrationJob` y `AuditLog` (trazabilidad de sincronizaciones y datos).
- Métricas básicas: duración de sincronización, errores de integración, tasa de clasificación automática, precisión del forecast, latencia del dashboard.
- Monitoreo de workers Celery (colas, reintentos, fallos).

## 20. Roadmap Técnico

1. **Fase 0 — Base:** repositorio, CI/CD, Docker Compose, entornos dev/test.
2. **Fase 1 — Auth y tenant:** usuarios, empresas, roles (RBAC), logging.
3. **Fase 2 — Modelo de datos:** migraciones PostgreSQL de dominio.
4. **Fase 3 — Data pipeline:** import CSV, mock bank, normalización, deduplicación, categorización (regex + reglas + ML).
5. **Fase 4 — Facturación:** XML DIAN UBL 2.1 y/o API (Alegra/Siigo).
6. **Fase 5 — Forecast:** naive/ARIMA/Prophet, modelo híbrido, pronóstico probabilístico.
7. **Fase 6 — Aplicación:** dashboard, alertas de liquidez.
8. **Fase 7 — Seguridad:** OAuth + PKCE, cifrado de tokens, hardening OWASP ASVS.
9. **Fase 8 — Evaluación:** experimentos rolling-origin, métricas DLDE y de alertas, informe comparativo.

## 21. Riesgos Técnicos y Mitigación

| Riesgo | Mitigación |
|---|---|
| API bancaria no disponible | Adapter + sandbox + CSV. |
| Poco historial de datos | Nivel de confianza / estados de cold start. |
| Transacciones duplicadas | Idempotencia por clave única. |
| Clasificación errónea | Corrección manual + reentrenamiento. |
| Modelo impreciso | Comparación experimental de varios modelos. |
| Filtración de tokens | Cifrado AES-GCM + Secret Manager + TLS. |
| Factura emitida ≠ dinero recibido | Separar caja, receivable y payable en el modelo. |

## 22. Decisiones de Alcance Técnico

El MVP **incluye**:

- Autenticación y empresas (RBAC).
- Importación bancaria (CSV) + integración con 1 sandbox.
- Integración de facturación o XML.
- Normalización y categorización automática.
- Identificación de recurrencias.
- Proyección 30/60/90 días (híbrido).
- Dashboard.
- Alertas de liquidez.

El MVP **no incluye**: transferencias, pagos, móvil nativo, contabilidad oficial, créditos/credit scoring, pronóstico > 90 días como función principal.
## 23. Contrato inicial y reglas de evolución

- API actual: GET /api/auth/csrf/, POST /api/auth/login/, POST /api/auth/logout/, GET /api/auth/me/, GET /api/companies/, GET /api/companies/{id}/dashboard/?horizon=30|60|90.
- Autenticación de aplicación: sesión HttpOnly + CSRF, incluso en login. OAuth + PKCE corresponde a las integraciones futuras.
- Administrador de plataforma y miembro de empresa son conceptos distintos; el privilegio de plataforma no concede datos financieros en la API. Roles iniciales: owner/accountant/viewer con acceso de lectura.
- Saldos consolidados en COP con fecha de corte común. No sumar saldos de fechas o monedas incompatibles.
- Montos Decimal en almacenamiento y cálculo; cadenas decimales en JSON. El frontend solo convierte para presentación.
- Obligaciones representan valores pendientes. Factura, CxC/CxP y recurrencia no pueden introducir tres veces el mismo flujo. Las futuras conciliaciones enlazarán fuentes y pagos.
- Obligaciones vencidas requieren fecha esperada explícita; la primera proyección las cuenta aparte y excluye del futuro. La caja inicial no vuelve a sumar el historial bancario.
- v0.1 genera un escenario de pagos/cobros puntuales sin cuantiles. P50 será mediana, no media; P10–P90 será un intervalo predictivo, no confianza de un parámetro.
- Los modelos excluirán del residual flujos ya cubiertos por obligaciones y recurrencias; validar sin información posterior al corte.
- DLDE solo se calcula si ambos déficits existen; ausencias se reportan como falsos positivos/negativos o casos sin evento.
- Medir cobertura de clasificación y exactitud por separado. Rendimiento: definir dataset, hardware, concurrencia y p95 antes de declarar RNF-03 cumplido.
- HTTPS obligatorio fuera de localhost. La configuración actual es desarrollo y no declara cumplimiento ASVS ni despliegue de producción.

### Navegación pública implementada

Inicio es accesible sin sesión y explica el alcance del producto; login y dashboard son vistas separadas. Acceder al dashboard sin sesión presenta el formulario de acceso. Cerrar sesión vuelve a Inicio. Las APIs financieras conservan autenticación y filtrado por empresa. El despliegue gratuito procesa integraciones con cola persistente en PostgreSQL; Redis no es requisito del cliente de escritorio.

### Corte CSV entregado

GET /api/companies/{id}/accounts/ y GET/POST /api/companies/{id}/imports/. POST multipart devuelve 202 y un trabajo; el worker procesa CSV/XLSX fuera de HTTP. Lectura restringida al tenant; escritura solo owner/accountant, revalidada al ejecutar. Carga atómica y bloqueo por cuenta, IDs estables, conflictos rechazados, sin actualizar saldo. Registro ImportJob con usuario/fecha/checksum/resultado; contenido temporal se borra al terminar. Límites y contrato en docs/TESTING.md. Normalización, clasificación y auditoría están implementadas; aceptación con corpus representativo pendiente.

### Corte de clasificación entregado

GET /api/companies/{id}/movements/?page=N y PATCH /api/companies/{id}/movements/{transaction_id}/category/. Payload: category y remember (booleano). Corrección owner/accountant, aislamiento por empresa, registro ClassificationChange y regla ClassificationRule por empresa/descripción normalizada/sentido. Prioridad: regla de empresa → regla por palabra completa → Otros. Solo nuevas filas importadas se clasifican automáticamente; no sobrescribir correcciones ni modificar saldos. La interfaz permite gestionar reglas y consultar sugerencias TF-IDF experimentales con abstención; no implica exactitud validada ni reclasificación histórica masiva. Contratos vigentes en docs/openapi-inventory.json, todavía parciales.
