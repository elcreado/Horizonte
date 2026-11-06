# Guía de aceptación pendiente — P05/RF-14: Historial y categorías

**Estado:** ejecución local parcial de Codex el 30 de octubre de 2026. Los casos pendientes conservan su estado; la suite automatizada y el recorrido visual se registran por separado.
**Alcance:** P05 / RF-14, saldo histórico diario (`balance_history`) en la sección **Historial y categorías**.
**Fecha de preparación:** 30 de octubre de 2026.
**Implementación:** a cargo de Codex. Esta guía no modifica código, rutas, contratos ni esquema de base de datos.

> Esta guía describe resultados esperados, no resultados observados. No debe registrarse ningún caso como aprobado sin evidencia de una ejecución real en un entorno local con datos sintéticos.

## 1. Contrato de referencia

- El endpoint existente `GET history` incorpora `balance_history`; no se crean rutas nuevas ni cambios de esquema.
- El saldo histórico diario se reconstruye hacia atrás desde el saldo declarado al corte común en COP:
  `B(día) = B(corte) - suma(importes registrados después del día y hasta el corte)`.
- Los movimientos del día de corte ya están incluidos en el saldo declarado: no se vuelven a sumar. `B(corte)` es siempre el saldo declarado.
- No se deducen obligaciones ni liquidaciones futuras del saldo histórico.
- Solo se reconstruyen días anteriores al corte cuando **todas** las cuentas de la empresa tienen cobertura confirmada o de fuente completa hasta ese corte. El inicio del tramo reconstruido es `max(inicio de cobertura de las cuentas)`, recortado al periodo visible de los últimos 12 meses.
- Los días anteriores a la cobertura completa tienen `balance = null` y estado `unknown`; nunca se muestran como cero.
- El punto de corte conserva el saldo declarado aunque no exista cobertura. Dentro del tramo completo, un día sin movimientos conserva el saldo del día anterior reconstruido.
- El saldo histórico no está verificado independientemente contra el banco. La procedencia distingue el saldo declarado y la cobertura por confirmación manual o fuente conectada; no clasifica el origen de cada transacción.
- Varios movimientos del mismo día se agrupan con aritmética Decimal exacta. El gráfico muestra solo la serie numérica; la tabla diaria accesible expone los mismos valores.
- Una entrada o importación nueva dentro del periodo confirmado revoca la cobertura e invalida la serie histórica hasta que se reconfirme.

## 2. Entorno de ejecución

- Usar exclusivamente Docker local o un entorno manual local.
- Usar empresas, cuentas, archivos y usuarios sintéticos.
- No usar datos bancarios reales, datos de producción ni credenciales reales.
- Registrar por caso: fecha y hora, entorno, empresa, usuario/rol, resultado y evidencia. No adjuntar secretos ni archivos financieros privados.

## 3. Escenario base con cifras exactas

**Empresa:** una sola cuenta manual COP.
**Corte declarado:** 2026-09-23.
**Saldo declarado al corte:** `B(corte) = 500.00 COP`.
**Cobertura confirmada:** desde 2026-09-21 inclusive.
**Movimientos registrados:**

| Fecha | Tipo | Importe |
|---|---|---:|
| 2026-09-22 | Ingreso | +100.10 |
| 2026-09-23 | Egreso | -20.05 |

**Resultado esperado:**

| Fecha | `balance` esperado | Estado esperado | Comprobación |
|---|---:|---|---|
| 2026-09-20 y anteriores | `null` | `unknown` | Fuera del inicio de cobertura |
| 2026-09-21 | `419.95` | reconstruido | `500.00 - (100.10 - 20.05) = 419.95` |
| 2026-09-22 | `520.05` | reconstruido | `500.00 - (-20.05) = 520.05` |
| 2026-09-23 (corte) | `500.00` | declarado | No se vuelve a sumar el egreso del día de corte |

Comprobaciones explícitas:

- El día de corte debe mostrar `500.00`, no `479.95`; sumar de nuevo el egreso de ese día es un error.
- El día 22 debe mostrar `520.05`, no `500.00`; omitir el movimiento del día de corte en la resta es un error.
- El día 21 debe mostrar `419.95`, no `520.05`; omitir el ingreso del día 22 es un error.
- El día 21 no tiene movimientos propios y aun así conserva `419.95`; un día vacío dentro del tramo completo no se convierte en cero.
- El día 20 y anteriores deben ser `null` / `unknown`, no `0.00`.

