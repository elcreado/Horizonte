import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

export function DashboardChart({ points, dateLabel, money }: {
  points: { date: string; balance: string }[];
  dateLabel: (value: string) => string;
  money: (value: number) => string;
}) {
  return <ResponsiveContainer width="100%" height="100%"><LineChart data={points.map(p => ({ ...p, balance: Number(p.balance) }))} margin={{ left: 0, right: 12, top: 15 }}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="date" tickFormatter={dateLabel} minTickGap={55} /><YAxis width={72} tickFormatter={v => new Intl.NumberFormat('es-CO', { notation: 'compact', maximumFractionDigits: 1 }).format(Number(v))} /><Tooltip formatter={v => money(Number(v))} labelFormatter={v => dateLabel(String(v))} /><ReferenceLine y={0} stroke="#b34035" strokeDasharray="5 5" /><Line type="stepAfter" dataKey="balance" name="Saldo" stroke="#227760" strokeWidth={3} dot={false} isAnimationActive={false} /></LineChart></ResponsiveContainer>;
}
