import assert from 'node:assert/strict';
import test from 'node:test';
import { balanceChartPoints, exactCop, selectBalancePoints } from '../src/balanceHistory.ts';

test('an unknown balance is a gap, never a zero balance on the chart', () => {
  const points = [
    { date: '2026-09-20', balance: null, status: 'unknown' },
    { date: '2026-09-21', balance: '0.00', status: 'reconstructed' },
    { date: '2026-09-22', balance: '-0.01', status: 'reconstructed' },
    { date: '2026-09-23', balance: '500.00', status: 'declared' },
  ];
  const chart = balanceChartPoints(points);
  assert.deepEqual(chart.map(point => point.balance), [null, 0, -0.01, 500]);
  assert.deepEqual(chart.map(point => point.status), ['unknown', 'reconstructed', 'reconstructed', 'declared']);
  assert.equal(points[3].balance, '500.00');
});

test('daily table preserves cents beyond safe floating point precision', () => {
  assert.equal(exactCop('9999999999999999.99'), '$ 9.999.999.999.999.999,99');
  assert.equal(exactCop('-9999999999999999.99'), '-$ 9.999.999.999.999.999,99');
  assert.equal(exactCop('419.95'), '$ 419,95');
  assert.equal(exactCop('-0.01'), '-$ 0,01');
});

test('missing, zero and invalid amounts have distinct accessible labels', () => {
  assert.equal(exactCop(null), 'Sin cobertura');
  assert.equal(exactCop('0.00'), '$ 0,00');
  assert.equal(exactCop('NaN'), 'Saldo no disponible');
});

test('history ranges end at the declared cut and preserve gaps without changing source data', () => {
  const points = Array.from({ length: 100 }, (_, index) => ({
    date: new Date(Date.UTC(2026, 5, index + 1)).toISOString().slice(0, 10),
    balance: index < 98 ? null : '500.00',
    status: index < 98 ? 'unknown' : index === 99 ? 'declared' : 'reconstructed',
  }));
  assert.equal(selectBalancePoints(points, '30').length, 30);
  assert.equal(selectBalancePoints(points, '90').length, 90);
  assert.equal(selectBalancePoints(points, 'all').length, 100);
  assert.equal(selectBalancePoints(points, '30')[0].balance, null);
  assert.equal(selectBalancePoints(points, '30').at(-1), points.at(-1));
  assert.equal(points.length, 100);
});