**Procedencia esperada:** una fila por cuenta con nombre de cuenta, saldo declarado, fecha de corte, inicio de cobertura confirmada, procedencia de cobertura (confirmación manual/fuente conectada) y la indicación de que no es verificación bancaria independiente.

## 4. Casos de aceptación

Los pasos siguientes definen resultados contractuales. Los estados reales se registran en la tabla de ejecución; el guion original se conserva en los artefactos locales de OpenCode.

### A01 — Reconstrucción base y procedencia

- **Precondición:** escenario base de la sección 3.
- **Pasos:** abrir **Historial y categorías**, seleccionar la empresa y consultar la serie diaria y la tabla accesible.
- **Esperado:** días 21, 22 y 23 con `419.95`, `520.05` y `500.00`; día 20 y anteriores `null` / `unknown`; procedencia por cuenta visible; gráfico y tabla coincidentes.
- **Estado:** Aprobado local por Codex; ver tabla de ejecución.

### A02 — El día de corte no se vuelve a sumar

- **Precondición:** escenario base.
- **Pasos:** comparar el valor del corte con el saldo declarado y revisar que el egreso de `-20.05` del 2026-09-23 solo interviene en la reconstrucción de días anteriores.
- **Esperado:** corte `500.00`; día 22 `520.05`; día 21 `419.95`. No debe aparecer `479.95` ni `500.00` en el día 22.
- **Estado:** Aprobado local por Codex; ver tabla de ejecución.

### A03 — Día sin movimientos dentro del tramo completo

- **Precondición:** escenario base.
- **Pasos:** revisar el 2026-09-21, que no tiene movimientos registrados.
- **Esperado:** `419.95`, estado reconstruido; no `0.00` ni `null`.
- **Estado:** No ejecutado.

### A04 — Varios movimientos el mismo día y precisión de centavos

- **Precondición:** empresa con una cuenta manual COP, corte 2026-09-23, cobertura desde 2026-09-21, saldo declarado `500.20` (incluye ambos ingresos del día 22). Movimientos: ingreso `+100.10` y ingreso `+0.20` el 2026-09-22; egreso `-20.05` el 2026-09-23.
- **Pasos:** consultar la serie y la tabla; comprobar la agrupación del día 22.
- **Esperado:** importe agrupado del día 22 `+100.30`; día 21 `419.95`; día 22 `520.25`; corte `500.20`. La aritmética debe ser Decimal exacta, sin artefactos binarios como `100.30000000000001`.
- **Estado:** No ejecutado.

### A05 — Saldo cero

- **Precondición:** una cuenta manual COP, corte 2026-09-23, saldo declarado `0.00`, sin movimientos, cobertura confirmada desde el día de corte.
- **Pasos:** consultar la serie.
- **Esperado:** corte `0.00` con estado declarado; días anteriores `null` / `unknown`. El cero es un valor válido y no debe confundirse con ausencia de dato.
- **Estado:** No ejecutado.

### A06 — Saldo negativo

- **Precondición:** una cuenta manual COP, corte 2026-09-23, saldo declarado `-25.50`, sin movimientos, cobertura confirmada desde el día de corte.
- **Pasos:** consultar la serie y la tabla.
- **Esperado:** corte `-25.50`; no se recorta a cero ni se muestra como `null`. Días anteriores `null` / `unknown`.
- **Estado:** No ejecutado.

### A07 — Intersección de cobertura entre cuentas

- **Precondición:** dos cuentas manuales COP con corte común 2026-09-23.
  - Cuenta A: saldo `500.00`; ingreso `+100.10` el 2026-09-22; egreso `-20.05` el 2026-09-23; cobertura desde 2026-09-21.
  - Cuenta B: saldo `200.00`; egreso `-50.00` el 2026-09-22; sin movimientos el 2026-09-23; cobertura desde 2026-09-22.
- **Pasos:** consultar la serie consolidada y la procedencia por cuenta.
- **Esperado:** inicio común de cobertura 2026-09-22 (`max(2026-09-21, 2026-09-22)`).
  - 2026-09-21: `null` / `unknown`, aunque la cuenta A tenga cobertura desde el 21.
  - 2026-09-22: `520.05 + 200.00 = 720.05`.
  - 2026-09-23: `500.00 + 200.00 = 700.00`.
  - Procedencia: A desde 2026-09-21; B desde 2026-09-22; ambas cuentas visibles.
- **Estado:** No ejecutado.

### A08 — Cobertura antigua que no alcanza el corte actual

