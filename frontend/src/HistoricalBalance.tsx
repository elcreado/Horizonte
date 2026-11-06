import { useState } from 'react';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { BalanceHistoryData, BalanceWindow, balanceChartPoints, exactCop, selectBalancePoints } from './balanceHistory';

const labels = { declared: 'Saldo declarado al corte', reconstructed: 'Reconstruido con cobertura', unknown: 'Sin cobertura' };

export function HistoricalBalance({ data, onRefresh }: { data: BalanceHistoryData; onRefresh: () => void }) {
  const [window, setWindow] = useState<BalanceWindow>('30');
  const visible = selectBalancePoints(data.points, window);
  return <section className="panel">
    <div className="toolbar"><h2>Saldo histórico al cierre del día</h2><button className="secondary" onClick={onRefresh}>Actualizar saldos históricos</button></div>
    <p>Saldo declarado al {data.cutoff}: <strong>{exactCop(data.declared_balance)}</strong>. {data.complete_from ? `Historial consolidado con cobertura desde ${data.complete_from}.` : 'Falta cobertura común para reconstruir los días anteriores al corte.'}</p>
    <p>{data.notice}</p>
    {!data.complete_from && <p className="notice">Por ahora solo se muestra el saldo declarado al corte. Revisa cada cuenta en <a href="#/dashboard/accounts">Cuentas y saldos</a> y confirma el periodo únicamente si registraste toda su actividad.</p>}
    <label>Rango del histórico<select value={window} onChange={event => setWindow(event.target.value as BalanceWindow)}><option value="30">Últimos 30 días del corte</option><option value="90">Últimos 90 días del corte</option><option value="all">Doce meses hasta el corte</option></select></label>
    <div style={{ height: 300 }} aria-label="Saldo histórico diario en COP; los huecos no son cero. Consulta las cifras exactas y su origen en la tabla siguiente.">
      <ResponsiveContainer width="100%" height="100%"><LineChart data={balanceChartPoints(visible)}>
        <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" minTickGap={45} /><YAxis />
        <Tooltip formatter={value => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(Number(value))} />
        <Line dataKey="balance" name="Saldo al cierre COP" stroke="#187a69" connectNulls={false} dot={{ r: 2 }} isAnimationActive={false} />
      </LineChart></ResponsiveContainer>
    </div>
    <details><summary>Ver saldos diarios y su origen</summary><div className="table-wrap"><table>
      <caption>Saldos COP al cierre · {visible[0]?.date} a {data.cutoff}. Los días sin cobertura no tienen un saldo reconstruido.</caption>
      <thead><tr><th scope="col">Fecha</th><th scope="col">Saldo COP</th><th scope="col">Origen</th></tr></thead>
      <tbody>{visible.map(point => <tr key={point.date}><td>{point.date}</td><td>{exactCop(point.balance)}</td><td>{labels[point.status]}</td></tr>)}</tbody>
    </table></div></details>
    <details><summary>Ver saldos y cobertura por cuenta</summary><div className="table-wrap"><table>
      <caption>Fuentes del saldo consolidado; la cobertura no es una certificación bancaria.</caption>
      <thead><tr><th scope="col">Cuenta</th><th scope="col">Saldo declarado COP</th><th scope="col">Corte</th><th scope="col">Cobertura</th><th scope="col">Procedencia</th></tr></thead>
      <tbody>{data.accounts.map(account => <tr key={account.account_id}><td>{account.name}</td><td>{exactCop(account.declared_balance)}</td><td>{account.balance_date}</td><td>{account.coverage_valid ? `${account.complete_from} a ${account.complete_through}` : 'Sin cobertura válida al corte'}</td><td>{account.coverage_source === 'source' ? 'Fuente conectada' : 'Confirmación manual'}</td></tr>)}</tbody>
    </table></div></details>
  </section>;
}
