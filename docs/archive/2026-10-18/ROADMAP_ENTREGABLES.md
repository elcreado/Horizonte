> Archivo histórico previo a la auditoría documental del 18 de octubre de 2026.
> No usar como estado ni arranque vigente. Ver [índice actual](../../README.md).

> Actualización 16 de octubre de 2026: la prioridad vigente es la V1 web manual, implementada localmente en `codex/v1-manual-transactions`. Escritorio y móvil están aplazados. Consultar [estado actual](../../IMPLEMENTATION_STATUS.md) y [recorrido](../../PLAN_DEMO_FUNCIONAL.md); los entregables académicos inferiores mantienen sus límites.

# Hoja de ruta vigente

Revisión: **16 de octubre de 2026**. La prioridad actual es la aplicación web útil y
presentable, con transacciones manuales. No se eliminan los objetivos académicos originales:
sus brechas están en [estado y pendientes](../../ESTADO_Y_PENDIENTES.md).

## Etapa actual: demostrar la idea desde la web

Seguir el [plan de demostración](../../PLAN_DEMO_FUNCIONAL.md). El reparto concreto por dificultad,
paralelismo y bloqueos está en el [roadmap para agentes IA](../../ROADMAP_TRABAJO_IA.md).

- [ ] Implementar captura manual segura de ingresos/egresos, sin alterar dos veces el saldo.
- [ ] Integrar clasificación, histórico, cobertura y refresco de vistas.
- [ ] Verificar cobros/pagos, conciliación y proyección con resultados esperados.
- [ ] Preparar caso repetible y guía de presentación.
- [ ] Ejecutar QA de navegador y comprobar la versión publicada.

Presupuesto inicial 0 USD; suspensión del servicio gratuito aceptada. Respaldo manual únicamente.
No se exige correo real para mostrar el recorrido con una cuenta conocida, pero su ausencia
debe declararse. No se exige perfeccionar el modelo estadístico antes de demostrar el escenario.

## Escritorio: disponible, mejoras aplazadas

- [x] Cliente Windows x64 Electron/NSIS con Inicio sin sesión y servidor HTTPS configurable.
- [x] React/Django y PostgreSQL alojados para uso sin Docker local; importaciones y cola disponibles.
- [ ] Aceptación en Windows limpio: instalación, flujo financiero, reintentos y desinstalación.
- [ ] Firma, distribución y actualización del instalador.

Para probar: Windows x64 e internet. El cliente depende del servidor y no ofrece modo offline.
Estas tareas no bloquean la demostración web actual.

## Completar los objetivos originales

- [ ] Administración de plataforma conforme al actor definido en README.
- [ ] Gráfico de saldo histórico real y revisión de todos los gráficos RF-14.
- [ ] Modelo híbrido/recurrencias/clasificación sobre corpus independiente y temporalmente válido.
- [ ] Calibración de cuantiles, riesgo/factores y confianza con evidencia por segmento.
- [ ] Comparación de modelos acordada, incluida decisión explícita sobre Prophet.
- [ ] ASVS, rendimiento con carga/renderizado, disponibilidad y accesibilidad comprobados.
- [ ] OpenAPI, despliegue completo reproducible y entrega académica consolidada.

## Segunda versión

- [ ] **Port Android/iOS:** reutilizar el backend HTTPS y evaluar reutilización de React;
  adaptar navegación, carga de archivos, gráficos y autenticación/CSRF de WebView.
- [ ] QA en dispositivos reales, funcionamiento ante conectividad irregular y distribución.
  Confirmar herramientas de Android y entorno macOS para iOS al ejecutar la fase, con costes
  autorizados; no prometer publicación gratuita en tiendas sin comprobar sus condiciones.
- [ ] Conector externo autorizado y facturación de proveedor cuando aporte valor frente al XML.
- [ ] Notificaciones opt-in, observabilidad, actualizaciones del cliente y soporte.
- [ ] Modelos nuevos solo tras comparación que justifique incorporarlos; supervisión de deriva.

No incluir transferencias, banca de producción ni contabilidad oficial silenciosamente.
La [hoja anterior](../2026-10-05/ROADMAP_ENTREGABLES.md) se conserva como historia, no como plan vigente.
