import { getCsrf } from './csrf';
import { useEffect, useState } from 'react';

type Occurrence = { link_id: number | null; date: string; obligation_id: number | null; cancelled: boolean; matching_obligations: { id: number; reference: string; description: string; outstanding_amount: string }[] };
type Candidate = { occurrences: Occurrence[]; fingerprint: string; status: string; account_id: number; description: string; direction: string; cadence: string; amount: string; next_date: string; observations: number };
type Result = { can_edit: boolean; as_of: string; notice: string; results: Candidate[] };

export function Recurrences({ company, horizon, onChanged }: { company: string; horizon: number; onChanged: () => void }) {
  const [data, setData] = useState<Result | null>(null);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setData(null); setError('');
    fetch(`/api/companies/${company}/recurrences/?horizon=${horizon}`, { signal: controller.signal }).then(async response => {
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'No se pudieron detectar las recurrencias.');
      setData(result);
    }).catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [company, horizon, revision]);
  async function review(item: Candidate, status: string, obligationId?: number, occurrenceDate?: string) {
    setSaving(true); setError('');
    try {
      const csrf = await getCsrf();
      const response = await fetch(`/api/companies/${company}/recurrences/?horizon=${horizon}`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf.csrfToken },
        body: JSON.stringify({ fingerprint: item.fingerprint, status, obligation_id: obligationId, occurrence_date: occurrenceDate }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'No se pudo guardar la revisión.');
      setRevision(n => n + 1);
      if (status === 'create' || status === 'link') onChanged();
    } catch (e) { setError((e as Error).message); }
    finally { setSaving(false); }
  }
  async function unlink(occurrence: Occurrence) {
    if (!occurrence.link_id) return;
    setSaving(true); setError('');
    try {
      const csrf = await getCsrf();
      const response = await fetch(`/api/companies/${company}/recurrence-occurrences/${occurrence.link_id}/unlink/`, {
        method: 'POST', headers: { 'X-CSRFToken': csrf.csrfToken },
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'No se pudo desvincular.');
      setRevision(n => n + 1);
    } catch (e) { setError((e as Error).message); }
    finally { setSaving(false); }
  }
  return <section className="panel"><div className="toolbar"><h2>Recurrencias sugeridas</h2><button className="secondary" onClick={() => setRevision(n => n + 1)}>Actualizar patrones</button></div>
    <p>Se buscan al menos tres movimientos semanales o mensuales con descripción coincidente y montos similares, separados por cuenta y sentido. Si cambia la evidencia, el patrón requiere una nueva revisión.</p>
    {error && <p className="error" role="alert">{error}</p>}
    {!data && !error && <p role="status">Analizando historial…</p>}
    {data && <><p>{data.notice}</p><p>Corte: {data.as_of}</p>
      {!data.results.length ? <p>No hay patrones suficientes y vigentes en el historial disponible.</p> : <div className="table-wrap"><table><thead><tr><th>Descripción</th><th>Frecuencia</th><th>Monto estimado COP</th><th>Próxima fecha estimada</th><th>Evidencia</th><th>Revisión</th></tr></thead><tbody>{data.results.map(item => <tr key={`${item.account_id}-${item.direction}-${item.description}`}><td>{item.description}<small>Cuenta {item.account_id} · {item.direction === 'in' ? 'Cobro' : 'Pago'}</small></td><td>{item.cadence === 'monthly' ? 'Mensual' : 'Semanal'}</td><td>{new Intl.NumberFormat('es-CO').format(Number(item.amount))}</td><td>{item.next_date}</td><td>{item.observations} movimientos</td><td><span>{item.status === 'confirmed' ? 'Confirmada' : item.status === 'rejected' ? 'Rechazada' : 'Pendiente'}</span>{data.can_edit && <div><button disabled={saving || item.status === 'confirmed'} onClick={() => review(item, 'confirmed')}>Confirmar patrón</button> <button className="secondary" disabled={saving || item.status === 'rejected'} onClick={() => review(item, 'rejected')}>Rechazar</button> <button className="secondary" disabled={saving || item.status === 'pending'} onClick={() => review(item, 'pending')}>Reabrir</button></div>}<details><summary>Fechas previstas en {horizon} días ({item.occurrences.length})</summary>{item.occurrences.map(occurrence => <div key={occurrence.date} className="panel"><strong>{occurrence.date}</strong>{occurrence.obligation_id ? <p>Obligación #{occurrence.obligation_id}{occurrence.cancelled ? ' · Cancelada' : ''}. Gestionar en Obligaciones.{data.can_edit && <><br /><button className="secondary" disabled={saving} onClick={() => unlink(occurrence)}>Desvincular conservando la obligación</button></>}</p> : data.can_edit && item.status === 'confirmed' ? <div>{occurrence.matching_obligations.map(obligation => <button className="secondary" disabled={saving} key={obligation.id} onClick={() => review(item, 'link', obligation.id, occurrence.date)}>Vincular {obligation.reference}: {obligation.description} · {obligation.outstanding_amount} COP pendientes</button>)}<button disabled={saving || occurrence.matching_obligations.length > 0} onClick={() => review(item, 'create', undefined, occurrence.date)}>Crear obligación por {item.amount} COP</button></div> : <p>Sin obligación vinculada.</p>}</div>)}</details></td></tr>)}</tbody></table></div>}</>}
  </section>;
}
