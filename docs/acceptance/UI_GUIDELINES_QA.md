# Interfaz intuitiva y Web Interface Guidelines

Verificación: **5 de noviembre de 2026**, rama `codex/v1-manual-transactions`.
[Guías de Vercel consultadas](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md).
Alcance: navegación del dashboard, Resumen, captura manual, programaciones mensuales,
lectura de gráficos y estilos compartidos. No certifica accesibilidad integral.

## Cambios

- Sidebar con iconos decorativos y sección activa; menú móvil con botón, estado expandido,
  cierre por navegación/Escape y retorno de foco.
- Accesos directos a registrar movimientos, programar pagos e importar; estado vacío con
  siguiente paso. El método y las limitaciones permanecen accesibles en un desplegable.
- Formulario manual con introducción breve, ayuda por campo y radios ingreso/egreso;
  controles nativos, teclado decimal, fecha predeterminada hoy de Colombia y pasado permitido.
- Detener una programación requiere confirmación; Mantener programación devuelve el foco
  y no ejecuta cancelación. Las reglas financieras y los recibos de reintento se conservan.
- Escala del gráfico adaptada a magnitud; cifras tabulares, foco visible, estados hover,
  controles móviles de 16 px y reducción de movimiento. Barras del histórico sin animación.

## Aceptación ejecutada

| Caso | Resultado esperado | Evidencia local |
|---|---|---|
| UI-01 | Sidebar de escritorio conserva diez destinos y sección activa. | Aprobado visual/DOM, ventana predeterminada de 1265 px. |
| UI-02 | Menú móvil cerrado inicialmente; botón expone aria-expanded/controls. | Aprobado a 390 px. |
| UI-03 | Escape cierra menú y devuelve foco; cambiar sección cierra menú y enfoca main. | Aprobado en navegador. |
| UI-04 | Acciones frecuentes llevan a sus secciones. | Destinos revisados en DOM; Movimientos y Cobros y pagos recorridos. |
| UI-05 | Método completo disponible sin saturar tarjetas; estado vacío ofrece acción. | Desplegable y caja vacía observados en empresa QA de saldos. |
| UI-06 | Ingreso/egreso seleccionable por teclado y etiquetas; importes obligatorios. | Flecha izquierda seleccionó Ingreso; envío vacío enfocó amount, sin crear movimiento. |
| UI-07 | Fecha inicial hoy de Colombia y ayuda de pasado. | Observado 2026-11-05; restricción max conservada; no se creó una operación. |
| UI-08 | Botón Detener abre confirmación; Mantener conserva activa y devuelve foco. | Aprobado sobre Nómina QA conexión; no se confirmó detención. Ejecución del POST tras confirmación pendiente en UI. |
| UI-09 | Página sin desbordamiento horizontal; tablas confinadas a su contenedor. | Resumen/Movimientos a 390 px, Cobros y pagos a 390/650 px, Fuentes a 320 px. Anchos útiles 375/635/305 iguales a scrollWidth. No sustituye revisión de todas las secciones. |
| UI-10 | Saltar al contenido funciona por teclado. | Enter enfocó MAIN en Fuentes de datos. |
| UI-11 | Cifras pequeñas no aparecen como fracciones de millón. | Eje observado 250/500/750/1 K con saldo sintético 510 COP. Valores financieros conservados. |
| UI-12 | Reducción de movimiento y anuncios no impiden entender resultados. | CSS y gráficos revisados; status/alert existentes conservados. Lector de pantalla y preferencia real del sistema pendientes. |

## Comprobación técnica

Docker: 13 pruebas frontend aprobadas; TypeScript/Vite compilados (655 módulos).
PostgreSQL: 247 pruebas, 245 aprobadas y dos omitidas del preparador SQLite.
No se agregaron dependencias, migraciones ni rutas API. No hubo commit, publicación,
altas manuales ni confirmación de cancelaciones durante la revisión visual.

Plan y simulación OpenCode completados en checkout limpio separado. Ejecución del
checklist agotó 60 s sin crear archivos: informes y alcance revisados; no se integró
salida delegada. Codex implementó y revisó cambios y documentación.

## Asuntos abiertos

- Auditoría completa con lector de pantalla, zoom 200 %, contraste medido de todos los
  estados, otras pantallas y todos los flujos de teclado.
- Aviso de borradores sin guardar al abandonar formularios, especialmente envíos inciertos.
- Horizonte, filtros y paginación en URL; las secciones ya tienen rutas hash.
- Errores de servidor junto a cada campo en todos los formularios; la captura manual
  anuncia y enfoca su error general, y el navegador enfoca requisitos inválidos.
- T14/T15 conservan sus pendientes de red, roles y aceptación transversal. Ver
  [roadmap](../ROADMAP_TRABAJO_IA.md) y [QA web](WEB_V1_QA.md).

## Revisión de código

```text
frontend/src/DashboardNavigation.tsx:25 - corregido: menú móvil explícito, Escape y foco devuelto al control; enlaces activos y SVG decorativos.
frontend/src/main.tsx:186 - corregido: acciones frecuentes visibles y navegación semántica.
frontend/src/main.tsx:191 - corregido: resumen legible con método y limitaciones disponibles en desplegable.
frontend/src/ManualMovement.tsx:77 - corregido: radio nativo ingreso/egreso, etiquetas y ayudas por campo.
frontend/src/MonthlySchedules.tsx:71 - corregido: confirmación previa a detener; foco seguro y retorno al origen.
frontend/src/style.css:28 - corregido: cifras tabulares y contenedores adaptables.
frontend/src/style.css:212 - corregido: movimiento reducido; barras de History sin animación.
frontend/src/DashboardChart.tsx:8 - corregido: escala compacta localizada, sin diminutas fracciones de millones.
frontend/src/ManualMovement.tsx:73 - pendiente de revisión: aviso de borrador sin guardar al abandonar la sección; la advertencia de envío incierto existente sigue visible.
frontend/src/main.tsx:97 - pendiente de revisión: horizonte y filtros no sincronizados con URL; navegación por sección sí usa hash.
```