- **Precondición:** una cuenta manual COP con corte declarado 2026-09-23, saldo `500.00` y los movimientos del escenario base, pero cobertura confirmada solo hasta 2026-09-20.
- **Pasos:** consultar la serie sin ampliar ni reconfirmar la cobertura.
- **Esperado:** el corte conserva `500.00` como saldo declarado; los días 2026-09-21, 2026-09-22 y cualquier día anterior al corte quedan `null` / `unknown`. No se extrapola la cobertura antigua ni se muestran `419.95` o `520.05`.
- **Estado:** No ejecutado.

### A09 — Revocación por entrada nueva en el periodo confirmado

- **Precondición:** escenario base con cobertura confirmada desde 2026-09-21.
- **Pasos:**
  1. Registrar un ingreso nuevo de `+10.00` el 2026-09-22, dentro del periodo confirmado.
  2. Consultar la serie antes de reconfirmar.
  3. Actualizar el saldo declarado al corte a `510.00`, de modo que incluya el nuevo ingreso, y reconfirmar la cobertura desde 2026-09-21.
  4. Consultar de nuevo la serie.
- **Esperado:**
  - Antes de reconfirmar: serie histórica invalidada; días anteriores al corte `null` / `unknown`; el corte mantiene el saldo declarado vigente.
  - Después de actualizar y reconfirmar: día 21 `419.95`; día 22 `530.05`; corte `510.00`. El día 21 no cambia porque el nuevo ingreso pertenece al día 22 y también se descuenta al reconstruir el 21.
- **Estado:** Aprobado local por Codex; ver tabla de ejecución.

### A10 — Revocación por importación en el periodo confirmado

- **Precondición:** escenario base con cobertura confirmada desde 2026-09-21.
- **Pasos:** importar un movimiento sintético dentro del periodo confirmado, por ejemplo un ingreso de `+10.00` el 2026-09-22. Consultar la serie antes y después de actualizar el saldo declarado y reconfirmar.
- **Esperado:** misma invalidación y mismas cifras que A09: `null` / `unknown` antes de reconfirmar; después, día 21 `419.95`, día 22 `530.05`, corte `510.00`.
- **Estado:** No ejecutado.

### A11 — Obligaciones y liquidaciones futuras no se deducen

- **Precondición:** escenario base más un cobro futuro de `119.00` en corte+10, un pago futuro de `700.00` en corte+15 y una conciliación de un pago ya registrado al corte.
- **Pasos:** consultar **Historial y categorías**.
- **Esperado:** la serie histórica no cambia: día 21 `419.95`, día 22 `520.05`, corte `500.00`. Ningún compromiso futuro se resta del saldo histórico.
- **Estado:** No ejecutado.

### A12 — Usuario lector

- **Precondición:** usuario con rol lector en la empresa del escenario base.
- **Pasos:** abrir **Historial y categorías** y consultar gráfico, tabla y procedencia; intentar confirmar cobertura o editar datos.
- **Esperado:** el lector ve las mismas cifras y la procedencia; no dispone de acciones de confirmación, edición ni captura. No se altera la serie.
- **Estado:** No ejecutado.

### A13 — Usuario de otra empresa (aislamiento)

- **Precondición:** usuario autenticado sin membresía en la empresa del escenario base.
- **Pasos:** intentar acceder a la empresa y consultar su historial.
- **Esperado:** no se exponen cuentas, movimientos, `balance_history` ni procedencia de la empresa ajena. La interfaz debe rechazar el acceso o mostrar una vista vacía sin datos.
- **Estado:** No ejecutado.

### A14 — Cierre de sesión y recarga

- **Precondición:** escenario base consultado correctamente.
- **Pasos:** cerrar sesión, comprobar que el historial no es accesible, volver a entrar, recargar la página y consultar de nuevo.
- **Esperado:** tras cerrar sesión no se muestran datos financieros; tras volver a entrar y recargar, la serie y la procedencia coinciden con A01. No debe haber caché de otra empresa ni valores obsoletos.
- **Estado:** No ejecutado.

### A15 — Recorte al periodo visible de 12 meses

- **Precondición:** empresa con cobertura confirmada desde una fecha anterior a los últimos 12 meses; corte 2026-09-23.
- **Pasos:** consultar la serie con el periodo visible de últimos 12 meses.
- **Esperado:** la serie comienza en el inicio del periodo visible, no antes; los días fuera del periodo no se muestran. El inicio efectivo es `max(inicio de cobertura, inicio visible)`. No se inventan valores fuera del periodo.
- **Estado:** Aprobado local por Codex; ver tabla de ejecución.

