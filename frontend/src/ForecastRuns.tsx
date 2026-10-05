import { useEffect, useState } from 'react';
import { ForecastChart } from './ForecastChart';

type Point = { p10?: string; p50?: string; p90?: string; date: string; known_flow: string; recurring_flow?: string; estimated_flow: string; balance: string };
type Run = { id: number; created_at: string; method: string; horizon: number; as_of: string; evidence: { movements: number; source_digest: string }; result: { quantiles?: { status: string; notice: string }; minimum_balance: string; first_deficit: string | null; points: Point[] } };
type Page = { results: Run[]; count: number; next: string | null; previous: string | null; can_save: boolean };
const money = (value: string) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(Number(value));

export function ForecastRuns({ company, horizon, method, ready }: { company: string; horizon: number; method: string; ready: boolean }) {
  const [data, setData] = useState<Page | null>(null);
  const [page, setPage] = useState(1);
  const [revision, setRevision] = useState(0);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const controller = new AbortController(); setData(null); setError('');
    fetch(`/api/companies/${company}/forecast-runs/?page=${page}`, { signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error('No se pudo consultar el historial de pronósticos.');
      setData(await response.json());
    }).catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [company, page, revision]);
  async function save() {
    setBusy(true); setError('');
    try {
      const csrf = await (await fetch('/api/auth/csrf/')).json();
      const response = await fetch(`/api/companies/${company}/forecast-runs/`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf.csrfToken }, body: JSON.stringify({ horizon, method }) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'No se pudo guardar el pronóstico.');
      setPage(1); setRevision(value => value + 1);
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  return <div><h3>Historial de pronósticos experimentales</h3><p>Guarda el cálculo para consultar su saldo diario y los datos con que se generó. Si los datos no cambian, se conserva la misma ejecución.</p>
    {data?.can_save && <button disabled={busy || !ready} onClick={save}>Guardar pronóstico actual</button>}
    {error && <p className="error" role="alert">{error}</p>}
    {!data && !error && <p role="status">Cargando historial…</p>}
    {data && <>{!data.count ? <p>No hay pronósticos guardados.</p> : <div className="table-wrap"><table><thead><tr><th>Guardado</th><th>Corte</th><th>Método</th><th>Horizonte</th><th>Saldo mínimo</th><th>Detalle</th></tr></thead><tbody>{data.results.map(row => <tr key={row.id}><td>{new Date(row.created_at).toLocaleString('es-CO')}</td><td>{row.as_of}</td><td>{row.method === 'hybrid_weekly' ? 'Semanal y recurrencias' : row.method === 'naive' ? 'Último flujo diario' : row.method === 'ses' ? 'Suavizado exponencial' : 'Patrón semanal'}</td><td>{row.horizon} días</td><td>{money(row.result.minimum_balance)}</td><td><details><summary>Ver ejecución</summary><p>{row.evidence.movements} movimientos; primer déficit: {row.result.first_deficit || 'ninguno'}.</p>{row.result.quantiles && <p>{row.result.quantiles.notice}</p>}<ForecastChart points={row.result.points} quantiles={row.result.quantiles?.status === 'experimental'} /><div className="table-wrap"><table><thead><tr><th>Fecha</th><th>Obligaciones</th><th>Recurrencias estimadas</th><th>Variable estimado</th><th>Saldo puntual</th>{row.result.quantiles?.status === 'experimental' && <><th>P10</th><th>P50</th><th>P90</th></>}</tr></thead><tbody>{row.result.points.map(point => <tr key={point.date}><td>{point.date}</td><td>{money(point.known_flow)}</td><td>{money(point.recurring_flow || '0')}</td><td>{money(point.estimated_flow)}</td><td>{money(point.balance)}</td>{row.result.quantiles?.status === 'experimental' && <><td>{point.p10 === undefined ? '—' : money(point.p10)}</td><td>{point.p50 === undefined ? '—' : money(point.p50)}</td><td>{point.p90 === undefined ? '—' : money(point.p90)}</td></>}</tr>)}</tbody></table></div></details></td></tr>)}</tbody></table></div>}<button disabled={busy || !data.previous} onClick={() => setPage(value => value - 1)}>Anterior</button> <span>Página {page}</span> <button disabled={busy || !data.next} onClick={() => setPage(value => value + 1)}>Siguiente</button></>}</div>;
}
