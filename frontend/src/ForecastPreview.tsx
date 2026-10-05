import { useEffect, useState } from 'react';
import { ForecastChart } from './ForecastChart';
import { ForecastRuns } from './ForecastRuns';

type Point = { p10?: string; p50?: string; p90?: string; date: string; known_flow: string; recurring_flow?: string; estimated_flow: string; balance: string };
type Preview = { quantiles?: { status: string; notice: string }; method: string; status: string; notice: string; training_start: string; as_of: string; training_days: number; observed_movements: number; excluded_recurring_movements: number; estimated_recurrence_occurrences: number; first_deficit: string | null; minimum_balance: string; points: Point[] };
const money = (value: string | number) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(Number(value));

export function ForecastPreview({ company, horizon, revision }: { company: string; horizon: number; revision: number }) {
  const [method, setMethod] = useState('hybrid_weekly');
  const [data, setData] = useState<Preview | null>(null);
  const [unavailable, setUnavailable] = useState('');
  const [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController(); setData(null); setUnavailable(''); setError('');
    fetch(`/api/companies/${company}/experimental-forecast/?horizon=${horizon}&method=${method}`, { signal: controller.signal }).then(async response => {
      const result = await response.json();
      if (response.status === 409) { setUnavailable(result.detail || 'Faltan datos para esta referencia.'); return; }
      if (!response.ok) throw new Error(result.detail || 'No se pudo calcular la referencia estadística.');
      setData(result);
    }).catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [company, horizon, method, revision]);
  return <section className="panel"><h2>Pronóstico híbrido experimental</h2><label>Método<select value={method} onChange={event => setMethod(event.target.value)}><option value="hybrid_weekly">Patrón semanal y recurrencias confirmadas</option><option value="seasonal_naive">Repetir patrón semanal</option><option value="naive">Repetir último flujo diario</option><option value="ses">Suavizado exponencial simple</option></select></label>
    {error && <p className="error" role="alert">{error}</p>}{unavailable && <p role="status">{unavailable}</p>}{!data && !error && !unavailable && <p role="status">Calculando referencia…</p>}
    {data && <><p>{data.notice}</p>{data.quantiles && <p role="status">{data.quantiles.notice}</p>}<p>Entrenamiento: {data.training_start} a {data.as_of} ({data.training_days} días, {data.observed_movements} movimientos). Movimientos recurrentes excluidos: {data.excluded_recurring_movements}.</p><p>Saldo mínimo estimado: {money(data.minimum_balance)}. {data.first_deficit ? `Primer déficit estimado: ${data.first_deficit}.` : 'Sin déficit en esta referencia.'}</p><ForecastChart points={data.points} quantiles={data.quantiles?.status === 'experimental'} /><details><summary>Ver flujos y saldos diarios</summary><div className="table-wrap"><table><thead><tr><th>Fecha</th><th>Obligaciones COP</th><th>Recurrencias estimadas COP</th><th>Variable estimado COP</th><th>Saldo puntual COP</th>{data.quantiles?.status === 'experimental' && <><th>P10 COP</th><th>P50 COP</th><th>P90 COP</th></>}</tr></thead><tbody>{data.points.map(point => <tr key={point.date}><td>{point.date}</td><td>{money(point.known_flow)}</td><td>{money(point.recurring_flow || '0')}</td><td>{money(point.estimated_flow)}</td><td>{money(point.balance)}</td>{data.quantiles?.status === 'experimental' && <><td>{point.p10 === undefined ? '—' : money(point.p10)}</td><td>{point.p50 === undefined ? '—' : money(point.p50)}</td><td>{point.p90 === undefined ? '—' : money(point.p90)}</td></>}</tr>)}</tbody></table></div></details></>}
    <ForecastRuns company={company} horizon={horizon} method={method} ready={Boolean(data)} />
  </section>;
}
