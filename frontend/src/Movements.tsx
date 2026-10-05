import { FormEvent, useEffect, useState } from 'react';
import { CategorySuggestion } from './CategorySuggestion';

type Movement = { id: number; date: string; description: string; normalized_description: string; merchant_name: string; merchant_id: number | null; merchant_display_name: string | null; amount: string; category: string; source: string; categories: string[] };
type Page = { count: number; next: string | null; previous: string | null; results: Movement[]; can_edit: boolean };
const sources: Record<string, string> = { manual: 'Corregida manualmente', rule: 'Regla automática', company_rule: 'Regla de tu empresa', unclassified: 'Sin regla aplicada', existing: 'Categoría previa' };

export function Movements({ company }: { company: string }) {
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Page | null>(null);
  const [error, setError] = useState('');
  const [reload, setReload] = useState(0);
  const [editing, setEditing] = useState<Movement | null>(null);
  const [category, setCategory] = useState('');
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    setData(null); setError(''); setEditing(null);
    fetch(`/api/companies/${company}/movements/?page=${page}`, { signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error('No se pudieron consultar los movimientos.');
      setData(await response.json());
    }).catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [company, page, reload]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!editing) return;
    const form = new FormData(event.currentTarget); setSaving(true); setError(''); setNotice('');
    try {
      const csrf = await (await fetch('/api/auth/csrf/')).json();
      const response = await fetch(`/api/companies/${company}/movements/${editing.id}/category/`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf.csrfToken },
        body: JSON.stringify({ category: form.get('category'), remember: form.get('remember') === 'on' }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'No se pudo guardar la categoría.');
      setEditing(null); setReload(value => value + 1); setNotice('Categoría guardada.');
    } catch (e) { setError((e as Error).message); }
    finally { setSaving(false); }
  }
  return <section className="panel"><div className="toolbar"><h2>Movimientos y categorías</h2><button className="secondary" disabled={saving} onClick={() => setReload(n => n + 1)}>Actualizar movimientos</button></div>
    <p>Las reglas se aplican a nuevas importaciones. Puedes corregir una categoría sin cambiar el monto ni el saldo.</p>
    {error && <p className="error" role="alert">{error}</p>}{notice && <p role="status">{notice}</p>}
    {!data && !error && <p role="status">Cargando movimientos…</p>}
    {editing && <form className="panel" onSubmit={save}><h3>Clasificar: {editing.description}</h3><label>Categoría<select name="category" value={category} onChange={event => setCategory(event.target.value)}>{editing.categories.map(c => <option key={c}>{c}</option>)}</select></label>
      <CategorySuggestion key={`${company}-${editing.id}`} company={company} movement={editing.id} disabled={saving} onChoose={value => { if (editing.categories.includes(value)) setCategory(value); }} />
      <label style={{ display: 'block', margin: '16px 0' }}><input type="checkbox" name="remember" /> Recordar para futuras importaciones con la misma descripción y sentido (ingreso o egreso), solo en esta empresa.</label>
      <button disabled={saving}>{saving ? 'Guardando…' : 'Guardar categoría'}</button> <button className="secondary" type="button" disabled={saving} onClick={() => setEditing(null)}>Cancelar</button></form>}
    {data && <><div className="table-wrap"><table><thead><tr><th>Movimiento</th><th>Fecha</th><th>Categoría</th><th>Valor COP</th>{data.can_edit && <th>Acción</th>}</tr></thead><tbody>{data.results.map(m => <tr key={m.id}><td>{m.description}{m.merchant_name && <small>Comercio: {m.merchant_display_name || m.merchant_name}</small>}<details><summary>Descripción normalizada</summary>{m.normalized_description || 'Pendiente de normalizar'}</details></td><td>{m.date}</td><td>{m.category}<small>{sources[m.source] || m.source}</small></td><td>{new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(Number(m.amount))}</td>{data.can_edit && <td><button className="secondary" disabled={saving} onClick={() => { setEditing(m); setCategory(m.category); setNotice(''); }}>Clasificar</button></td>}</tr>)}</tbody></table></div>
      {!data.count && <p>No hay movimientos registrados.</p>}
      <div className="toolbar"><button className="secondary" disabled={!data.previous || saving} onClick={() => setPage(n => n - 1)}>Anterior</button><span>Página {page} · {data.count} movimientos</span><button className="secondary" disabled={!data.next || saving} onClick={() => setPage(n => n + 1)}>Siguiente</button></div></>}
  </section>;
}
