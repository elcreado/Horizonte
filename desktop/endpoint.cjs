function validateEndpoint(value, allowLocal = false) {
  const url = new URL(value);
  const local = ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
  if (url.protocol !== 'https:' && !(allowLocal && local && url.protocol === 'http:')) {
    throw new Error('El servidor debe usar HTTPS.');
  }
  if (url.username || url.password || url.search || url.hash || url.pathname !== '/') {
    throw new Error('Introduce solo el origen del servidor, sin credenciales ni rutas.');
  }
  return url.origin;
}
module.exports = { validateEndpoint };
