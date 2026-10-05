const test = require('node:test');
const assert = require('node:assert/strict');
const { validateEndpoint } = require('../endpoint.cjs');
test('acepta origen HTTPS y normaliza barra final', () => assert.equal(validateEndpoint('https://demo.example.com/'), 'https://demo.example.com'));
test('no permite secretos, rutas ni protocolos no web', () => {
  for (const url of ['https://user:pass@example.com', 'https://example.com/api', 'https://example.com?token=secret', 'https://example.com/#login', 'file:///C:/secret', 'http://example.com']) assert.throws(() => validateEndpoint(url));
});
test('HTTP local solo es válido en desarrollo', () => {
  assert.equal(validateEndpoint('http://127.0.0.1:8000', true), 'http://127.0.0.1:8000');
  assert.throws(() => validateEndpoint('http://127.0.0.1:8000'));
  assert.throws(() => validateEndpoint('http://external.example.com', true));
});
