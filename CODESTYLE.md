# Convenciones de código

## Principios

Monolito modular Django/DRF y frontend React/TypeScript. Entregar cortes funcionales pequeños,
con estado de implementación documentado. No presentar escenarios determinísticos como modelos
probabilísticos ni datos sintéticos como información bancaria real.

## Python

- Python 3.13, indentación de cuatro espacios, UTF-8 y finales LF.
- Ruff para formato y lint; nombres `snake_case`, clases `PascalCase`, constantes `UPPER_SNAKE_CASE`.
- Servicios de dominio separados de HTTP y del ORM cuando sea práctico. No incorporar lógica financiera en componentes React.
- Imports absolutos entre módulos; relativos dentro de un módulo. No usar `import *`.
- Type hints en nuevos contratos públicos; docstrings para supuestos financieros y reglas no evidentes.
- Usar `Decimal` para dinero y serializar montos como cadenas. `Number` solo para presentación/gráficos.
- Fechas de negocio ISO 8601 y zona America/Bogota; timestamps con zona horaria.

## TypeScript y UI

- TypeScript estricto, componentes funcionales y hooks. Evitar `any`.
- Dos espacios, punto y coma y comillas simples. `PascalCase` para componentes/tipos y `camelCase` para funciones.
- CSS independiente con variables/tokens cuando haya reutilización. No añadir un framework de estilos sin necesidad.
- Interfaz y errores en español; identificadores técnicos en inglés.
- Toda carga remota requiere estados de carga, error y vacío; cancelar solicitudes obsoletas.
- Formularios con etiquetas, navegación por teclado, foco visible y alternativas textuales para gráficos.

## Seguridad y datos

- Obtener el tenant desde la membresía autenticada; un ID enviado por el cliente nunca autoriza acceso.
- No habilitar acceso financiero implícito para administradores de plataforma. Los roles de escritura se comprobarán al agregar mutaciones.
- Cookies de sesión HttpOnly y protección CSRF, incluido login; nunca guardar tokens en localStorage.
- Sin secretos en Git, respuestas API o logs. `.env.example` contiene solo marcadores.
- Restricciones de idempotencia e integridad en base de datos, además de validación de entrada.
- Migraciones versionadas. Prohibido modificar una migración ya desplegada: agregar otra.
- Jobs futuros deben ser idempotentes, mantener tenant y consentimiento, registrar estado y ejecutarse tras commit.

## Dependencias y pruebas

- Instalar backend desde `requirements.txt` y frontend con `npm ci`; actualizar locks junto con cambios deliberados de versiones.
- Verificar reglas de dinero, fechas límite, aislamiento, autenticación y duplicados con pruebas de comportamiento.
- Cada nueva integración requiere pruebas de contrato y fallos/reintentos. No usar datos privados en fixtures.
- Antes de entregar: `ruff check backend`, `ruff format --check backend`, `python backend/manage.py test backend/tests`, `npm run build` dentro de frontend.
- Describir qué se verificó y qué depende de un entorno externo; no afirmar que un build sustituye pruebas de navegador.
