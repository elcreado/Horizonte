import { getCsrf } from './csrf';
import { useEffect, useState } from 'react';
type Rule = { id: number; normalized_description: string; direction: string; category: string };
type Page = { results: Rule[]; count: number; next: string | null; previous: string | null; can_edit: boolean };
export function ClassificationRules({ company }: { company: string }) {
  const [data, setData] = useState<Page | null>(null);
  const [page, setPage] = useState(1);
  const [revision, setRevision] = useState(0);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  useEffect(() => {
    const controller = new AbortController(); setData(null); setError('');
    fetch(`/api/companies/${company}/classification-rules/?page=${page}`, { signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error('No se pudieron consultar las reglas.');
      setData(await response.json());
    }).catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [company, page, revision]);
  async function remove(rule: Rule) {
    setSaving(true); setError('');
    try {
      const csrf = await getCsrf();
      const response = await fetch(`/api/companies/${company}/classification-rules/${rule.id}/`, { method: 'DELETE', headers: { 'X-CSRFToken': csrf.csrfToken } });
      if (!response.ok) throw new Error('No se pudo eliminar la regla. Actualiza la lista.');
      setPage(1); setRevision(n => n + 1);
    } catch (e) { setError((e as Error).message); }
    finally { setSaving(false); }
  }
  return <section className="panel"><div className="toolbar"><h2>Reglas de clasificación guardadas</h2><button className="secondary" disabled={saving} onClick={() => { setPage(1); setRevision(n => n + 1); }}>Actualizar reglas</button></div><p>Eliminar una regla afecta a futuras importaciones. Las categorías de movimientos anteriores se conservan. Puedes guardar una nueva regla al corregir un movimiento.</p>
    {error && <p className="error" role="alert">{error}</p>}{!data && !error && <p role="status">Cargando reglas…</p>}
    {data && <>{!data.count ? <p>No hay reglas guardadas.</p> : <div className="table-wrap"><table><thead><tr><th>Descripción</th><th>Sentido</th><th>Categoría</th>{data.can_edit && <th>Acción</th>}</tr></thead><tbody>{data.results.map(rule => <tr key={rule.id}><td>{rule.normalized_description}</td><td>{rule.direction === 'in' ? 'Ingreso' : 'Egreso'}</td><td>{rule.category}</td>{data.can_edit && <td><button className="secondary" disabled={saving} onClick={() => remove(rule)}>Eliminar regla</button></td>}</tr>)}</tbody></table></div>}<div className="toolbar"><button disabled={saving || !data.previous} onClick={() => setPage(n => n - 1)}>Anterior</button><span>Página {page} · {data.count} reglas</span><button disabled={saving || !data.next} onClick={() => setPage(n => n + 1)}>Siguiente</button></div></>}
  </section>;
}
