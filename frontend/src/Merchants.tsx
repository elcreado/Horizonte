import { useEffect, useRef, useState, type FormEvent } from 'react';
import { MerchantAliases } from './MerchantAliases';

type Merchant = { id: number; display_name: string; movement_count: number };
type Page = { count: number; next: string | null; previous: string | null; results: Merchant[]; can_edit: boolean };

export function Merchants({ company }: { company: string }) {
  const [page, setPage] = useState(1);
  const [revision, setRevision] = useState(0);
  const [data, setData] = useState<Page | null>(null);
  const [error, setError] = useState('');
  const [editing, setEditing] = useState<number | null>(null);
  const [aliasTarget, setAliasTarget] = useState<Merchant | null>(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const saving = useRef<AbortController | null>(null);
  useEffect(() => () => saving.current?.abort(), [company]);
  async function assignAlias(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!aliasTarget || busy) return;
    const form = new FormData(event.currentTarget);
    const name = String(form.get('name') || '').trim();
    if (!name) return;
    const controller = new AbortController(); saving.current = controller;
    setBusy(true); setError(''); setNotice('');
    try {
      const csrfResponse = await fetch('/api/auth/csrf/', { signal: controller.signal });
      if (!csrfResponse.ok) throw new Error('No se pudo preparar la sesión.');
      const csrf = await csrfResponse.json();
      const response = await fetch(`/api/companies/${company}/merchant-aliases/`, {
        method: 'POST', signal: controller.signal,
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf.csrfToken },
        body: JSON.stringify({ merchant_id: aliasTarget.id, provider: form.get('provider'), name }),
      });
      if (!response.ok) throw new Error(response.status === 403 ? 'Tu sesión o rol no permite asignar alias.' : 'No se pudo asignar la etiqueta. Comprueba la fuente y el comercio.');
      if (!controller.signal.aborted) { setAliasTarget(null); setNotice('Etiqueta asignada para futuras importaciones. Los movimientos anteriores se conservan.'); setRevision(value => value + 1); }
    } catch (error) {
      if (!controller.signal.aborted) setError(error instanceof Error ? error.message : 'No se pudo asignar.');
    } finally { if (!controller.signal.aborted) setBusy(false); }
  }
  async function save(event: FormEvent<HTMLFormElement>, row: Merchant) {
    event.preventDefault();
    const name = String(new FormData(event.currentTarget).get('display_name') || '').trim();
    if (!name || busy) return;
    const controller = new AbortController(); saving.current = controller;
    setBusy(true); setError(''); setNotice('');
    try {
      const csrfResponse = await fetch('/api/auth/csrf/', { signal: controller.signal });
      if (!csrfResponse.ok) throw new Error('No se pudo preparar la sesión.');
      const csrf = await csrfResponse.json();
      const response = await fetch(`/api/companies/${company}/merchants/${row.id}/name/`, {
        method: 'PATCH', signal: controller.signal,
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf.csrfToken },
        body: JSON.stringify({ display_name: name }),
      });
      if (!response.ok) throw new Error(response.status === 403 ? 'Tu sesión o rol no permite editar este comercio.' : 'No se pudo guardar el nombre del comercio.');
      if (!controller.signal.aborted) { setEditing(null); setNotice('Nombre guardado.'); setRevision(value => value + 1); }
    } catch (error) {
      if (!controller.signal.aborted) setError(error instanceof Error ? error.message : 'No se pudo guardar.');
    } finally { if (!controller.signal.aborted) setBusy(false); }
  }
  useEffect(() => {
    const controller = new AbortController(); setData(null); setError(''); setAliasTarget(null);
    fetch(`/api/companies/${company}/merchants/?page=${page}`, { signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error('No se pudieron consultar los comercios.');
      const result = await response.json();
      if (!controller.signal.aborted) setData(result);
    }).catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [company, page, revision]);
  return <section className="panel"><div className="toolbar"><h2>Comercios identificados</h2><button disabled={busy} className="secondary" onClick={() => { setEditing(null); setRevision(value => value + 1); }}>Actualizar</button></div><p>Solo aparecen comercios indicados expresamente por la fuente; un nombre ambiguo no se asigna automáticamente. Corregir el nombre visible conserva los alias y movimientos originales.</p>
    {error && <p className="error" role="alert">{error}</p>}
    {notice && <p role="status">{notice}</p>}
    {data?.can_edit && <><label>Asignar una etiqueta a un comercio<select disabled={busy} value={aliasTarget?.id ?? ''} onChange={event => setAliasTarget(data.results.find(row => row.id === Number(event.target.value)) ?? null)}><option value="">Selecciona un comercio de esta página</option>{data.results.map(row => <option key={row.id} value={row.id}>{row.display_name}</option>)}</select></label>{aliasTarget && <form onSubmit={event => void assignAlias(event)}><p>Las próximas importaciones de esta fuente usarán «{aliasTarget.display_name}» para la etiqueta indicada. Si ya estaba asignada a otro comercio, se reemplazará esa asignación. Los movimientos anteriores no cambian.</p><label>Fuente<select name="provider" disabled={busy}><option value="manual_upload">Archivo CSV/XLSX</option><option value="mock">Mock Bank</option></select></label><label>Etiqueta de comercio de la fuente<input name="name" maxLength={250} required disabled={busy} /></label><button disabled={busy}>Asignar etiqueta</button> <button type="button" className="secondary" disabled={busy} onClick={() => setAliasTarget(null)}>Cancelar</button></form>}</>}
    {!data && !error && <p role="status">Cargando comercios…</p>}
    {data && <>{!data.count ? <p>No hay comercios identificados todavía.</p> : <div className="table-wrap"><table><thead><tr><th>Comercio</th><th>Movimientos</th></tr></thead><tbody>{data.results.map(row => <tr key={row.id}><td>{editing === row.id ? <form onSubmit={event => void save(event, row)}><label>Nombre visible<input name="display_name" defaultValue={row.display_name} maxLength={250} required disabled={busy} autoFocus /></label><button disabled={busy}>Guardar</button> <button type="button" className="secondary" disabled={busy} onClick={() => setEditing(null)}>Cancelar</button></form> : <>{row.display_name} {data.can_edit && <button className="secondary" disabled={busy} onClick={() => { setEditing(row.id); setError(''); setNotice(''); }}>Editar nombre</button>}</>}</td><td>{row.movement_count}</td></tr>)}</tbody></table></div>}<button disabled={busy || !data.previous} onClick={() => { setEditing(null); setPage(value => value - 1); }}>Anterior</button> <span>Página {page}</span> <button disabled={busy || !data.next} onClick={() => { setEditing(null); setPage(value => value + 1); }}>Siguiente</button></>}
    <MerchantAliases key={company} company={company} revision={revision} />
  </section>;
}