### A16 — Gráfico numérico y tabla accesible

- **Precondición:** escenario base.
- **Pasos:** revisar el gráfico y la tabla diaria con lector de pantalla o navegación por teclado.
- **Esperado:** el gráfico presenta la serie numérica sin bandas ni probabilidades no contractuales; la tabla diaria accesible contiene fecha, saldo y estado; una segunda tabla muestra procedencia y cobertura por cuenta. Los importes de las tablas conservan centavos exactos, aunque el gráfico use números de presentación. Los días `null` se anuncian como desconocidos, no como cero.
- **Estado:** No ejecutado.

## 5. Registro de ejecución

| Caso | Estado | Evidencia | Observaciones |
|---|---|---|---|
| A01 | Aprobado local | Navegador y pruebas API | Navegador: 419,95 / 520,05 / 500,00; día20 Sin cobertura y procedencia manual visible |
| A02 | Aprobado local | Navegador y pruebas API | Navegador: corte500,00 y cierre22=520,05, sin volver a restar20,05 |
| A03 | No ejecutado | Pendiente | Sin verificación |
| A04 | No ejecutado | Pendiente | Sin verificación |
| A05 | No ejecutado | Pendiente | Sin verificación |
| A06 | No ejecutado | Pendiente | Sin verificación |
| A07 | No ejecutado | Pendiente | Sin verificación |
| A08 | No ejecutado | Pendiente | Sin verificación |
| A09 | Aprobado local | Navegador y pruebas API | Navegador: +10 el22 invalida; saldo510 y reconfirmación producen419,95 / 530,05 / 510,00 |
| A10 | No ejecutado | Pendiente | Sin verificación |
| A11 | No ejecutado | Pendiente | Sin verificación |
| A12 | No ejecutado | Pendiente | Sin verificación |
| A13 | No ejecutado | Pendiente | Sin verificación |
| A14 | No ejecutado | Pendiente | Sin verificación |
| A15 | Aprobado local | Navegador y pruebas API | Navegador: rangos30/90/anual muestran30/90/358 fechas en este corte; límite cubierto también por API |
| A16 | Parcial | Tabla diaria y procedencia comprobadas | Falta ensayo completo de lector de pantalla/teclado |

## 6. Limitaciones de esta guía

- No sustituye una prueba de aceptación ejecutada ni una verificación bancaria independiente.
- No fija requisitos de producto nuevos ni modifica el contrato de implementación.
- No incluye acceso a producción, datos reales ni credenciales.
- Las cifras son contractuales y deben comprobarse contra la implementación de Codex; cualquier discrepancia debe registrarse como fallo, no ajustarse en esta guía.
- La disponibilidad de la sección, los roles y los mensajes exactos de la interfaz deben confirmarse en el entorno local durante la ejecución.

## 7. Verificación automatizada y límites

- PostgreSQL/Docker: **247 pruebas; 245 aprobadas y 2 omitidas** (demo exclusiva de SQLite).
- SQLite local: **247 pruebas; 240 aprobadas y 7 omitidas** (bloqueos PostgreSQL y precisión extrema de persistencia Decimal).
- Doce regresiones backend nuevas en `test_balance_history.py`: cierres, huecos, todas las cuentas,
  fuente/manual, tenant/roles, importación/captura que revocan cobertura, cambio de saldo,
  importes negativos, máximos, centavos y conciliación sin doble descuento.
- Ocho pruebas frontend totales: cuatro nuevas para huecos, importes exactos, cero y rangos.
  Build TypeScript/Vite (651 módulos), Ruff (210 archivos), formato y migraciones sin cambios.
- Tres pruebas Node de escritorio aprobadas. No se ejecutó CI remoto ni despliegue.
- El cálculo puro usa Decimal también en SQLite. La precisión extrema de la persistencia se
  acredita en PostgreSQL; SQLite no debe usarse para validar importes de ese tamaño.

La cuenta de prueba y la empresa «QA Saldos 2026-10-30» se crearon de forma separada;
no se borraron ni reiniciaron empresas anteriores. Se observó que una reconstrucción del
frontend reinicia la selección de empresa a la primera disponible: su persistencia al
recargar continúa como hallazgo transversal de T14, fuera del cálculo P05.
La declaración manual y la cobertura no certifican un extracto bancario. A14 y la
aceptación de accesibilidad completa permanecen pendientes; no se marcan por inferencia.
