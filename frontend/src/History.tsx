import { useEffect, useState } from 'react';
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

type Totals = { income: string; expense: string };
type HistoryData = { start: string; as_of: string; first_transaction: string | null; count: number; notice: string; months: (Totals & { month: string; net: string; count: number })[]; categories: (Totals & { category: string })[] };
const money = (value: string | number) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(Number(value));

export function History({ company, refresh }: { company: string; refresh: number }) {
  const [data, setData] = useState<HistoryData | null>(null);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController(); setData(null); setError('');
    fetch(`/api/companies/${company}/history/`, { signal: controller.signal }).then(async response => {
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'No se pudo cargar el histórico.');
      if (!controller.signal.aborted) setData(result);
    }).catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [company, revision, refresh]);
  return <section className="panel"><div className="toolbar"><h2>Ingresos y egresos registrados</h2><button className="secondary" onClick={() => setRevision(n => n + 1)}>Actualizar histórico</button></div>
    {error && <p className="error" role="alert">{error}</p>}{!data && !error && <p role="status">Cargando histórico…</p>}
    {data && <><p>{data.start} a {data.as_of} · {data.count} movimientos · Primera fecha registrada en el periodo: {data.first_transaction || 'sin datos'}.</p><p>{data.notice}</p>
      {!data.count ? <p>No hay movimientos en los últimos doce meses del corte.</p> : <>
        <div style={{ height: 300 }} aria-label="Ingresos y egresos mensuales; cifras exactas en la tabla siguiente"><ResponsiveContainer width="100%" height="100%"><BarChart data={data.months.map(row => ({ ...row, income: Number(row.income), expense: Number(row.expense) }))}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="month" /><YAxis /><Tooltip formatter={value => money(Number(value))} /><Legend /><Bar dataKey="income" name="Ingresos COP" fill="#187a69" /><Bar dataKey="expense" name="Egresos COP" fill="#b85435" /></BarChart></ResponsiveContainer></div>
        <details><summary>Ver cifras mensuales</summary><div className="table-wrap"><table><thead><tr><th>Mes</th><th>Ingresos COP</th><th>Egresos COP</th><th>Neto COP</th><th>Movimientos</th></tr></thead><tbody>{data.months.map(row => <tr key={row.month}><td>{row.month}</td><td>{money(row.income)}</td><td>{money(row.expense)}</td><td>{money(row.net)}</td><td>{row.count || 'Sin datos'}</td></tr>)}</tbody></table></div></details>
        <h3>Desglose por categorías</h3>
        <div style={{ height: Math.max(240, data.categories.length * 52) }} aria-label="Ingresos y egresos por categoría; cifras en la tabla siguiente"><ResponsiveContainer width="100%" height="100%"><BarChart layout="vertical" data={data.categories.map(row => ({ ...row, income: Number(row.income), expense: Number(row.expense) }))} margin={{ left: 20 }}><CartesianGrid strokeDasharray="3 3" /><XAxis type="number" /><YAxis type="category" dataKey="category" width={135} interval={0} /><Tooltip formatter={value => money(Number(value))} /><Legend /><Bar dataKey="income" name="Ingresos COP" fill="#187a69" /><Bar dataKey="expense" name="Egresos COP" fill="#b85435" /></BarChart></ResponsiveContainer></div>
        <div className="table-wrap"><table><thead><tr><th>Categoría</th><th>Ingresos COP</th><th>Egresos COP</th></tr></thead><tbody>{data.categories.map(row => <tr key={row.category}><td>{row.category}</td><td>{money(row.income)}</td><td>{money(row.expense)}</td></tr>)}</tbody></table></div>
      </>}
    </>}
  </section>;
}
