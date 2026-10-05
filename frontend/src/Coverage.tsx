export type CoverageData = { start: string; as_of: string; notice: string; accounts: { account_id: number; name: string; state: string; count: number; first: string | null; last: string | null; span_days: number; active_days: number; days_since_last: number | null; other_category_count: number }[] };
function historyStage(days: number) {
  if (days < 30) return 'Datos insuficientes';
  if (days < 90) return 'Proyección experimental';
  if (days < 365) return 'Historial intermedio';
  return 'Historial extendido';
}
export function Coverage({ data }: { data: CoverageData }) {
  return <section className="panel"><h2>Cobertura del historial</h2><p>{data.notice}</p><p>Ventana revisada: {data.start} a {data.as_of}.</p><p>Etapas por amplitud observada: 0–29 días, datos insuficientes; 30–89, proyección experimental; 90–364, historial intermedio; 365, historial extendido en esta ventana. Estas etiquetas no son niveles de precisión predictiva ni confirman que el historial esté completo.</p><div className="table-wrap"><table><thead><tr><th scope="col">Cuenta</th><th scope="col">Historial observado</th><th scope="col">Movimientos</th><th scope="col">Fechas</th><th scope="col">Última actividad</th></tr></thead><tbody>{data.accounts.map(account => <tr key={account.account_id}><th scope="row">{account.name}</th><td>{historyStage(account.span_days)}{account.state === 'empty' && <small>Sin movimientos</small>}<small>{account.active_days} días con registros · {account.span_days} días entre extremos, incluidos</small></td><td>{account.count}<small>{account.other_category_count} en Otros</small></td><td>{account.first && account.last ? `${account.first} a ${account.last}` : 'Sin datos'}</td><td>{account.days_since_last === null ? 'Sin datos' : `${account.days_since_last} días antes del corte`}</td></tr>)}</tbody></table></div><p>Importa el historial faltante de cada cuenta y revisa las categorías. Las empresas sin movimientos pueden seguir registrando obligaciones.</p></section>;
}
