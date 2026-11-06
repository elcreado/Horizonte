import { useEffect, useState } from 'react';

type Day = { date: string; receivable: string; payable: string; receivable_count: number; payable_count: number };
type Calendar = { month: string; currency: string; days: Day[]; notice: string };
const money = (amount: string) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(Number(amount));
const currentMonth = () => { const date = new Date(); return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`; };

export function ObligationCalendar({ company, refresh }: { company: string; refresh: number }) {
  const [month, setMonth] = useState(currentMonth);
  const [data, setData] = useState<Calendar | null>(null);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController(); setData(null); setError('');
    fetch(`/api/companies/${company}/obligation-calendar/?month=${encodeURIComponent(month)}`, { signal: controller.signal }).then(async response => {
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'No se pudo consultar el calendario.');
      if (!controller.signal.aborted) setData(result);
    }).catch(error => { if (!controller.signal.aborted) setError(error.message); });
    return () => controller.abort();
  }, [company, month, refresh, revision]);
  const cells: (Day | null)[] = [];
  if (data) {
    const first = new Date(`${data.days[0].date}T12:00:00Z`).getUTCDay();
    cells.push(...Array<null>((first + 6) % 7).fill(null), ...data.days);
    while (cells.length % 7) cells.push(null);
  }
  return <section className="panel"><div className="toolbar"><h2>Calendario de obligaciones</h2><label>Mes<input type="month" value={month} min="0001-01" max="9999-12" onChange={event => { if (event.target.value) setMonth(event.target.value); }} /></label></div>
    {error && <div role="alert"><p className="error">{error}</p><button onClick={() => setRevision(n => n + 1)}>Reintentar calendario</button></div>}
    {!data && !error && <p role="status">Cargando calendario…</p>}
    {data && <><p>{data.notice}</p><div className="table-wrap"><table className="obligation-calendar"><caption>Vencimientos pendientes · {data.month} · COP</caption><thead><tr>{['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'].map(day => <th scope="col" key={day}>{day}</th>)}</tr></thead><tbody>{Array.from({ length: cells.length / 7 }, (_, week) => <tr key={week}>{cells.slice(week * 7, week * 7 + 7).map((day, offset) => <td key={day?.date || `empty-${offset}`}>{day && <><time dateTime={day.date}>{Number(day.date.slice(-2))}</time>{day.receivable_count > 0 && <p>Por cobrar: {money(day.receivable)}<small>{day.receivable_count} obligaciones</small></p>}{day.payable_count > 0 && <p>Por pagar: {money(day.payable)}<small>{day.payable_count} obligaciones</small></p>}{!day.receivable_count && !day.payable_count && <small>Sin vencimientos pendientes</small>}</>}</td>)}</tr>)}</tbody></table></div></>}
  </section>;
}
