import { FormEvent, useEffect, useRef, useState } from 'react';
import { getCsrf } from './csrf';

type Schedule = { id: number; description: string; amount: string; direction: string; day: number; start_date: string; end_date: string | null; active: boolean };
type Page = { can_edit: boolean; results: Schedule[] };
const today = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Bogota' }).format(new Date());

export function MonthlySchedules({ company, revision, onChanged }: { company: string; revision: number; onChanged: () => void }) {
  const [data, setData] = useState<Page | null>(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [reload, setReload] = useState(0);
  const attempt = useRef<string | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    fetch(`/api/companies/${company}/monthly-schedules/`, { signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error('No se pudieron consultar las programaciones.');
      const result = await response.json(); if (!controller.signal.aborted) { setData(result); setError(''); }
    }).catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [company, revision, reload]);
  async function post(path: string, body: object) {
    const csrf = await getCsrf();
    const response = await fetch(`/api/companies/${company}/monthly-schedules/${path}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf.csrfToken }, body: JSON.stringify(body),
    });
    const result = await response.json();
    if (!response.ok) { if (response.status < 500) attempt.current = null; throw new Error(typeof result.detail === 'string' ? result.detail : Object.values(result).flat().join(' ')); }
  }
  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (busy) return;
    const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form));
    attempt.current ||= crypto.randomUUID();
    setBusy(true); setError(''); setNotice('');
    try {
      await post('', { ...values, end_date: values.end_date || null, request_id: attempt.current });
      attempt.current = null; form.reset(); setNotice('Programación creada. Cada mes tendrá su propio compromiso en el calendario y la gráfica.'); setReload(n => n + 1); onChanged();
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  async function cancel(row: Schedule) {
    setBusy(true); setError(''); setNotice('');
    try { await post(`${row.id}/cancel/`, {}); setNotice('Programación detenida; se cancelaron vencimientos futuros sin pagos registrados.'); setReload(n => n + 1); onChanged(); }
    catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  return <section className="panel"><h2>Pagos y cobros mensuales</h2>
    <p>Programa, por ejemplo, el sueldo de tus trabajadores el día 1 de todos los meses. Se crean compromisos pendientes; no se ejecutan pagos bancarios. Si un mes no tiene el día elegido, se usa su último día.</p>
    {error && <p className="error" role="alert">{error} <button className="secondary" onClick={() => setReload(n => n + 1)}>Reintentar consulta</button></p>}{notice && <p role="status">{notice}</p>}
    {!data && !error && <p role="status">Cargando programaciones…</p>}
    {data?.can_edit && <form onSubmit={create}><fieldset className="manual-movement-fields" disabled={busy}>
      <label>Concepto mensual<input name="description" required maxLength={200} placeholder="Sueldos de trabajadores" /></label>
      <label>Tipo de compromiso<select name="direction" defaultValue="out"><option value="out">Pago mensual</option><option value="in">Cobro mensual</option></select></label>
      <label>Valor mensual COP<input name="amount" type="number" min="0.01" step="0.01" required /></label>
      <label>Día de cada mes<input name="day" type="number" min="1" max="31" defaultValue="1" required /></label>
      <label>A partir de<input name="start_date" type="date" defaultValue={today()} required /></label>
      <label>Fecha final (opcional)<input name="end_date" type="date" /></label>
    </fieldset><button disabled={busy}>{busy ? 'Guardando…' : 'Programar todos los meses'}</button></form>}
    {data && <div className="table-wrap"><table><thead><tr><th>Concepto</th><th>Frecuencia</th><th>Valor COP</th><th>Estado</th>{data.can_edit && <th>Acción</th>}</tr></thead><tbody>{data.results.map(row => <tr key={row.id}><td>{row.description}<small>{row.direction === 'out' ? 'Pago' : 'Cobro'} · desde {row.start_date}{row.end_date && ` hasta ${row.end_date}`}</small></td><td>Día {row.day} de cada mes</td><td>{new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(Number(row.amount))}</td><td>{row.active ? 'Activa' : 'Detenida'}</td>{data.can_edit && <td>{row.active && <button className="secondary" disabled={busy} onClick={() => void cancel(row)}>Detener programación</button>}</td>}</tr>)}</tbody></table>{!data.results.length && <p>No hay pagos ni cobros mensuales programados.</p>}</div>}
  </section>;
}
