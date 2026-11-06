import assert from 'node:assert/strict';
import test from 'node:test';
import { forgetCompany, readCompanyPreference, rememberCompany, resolveCompany } from '../src/companySelection.ts';

function memoryStorage() {
  const values = new Map();
  return {
    values,
    getItem: key => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    removeItem: key => values.delete(key),
  };
}

test('a second company is restored from storage only for the same authenticated user', () => {
  const storage = memoryStorage();
  rememberCompany(() => storage, 'ana', '8');
  const saved = readCompanyPreference(() => storage);
  assert.equal(resolveCompany([{ id: 7 }, { id: 8 }], 'ana', saved), '8');
  assert.equal(resolveCompany([{ id: 7 }, { id: 8 }], 'other', saved), '7');
  assert.deepEqual(JSON.parse([...storage.values.values()][0]), { username: 'ana', companyId: '8' });
});

test('a removed or forged company is never restored and an empty membership list stays empty', () => {
  const preference = { username: 'ana', companyId: '999' };
  assert.equal(resolveCompany([{ id: 7 }, { id: 8 }], 'ana', preference), '7');
  assert.equal(resolveCompany([], 'ana', preference), '');
  assert.equal(resolveCompany([{ id: 7 }], 'ana', { username: 'ana', companyId: '07' }), '7');
});

test('malformed or missing browser preferences fall back safely', () => {
  const storage = memoryStorage();
  assert.equal(readCompanyPreference(() => storage), null);
  rememberCompany(() => storage, 'ana', '8');
  const key = [...storage.values.keys()][0];
  for (const raw of ['{', 'null', '7', '[]', '{}', '{"username":null,"companyId":"8"}', '{"username":"ana","companyId":8}']) {
    storage.setItem(key, raw);
    assert.equal(readCompanyPreference(() => storage), null);
  }
});

test('denied storage getter, reads, writes and removal never interrupt company selection', () => {
  const denied = () => { throw new Error('Storage denied'); };
  assert.equal(readCompanyPreference(denied), null);
  assert.doesNotThrow(() => rememberCompany(denied, 'ana', '8'));
  assert.doesNotThrow(() => forgetCompany(denied));
  const storage = {
    getItem: denied, setItem: denied, removeItem: denied,
  };
  assert.equal(readCompanyPreference(() => storage), null);
  assert.doesNotThrow(() => rememberCompany(() => storage, 'ana', '8'));
  assert.doesNotThrow(() => forgetCompany(() => storage));
  assert.equal(resolveCompany([{ id: 8 }], 'ana', null), '8');
});

test('logout and an empty authorized list remove the preference instead of storing a blank company', () => {
  const storage = memoryStorage();
  rememberCompany(() => storage, 'ana', '8');
  forgetCompany(() => storage);
  assert.equal(storage.values.size, 0);
  rememberCompany(() => storage, 'ana', '8');
  rememberCompany(() => storage, 'ana', '');
  assert.equal(storage.values.size, 0);
});
