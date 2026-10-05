import { Area, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

type Point = { date: string; balance: string; p10?: string; p50?: string; p90?: string };
const money = (value: number) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(value);

export function ForecastChart({ points, quantiles }: { points: Point[]; quantiles: boolean }) {
  const complete = quantiles && points.length > 0 && points.every(point =>
    point.p10 !== undefined && point.p50 !== undefined && point.p90 !== undefined &&
    [point.p10, point.p50, point.p90].every(value => Number.isFinite(Number(value))) &&
    Number(point.p10) <= Number(point.p50) && Number(point.p50) <= Number(point.p90));
  const data = points.map(point => ({ date: point.date, balance: Number(point.balance),
    median: complete ? Number(point.p50) : undefined,
    interval: complete ? [Number(point.p10), Number(point.p90)] : undefined }));
  return <><div style={{ height: 320 }} role="img" aria-label={complete
    ? 'Saldo puntual, mediana P50 y banda experimental P10 a P90. Valores diarios en la tabla siguiente.'
    : 'Saldo puntual experimental. Valores diarios en la tabla siguiente.'}>
    <ResponsiveContainer width="100%" height="100%"><ComposedChart data={data}>
      <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" /><YAxis tickFormatter={value => `${Number(value) / 1000000} M`} />
      <Tooltip formatter={value => Array.isArray(value) ? value.map(item => money(Number(item))).join(' — ') : money(Number(value))} /><Legend />
      {complete && <Area dataKey="interval" name="P10–P90 experimental" stroke="none" fill="#187a69" fillOpacity={0.16} isAnimationActive={false} />}
      <Line dataKey="balance" name="Saldo puntual COP" stroke="#187a69" dot={false} isAnimationActive={false} />
      {complete && <Line dataKey="median" name="Mediana P50 COP" stroke="#6c4daa" strokeDasharray="5 3" dot={false} isAnimationActive={false} />}
    </ComposedChart></ResponsiveContainer>
  </div>{complete && <p className="footnote">Banda predictiva experimental, no calibrada. P50 es mediana y puede diferir del saldo puntual. No representa probabilidad de déficit ni garantiza cobertura de toda la trayectoria.</p>}</>;
}
