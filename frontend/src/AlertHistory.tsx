import { useEffect, useRef, useState } from 'react';
type Evaluation = { id: number; created_at: string; evidence: { as_of: string; horizon: number; threshold: string; balance: string }; result: { first_below: string | null; projected_days_below: number } };
type Page = { results: Evaluation[]; count: number; next: string | null; previous: string | null; can_save: boolean };
export function AlertHistory({ company, horizon }: { company: string; horizon: number }) {
  const savingRequest = useRef<AbortController | null>(null);
  useEffect(() => () => savingRequest.current?.abort(), [company]);
  const [data, setData] = useState<Page | null>(null); const [page, setPage] = useState(1); const [revision, setRevision] = useState(0); const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  useEffect(() => {
    const controller = new AbortController(); setData(null); setError('');
    fetch(`/api/companies/${company}/alert-history/?page=${page}`, { signal: controller.signal }).then(async response => { if (!response.ok) throw new Error('No se pudo consultar el historial.'); const result = await response.json(); if (!controller.signal.aborted) setData(result); }).catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [company, page, revision]);
  async function save() {
    const controller = new AbortController(); savingRequest.current = controller;
    setBusy(true); setError('');
    try {
      const tokenResponse = await fetch('/api/auth/csrf/', { signal: controller.signal });
      if (!tokenResponse.ok) throw new Error('No se pudo preparar la sesión. Reintenta la conexión.');
      const csrf = await tokenResponse.json();
      const response = await fetch(`/api/companies/${company}/alert-history/`, { signal: controller.signal, method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf.csrfToken }, body: JSON.stringify({ horizon }) });
      const result = await response.json(); if (!response.ok) throw new Error(result.detail || 'No se pudo guardar la evaluación.'); if (!controller.signal.aborted) { setPage(1); setRevision(n => n + 1); }
    } catch (e) { if (!controller.signal.aborted) setError((e as Error).message); } finally { if (!controller.signal.aborted) setBusy(false); }
  }
  return <section className="panel"><h2>Historial de evaluaciones de liquidez</h2><p>Guarda una evaluación del escenario actual. Si sus datos no cambian, se conserva la misma evaluación. No se generan avisos automáticos.</p>{data?.can_save && <button disabled={busy} onClick={save}>Guardar evaluación de {horizon} días</button>}{error && <div role="alert"><p className="error">{error}</p><button disabled={busy} onClick={() => setRevision(n => n + 1)}>Reintentar consulta</button><p>Si el guardado perdió conexión, consulta primero el historial antes de volver a guardar.</p></div>}{!data && !error && <p role="status">Cargando historial…</p>}{data && <>{!data.count ? <p>No hay evaluaciones guardadas.</p> : <div className="table-wrap"><table><thead><tr><th>Guardada</th><th>Corte</th><th>Horizonte</th><th>Saldo / umbral COP</th><th>Resultado</th></tr></thead><tbody>{data.results.map(row => <tr key={row.id}><td>{new Date(row.created_at).toLocaleString('es-CO')}</td><td>{row.evidence.as_of}</td><td>{row.evidence.horizon} días</td><td>{row.evidence.balance} / {row.evidence.threshold}</td><td>{row.result.first_below ? `Bajo umbral desde ${row.result.first_below}; ${row.result.projected_days_below} días futuros` : 'Sin caída bajo umbral'}</td></tr>)}</tbody></table></div>}<button disabled={busy || !data.previous} onClick={() => setPage(n => n - 1)}>Anterior</button> <span>Página {page}</span> <button disabled={busy || !data.next} onClick={() => setPage(n => n + 1)}>Siguiente</button></>}</section>;
}
