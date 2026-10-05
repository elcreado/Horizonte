import { useEffect, useState } from 'react';

type Alias = { id: number; provider: string; normalized_name: string; merchant_display_name: string };
type AliasPage = { count: number; next: string | null; previous: string | null; results: Alias[] };

export function MerchantAliases({ company, revision }: { company: string; revision: number }) {
  const [page, setPage] = useState(1);
  const [retry, setRetry] = useState(0);
  const [data, setData] = useState<AliasPage | null>(null);
  const [error, setError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    setData(null); setError('');
    async function load() {
      try {
        const response = await fetch(`/api/companies/${company}/merchant-aliases/?page=${page}`, { signal: controller.signal });
        if (!response.ok) throw new Error('No se pudieron consultar las etiquetas de comercios.');
        const result: AliasPage = await response.json();
        if (!controller.signal.aborted) setData(result);
      } catch (error) {
        if (!controller.signal.aborted) setError(error instanceof Error ? error.message : 'No se pudieron consultar las etiquetas.');
      }
    }
    void load();
    return () => controller.abort();
  }, [company, page, revision, retry]);
  return <section aria-label="Etiquetas de comercios"><h3>Etiquetas por fuente</h3>
    <p>Estas asignaciones se usan en futuras importaciones. Incluyen las etiquetas detectadas automáticamente y las asignadas manualmente.</p>
    {error && <p className="error" role="alert">{error} <button onClick={() => setRetry(value => value + 1)}>Reintentar</button></p>}
    {!data && !error && <p role="status">Cargando etiquetas…</p>}
    {data && <>{data.count === 0 ? <p>No hay etiquetas registradas.</p> : <div className="table-wrap"><table><thead><tr><th>Fuente</th><th>Etiqueta normalizada</th><th>Comercio asignado</th></tr></thead><tbody>{data.results.map(row => <tr key={row.id}><td>{row.provider === 'manual_upload' ? 'CSV/XLSX' : row.provider === 'mock' ? 'Mock Bank' : row.provider}</td><td>{row.normalized_name}</td><td>{row.merchant_display_name}</td></tr>)}</tbody></table></div>}
      <button disabled={!data.previous} onClick={() => setPage(value => value - 1)}>Etiquetas anteriores</button> <span>Página {page}</span> <button disabled={!data.next} onClick={() => setPage(value => value + 1)}>Etiquetas siguientes</button>
    </>}
  </section>;
}
