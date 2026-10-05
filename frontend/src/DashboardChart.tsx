import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

export function DashboardChart({ points, dateLabel, money }: {
  points: { date: string; balance: string }[];
  dateLabel: (value: string) => string;
  money: (value: number) => string;
}) {
  return <ResponsiveContainer width="100%" height="100%"><LineChart data={points.map(p => ({ ...p, balance: Number(p.balance) }))} margin={{ left: 15, right: 15, top: 15 }}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="date" tickFormatter={dateLabel} minTickGap={55} /><YAxis tickFormatter={v => `${Number(v) / 1000000} M`} /><Tooltip formatter={v => money(Number(v))} labelFormatter={v => dateLabel(String(v))} /><ReferenceLine y={0} stroke="#b34035" strokeDasharray="5 5" /><Line type="stepAfter" dataKey="balance" name="Saldo" stroke="#227760" strokeWidth={3} dot={false} isAnimationActive={false} /></LineChart></ResponsiveContainer>;
}
