# Revisión de coherencia — 23 de septiembre de 2026

La arquitectura propuesta es adecuada para una tesis de 24 semanas si se entrega por fases.
El alcance documental original describe la meta completa, no una aplicación ya implementada.

| Hallazgo | Decisión |
|---|---|
| MVP demasiado amplio para el arranque | v0.1: sesión, membresías, saldos, movimientos sintéticos, obligaciones y escenario diario. CSV/ETL, XML y modelos se implementan después. |
| Autenticación propia confundida con OAuth bancario | Sesiones Django + CSRF para la app. OAuth/OIDC + PKCE se evaluará para cada proveedor. |
| Argon2 supuesto por defecto | Se instala argon2-cffi y se configura Argon2PasswordHasher primero. |
| Rangos de historial superpuestos | 0–29, 30–89, 90–364 y ≥365 días, sin prometer precisión a partir de antigüedad solamente. |
| Caja, facturas, CxC/CxP y recurrencias pueden duplicar flujos | Las obligaciones representan saldos pendientes; las proyecciones futuras deben conciliar fuentes y excluir componentes ya modelados. |
| Monedas y fechas de saldo no definidas | Primera versión solo COP y un corte común por empresa; rechazar consolidación incompatible. |
| XML no aporta necesariamente fecha de pago o saldo pendiente | Vencimiento requiere política explícita si falta; pago se obtiene de conciliación/evidencia, no del estado inferido del XML. |
| Disponibilidad de proveedores asumida | Cada sandbox requiere verificar cobertura, acceso y contrato antes de comprometer la integración. |
| Administrador de plataforma confundido con miembro | `is_staff`/`is_superuser` no otorgan acceso automático a datos financieros en la API. Membresías owner/accountant/viewer para lectura inicial. |
| Requisitos de rendimiento sin protocolo | Medir p95, volumen, hardware y concurrencia; no declarar cumplido el objetivo de 2 s sin medición. |
| Métricas de clasificación ambiguas | Medir cobertura y exactitud por separado sobre conjunto etiquetado; 80% de cobertura no equivale a 80% de acierto. |
| DLDE indefinido cuando falta un déficit | Calcularlo solo si ambos eventos existen; reportar aparte falsos positivos, falsos negativos y casos sin evento. |

## Reglas para la siguiente fase predictiva

P50 es la mediana, no necesariamente la media. P10/P50/P90 se obtendrán de una distribución
predictiva y se evaluarán por cobertura y pinball loss; no se fabricarán sumando porcentajes.
La banda P10–P90 es un intervalo predictivo nominal del 80%, no un intervalo de confianza
del parámetro. La probabilidad de déficit en cualquier día requiere trayectorias conjuntas,
no se deduce solamente de cuantiles marginales.

Los pagos registrados afectan el saldo observado una sola vez. Las obligaciones vencidas necesitan
fecha estimada y estado explícitos: no se trasladan silenciosamente al día siguiente. El entrenamiento
rolling-origin solo utilizará información disponible en cada corte, incluidos estados de facturas;
se excluirán flujos ya representados por obligaciones/recurrencias para evitar doble conteo.

## Fuentes contrastadas

- [Django: configuración de contraseñas](https://docs.djangoproject.com/en/5.2/topics/auth/passwords/).
- [Decreto 368 de 2026, texto oficial](https://www.funcionpublica.gov.co/eva/gestornormativo/norma_pdf.php?i=275576).
- [RFC 10017, OAuth para aplicaciones en navegador](https://www.rfc-editor.org/rfc/rfc10017.html).

La referencia normativa no certifica cumplimiento. Las cifras de supervivencia, las afirmaciones
comparativas sobre ERP y el estado de cada proveedor requieren bibliografía específica antes de
presentar el documento académico. Se elimina la afirmación causal no sustentada del primer párrafo.
