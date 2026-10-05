# Instalador Windows de pruebas

Artefacto local comprobado el 5 de octubre de 2026:
`desktop/release/session-isolation/Horizonte Setup 0.1.0.exe`.

- Windows x64, Electron 44.5.1, NSIS, versión 0.1.0.
- Tamaño: 111.312.733 bytes.
- SHA-256: `2971179c76f0919fda334d5e5a2ef5a65c9a8c714f4850740f3df9b071e3be6d`.
- Sin firma de editor; el hash identifica esta copia, no acredita un editor ni reemplaza una firma.
- Servidor de pruebas: `https://horizonte-demo.onrender.com`; necesita internet, sin Docker local.
- Los cinco archivos del cliente en `app.asar` se compararon byte a byte con el fuente:
  `main.cjs`, `endpoint.cjs`, `setup-preload.cjs`, `setup.html`, `setup.js`.
- Smoke del ejecutable empaquetado: configurador, Node oculto, HTTP externo rechazado,
  permisos denegados y borrado de cookie persistente sin ventana remota, comprobados.
- Instalación/desinstalación en Windows limpio y recorrido visual remoto completo pendientes.
  No se declara aceptación de escritorio por tener una huella o un build correcto.

Para verificar una copia desde la raíz del proyecto:

```powershell
Get-FileHash 'desktop/release/session-isolation/Horizonte Setup 0.1.0.exe' -Algorithm SHA256
Get-AuthenticodeSignature 'desktop/release/session-isolation/Horizonte Setup 0.1.0.exe'
```

Si la huella difiere, comprobar la procedencia y versión antes de usarla. Una compilación
nueva puede producir otro hash; no reutilizar esta huella para certificar otro binario.
El ejecutable permanece local y no se publicó como release descargable en GitHub.
Seguir `DESKTOP_ACCEPTANCE.md` para las pruebas funcionales pendientes.
