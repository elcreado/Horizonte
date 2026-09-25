import { FormEvent, useEffect, useRef, useState } from 'react';

type Obligation = { id: number; reference: string; description: string; counterparty: string; direction: string; due_date: string; outstanding_amount: string; cancelled: boolean; status: string };
type Page<T> = { count: number; results: T[]; next: string | null; previous: string | null; can_edit: boolean };
type Payment = { id: number; transaction_id: number; amount: string; reversed_at: string | null };
type Movement = { id: number; description: string; date: string; amount: string; available: string };
const money = (value: string) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(Number(value));

async function request<T>(url: string, method = 'GET', body?: object, signal?: AbortSignal): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (method !== 'GET') {
    const response = await fetch('/api/auth/csrf/');
    if (!response.ok) throw new Error('No se pudo verificar la sesión.');
    headers['X-CSRFToken'] = (await response.json()).csrfToken;
  }
  const response = await fetch(url, { method, headers, body: body ? JSON.stringify(body) : undefined, signal });
  const result = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : Array.isArray(result) ? result.join(' ') : Object.values(result).flat().join(' ') || 'No se pudo completar la operación.');
  return result;
}

export function Obligations({ company, onChange, refresh }: { company: string; onChange: () => void; refresh: number }) {
  const [data, setData] = useState<Page<Obligation> | null>(null);
  const [page, setPage] = useState(1);
  const [revision, setRevision] = useState(0);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<Obligation | null>(null);
  const [creating, setCreating] = useState(false);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [candidates, setCandidates] = useState<Page<Movement> | null>(null);
  const [candidatePage, setCandidatePage] = useState(1);
  const [history, setHistory] = useState<{ id: number; action: string; user__username: string; created_at: string }[]>([]);
  const attempt = useRef(crypto.randomUUID());
  const base = `/api/companies/${company}/obligations/`;
  useEffect(() => {
    const controller = new AbortController(); setError('');
    request<Page<Obligation>>(`${base}?page=${page}`, 'GET', undefined, controller.signal).then(setData).catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [base, page, revision, refresh]);
  useEffect(() => {
    if (!selected) return;
    const controller = new AbortController(); setCandidates(null); setPayments([]); setHistory([]);
    Promise.all([
      request<Payment[]>(`${base}${selected.id}/settlements/`, 'GET', undefined, controller.signal),
      request<Page<Movement>>(`${base}${selected.id}/candidates/?page=${candidatePage}`, 'GET', undefined, controller.signal),
      request<Page<{ id: number; action: string; user__username: string; created_at: string }>>(`${base}${selected.id}/history/`, 'GET', undefined, controller.signal),
    ]).then(([p, c, h]) => { setPayments(p); setCandidates(c); setHistory(h.results); }).catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [base, selected, revision, candidatePage]);

  async function mutate(url: string, method: string, body: object, message: string) {
    setBusy(true); setError(''); setNotice('');
    try {
      await request(url, method, body);
      setRevision(n => n + 1); onChange(); setNotice(message); return true;
    } catch (e) { setError((e as Error).message); return false; }
    finally { setBusy(false); }
  }
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const fields = Object.fromEntries(new FormData(event.currentTarget));
    if (await mutate(base, 'POST', fields, 'Obligación registrada.')) setCreating(false);
  }
  async function edit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!selected) return;
    if (await mutate(`${base}${selected.id}/`, 'PATCH', Object.fromEntries(new FormData(event.currentTarget)), 'Obligación actualizada.')) setSelected(null);
  }
  async function reconcile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!selected) return;
    const fields = Object.fromEntries(new FormData(event.currentTarget));
    if (await mutate(`${base}${selected.id}/settlements/`, 'POST', { ...fields, request_id: attempt.current }, 'Conciliación registrada. El saldo bancario se conserva.')) {
      attempt.current = crypto.randomUUID(); setSelected(null);
    }
  }

  return <section className="panel"><div className="toolbar"><div><h2>Cuentas por cobrar y pagar</h2><p>Registra compromisos y vincula cobros o pagos que ya aparecen en tus movimientos.</p></div>{data?.can_edit && <button disabled={busy} onClick={() => { setCreating(!creating); setSelected(null); }}>Nueva obligación</button>}</div>
    {error && <p className="error" role="alert">{error}</p>}{notice && <p role="status">{notice}</p>}
    {creating && <form className="obligation-form" onSubmit={create}>
      <label>Referencia única<input name="reference" required maxLength={120} /></label><label>Descripción<input name="description" required maxLength={200} /></label>
      <label>Cliente o proveedor<input name="counterparty" maxLength={200} /></label><label>Tipo<select name="direction"><option value="in">Por cobrar</option><option value="out">Por pagar</option></select></label>
      <label>Vencimiento<input name="due_date" type="date" required /></label><label>Valor pendiente COP<input name="outstanding_amount" type="number" min="0.01" step="0.01" required /></label>
      <div><button disabled={busy}>Guardar</button> <button type="button" className="secondary" disabled={busy} onClick={() => setCreating(false)}>Cancelar</button></div>
    </form>}
    {!data && !error && <p role="status">Cargando obligaciones…</p>}
    {data && <><div className="table-wrap"><table><thead><tr><th>Concepto</th><th>Tipo</th><th>Vencimiento</th><th>Pendiente</th><th>Estado</th><th>Detalle</th></tr></thead><tbody>{data.results.map(o => <tr key={o.id}>
      <td>{o.description}<small>{o.reference} · {o.counterparty || 'Sin contraparte'}</small></td><td>{o.direction === 'in' ? 'Por cobrar' : 'Por pagar'}</td><td>{o.due_date}</td><td>{money(o.outstanding_amount)}</td><td>{o.cancelled ? 'Cancelada' : o.status === 'settled' ? 'Saldada' : 'Pendiente'}</td>
      <td><button className="secondary" disabled={busy} onClick={() => { setSelected(o); setCreating(false); setCandidatePage(1); attempt.current = crypto.randomUUID(); }}>Ver detalle</button></td>
    </tr>)}</tbody></table></div><div className="toolbar"><button className="secondary" disabled={!data.previous || busy} onClick={() => { setPage(n => n - 1); setSelected(null); }}>Anterior</button><span>Página {page} · {data.count} obligaciones</span><button className="secondary" disabled={!data.next || busy} onClick={() => { setPage(n => n + 1); setSelected(null); }}>Siguiente</button></div></>}
    {selected && <div className="panel" key={selected.id}><div className="toolbar"><h3>{selected.description}</h3><button className="secondary" disabled={busy} onClick={() => setSelected(null)}>Cerrar detalle</button></div>
      {data?.can_edit && <><form className="obligation-form" onSubmit={edit}><label>Descripción<input name="description" defaultValue={selected.description} required maxLength={200} /></label><label>Cliente o proveedor<input name="counterparty" defaultValue={selected.counterparty} maxLength={200} /></label><label>Vencimiento<input name="due_date" type="date" defaultValue={selected.due_date} required /></label><button disabled={busy}>Actualizar datos</button></form>
        <button className="secondary" disabled={busy} onClick={async () => { if (await mutate(`${base}${selected.id}/`, 'PATCH', { cancelled: !selected.cancelled }, selected.cancelled ? 'Obligación reactivada.' : 'Obligación cancelada; excluida de la proyección.')) setSelected(null); }}>{selected.cancelled ? 'Reactivar obligación' : 'Cancelar obligación'}</button>
        {!selected.cancelled && selected.status !== 'settled' && <form onSubmit={reconcile} className="obligation-form"><h3>Conciliar con un movimiento existente</h3><p>No realiza transferencias ni modifica el saldo bancario.</p>
          <label>Movimiento<select name="transaction_id" required onChange={() => { attempt.current = crypto.randomUUID(); }}>{candidates?.results.map(m => <option key={m.id} value={m.id}>{m.date} · {m.description} · disponible {money(m.available)}</option>)}</select></label>
          <label>Importe a conciliar COP<input name="amount" type="number" step="0.01" min="0.01" max={selected.outstanding_amount} required onChange={() => { attempt.current = crypto.randomUUID(); }} /></label>
          <button disabled={busy || !candidates?.results.length}>Registrar conciliación</button>
          <div><button className="secondary" type="button" disabled={busy || !candidates?.previous} onClick={() => setCandidatePage(n => n - 1)}>Movimientos anteriores</button> <button className="secondary" type="button" disabled={busy || !candidates?.next} onClick={() => setCandidatePage(n => n + 1)}>Más movimientos</button></div>
          {candidates?.count === 0 && <p>No hay movimientos disponibles del mismo sentido. Primero importa el cobro o pago desde CSV.</p>}
        </form>}</>}
      <h3>Conciliaciones</h3>{payments.map(p => <p key={p.id}>{money(p.amount)} · movimiento #{p.transaction_id} · {p.reversed_at ? 'Revertida' : 'Aplicada'} {data?.can_edit && !p.reversed_at && <button className="secondary" disabled={busy} onClick={async () => { if (await mutate(`${base}${selected.id}/settlements/${p.id}/reverse/`, 'POST', {}, 'Conciliación deshecha.')) setSelected(null); }}>Deshacer</button>}</p>)}
      {!payments.length && <p>No hay conciliaciones registradas.</p>}
      <h3>Historial reciente</h3>{history.map(h => <p key={h.id}>{new Date(h.created_at).toLocaleString('es-CO')} · {h.user__username} · {{ 'invoice.obligation_linked': 'Factura vinculada', 'obligation.created': 'Creación', 'obligation.updated': 'Actualización', 'obligation.reconciled': 'Conciliación', 'obligation.reconciliation_reversed': 'Reversión' }[h.action] || h.action}</p>)}
    </div>}
  </section>;
}
