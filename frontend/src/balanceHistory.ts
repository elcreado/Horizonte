export type BalancePoint = { date: string; balance: string | null; status: 'declared' | 'reconstructed' | 'unknown' };
export type BalanceWindow = '30' | '90' | 'all';
export type BalanceHistoryData = {
  currency: 'COP'; cutoff: string; declared_balance: string; complete_from: string | null; notice: string;
  points: BalancePoint[];
  accounts: { account_id: number; name: string; declared_balance: string; balance_date: string; complete_from: string | null; complete_through: string | null; coverage_valid: boolean; coverage_source: 'source' | 'manual_confirmation' }[];
};

// Keep cent precision in tables even when the amount exceeds Number's safe range.
export function exactCop(value: string | null): string {
  if (value === null) return 'Sin cobertura';
  const parts = /^(-?)(\d+)\.(\d{2})$/.exec(value);
  if (!parts) return 'Saldo no disponible';
  return `${parts[1]}$ ${parts[2].replace(/\B(?=(\d{3})+(?!\d))/g, '.')},${parts[3]}`;
}

export function balanceChartPoints(points: BalancePoint[]) {
  return points.map(point => ({ ...point, balance: point.balance === null ? null : Number(point.balance) }));
}

export function selectBalancePoints(points: BalancePoint[], window: BalanceWindow) {
  return points.slice(window === 'all' ? 0 : -Number(window));
}
