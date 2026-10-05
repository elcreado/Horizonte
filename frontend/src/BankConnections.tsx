import { getCsrf } from './csrf';
import { useEffect, useRef, useState } from 'react';

type Connection = { id: number; provider: string; status: string; account_id: number; consent: { scopes: string[]; granted_at: string; revoked_at: string | null } };
type Job = { id: number; connection_id: number; status: string; created_count: number; duplicate_count: number; error: string };
type Data = { can_manage: boolean; connections: Connection[]; jobs: Job[] };

export function BankConnections({ company, onChanged }: { company: string; onChanged: () => void }) {
  const [data, setData] = useState<Data | null>(null);
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const lastCompleted = useRef<string | null>(null);
  useEffect(() => {
    let alive = true;
    async function load() {
      try {
        const response = await fetch(`/api/companies/${company}/bank-connections/`);
        if (!response.ok) throw new Error('No se pudieron consultar las conexiones.');
        const next: Data = await response.json();
        if (!alive) return;
        setData(next);
        const completed = next.jobs.filter(job => job.status === 'completed').map(job => job.id).join(',');
        if (lastCompleted.current !== null && completed !== lastCompleted.current) onChanged();
        lastCompleted.current = completed;
      } catch (e) { if (alive) setError((e as Error).message); }
    }
    void load();
    const timer = window.setInterval(() => { void load(); }, 3000);
    return () => { alive = false; window.clearInterval(timer); };
  }, [company, onChanged]);
  async function action(path: string, body?: object) {
    setBusy(true); setError('');
    try {
      const csrf = await getCsrf();
      const response = await fetch(`/api/companies/${company}/bank-connections/${path}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf.csrfToken }, body: JSON.stringify(body || {}),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'No se pudo completar la operación.');
      const refresh = await fetch(`/api/companies/${company}/bank-connections/`);
      if (refresh.ok) setData(await refresh.json());
      onChanged();
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  const active = data?.connections.find(row => row.status === 'active');
  return <section className="panel"><h2>Fuente bancaria de prueba</h2><p>Mock Bank crea una cuenta y 120 días de movimientos sintéticos. No se conecta a un banco real ni solicita credenciales. El acceso es de solo lectura.</p>
    {data?.can_manage && !active && <><label><input type="checkbox" checked={consent} onChange={event => setConsent(event.target.checked)} /> Autorizo la lectura local de saldos y movimientos sintéticos para esta empresa.</label> <button disabled={busy || !consent} onClick={() => action('', { provider: 'mock', consent: true })}>{data.connections.length ? 'Volver a conectar Mock Bank' : 'Conectar Mock Bank'}</button></>}
    {active && <p>Conexión activa · cuenta #{active.account_id}. {data?.can_manage && <><button disabled={busy} onClick={() => action(`${active.id}/sync/`)}>Sincronizar</button> <button className="secondary" disabled={busy} onClick={() => action(`${active.id}/revoke/`)}>Revocar acceso</button></>}</p>}
    {data?.connections.some(row => row.status === 'revoked') && <p>La conexión revocada conserva sus datos históricos y no puede sincronizarse hasta que autorices volver a conectarla.</p>}
    {error && <p className="error" role="alert">{error}</p>}
    {!data && !error && <p role="status">Cargando conexiones…</p>}
    {data && data.jobs.length > 0 && <div className="table-wrap"><table><thead><tr><th>Sincronización</th><th>Estado</th><th>Nuevos</th><th>Duplicados</th><th>Detalle</th></tr></thead><tbody>{data.jobs.map(job => <tr key={job.id}><td>#{job.id}</td><td>{job.status === 'completed' ? 'Completada' : job.status === 'failed' ? 'Fallida' : 'En cola'}</td><td>{job.created_count}</td><td>{job.duplicate_count}</td><td>{job.error}</td></tr>)}</tbody></table></div>}
  </section>;
}
