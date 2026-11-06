import assert from 'node:assert/strict';
import test from 'node:test';
import { createMonthlySubmission } from '../src/monthlySubmission.ts';

const payroll = { description: 'Sueldos', amount: '1000000.00', day: '1', direction: 'out', start_date: '2026-11-01', end_date: '' };

test('lost response keeps the UUID and original payload even when retry fields are empty or changed', () => {
  let ids = 0;
  const attempt = createMonthlySubmission(() => `request-${++ids}`);
  const fields = { ...payroll };
  const original = attempt.capture(fields);
  fields.amount = '2000000';
  assert.equal(attempt.capture({}), original);
  assert.equal(attempt.capture(fields), original);
  assert.equal(original.amount, '1000000.00');
  assert.equal(original.end_date, null);
  assert.equal(ids, 1);
  assert.equal(attempt.isPending(), true);
});

test('server failure preserves the original request; confirmed replay allows a new payroll', () => {
  let ids = 0;
  const attempt = createMonthlySubmission(() => `request-${++ids}`);
  const original = attempt.capture(payroll);
  attempt.settle(503);
  assert.equal(attempt.capture({ ...payroll, day: '2' }), original);
  attempt.settle(200);
  assert.equal(attempt.isPending(), false);
  const next = attempt.capture({ ...payroll, day: '2' });
  assert.notEqual(next.request_id, original.request_id);
  assert.equal(next.day, '2');
});

test('a definitive validation error releases editing and uses a new key for corrected data', () => {
  let ids = 0;
  const attempt = createMonthlySubmission(() => `request-${++ids}`);
  const original = attempt.capture({ ...payroll, amount: '0' });
  attempt.settle(400);
  assert.equal(attempt.isPending(), false);
  const corrected = attempt.capture(payroll);
  assert.equal(corrected.amount, '1000000.00');
  assert.notEqual(corrected.request_id, original.request_id);
});

test('two intentional identical payroll creations receive distinct keys', () => {
  let ids = 0;
  const attempt = createMonthlySubmission(() => `request-${++ids}`);
  const first = attempt.capture(payroll);
  attempt.settle(201);
  const second = attempt.capture(payroll);
  assert.notEqual(first.request_id, second.request_id);
  assert.throws(() => { first.amount = '0'; }, TypeError);
});
