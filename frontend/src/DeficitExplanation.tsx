type Commitment = { id: number; description: string; due_date: string; direction: string; amount: string };

export function DeficitExplanation({ firstDeficit, asOf, balance, obligations, money, dateLabel }: {
  firstDeficit: string; asOf: string; balance: string; obligations: Commitment[];
  money: (value: string) => string; dateLabel: (value: string) => string;
}) {
  const payments = obligations.filter(row => row.direction === 'out' && row.due_date <= firstDeficit);
  return <aside className="warning"><h2>Revisa tu caja antes del {dateLabel(firstDeficit)}</h2>
    <p>El escenario parte de {money(balance)} al corte {dateLabel(asOf)} y aplica los cobros y pagos pendientes en su vencimiento. El saldo proyectado es negativo el {dateLabel(firstDeficit)}.</p>
    {payments.length > 0 ? <><p>Pagos registrados hasta esa fecha: {payments.length}. Primeros cinco por vencimiento:</p>
      <ul>{payments.slice(0, 5).map(row => <li key={row.id}>{row.description} · {dateLabel(row.due_date)} · {money(row.amount)}</li>)}</ul>
      <p>Revisa también los cobros esperados y todos los compromisos en el calendario. Un cobro registrado puede retrasarse; cambiar una fecha aquí requiere editar su obligación.</p>
    </> : <p>No hay pagos registrados hasta esa fecha. Revisa el saldo al corte y los cobros pendientes: un saldo inicial negativo puede mantener el déficit sin nuevos pagos.</p>}
    <p>Esta explicación usa obligaciones conocidas. No estima probabilidad de déficit ni demuestra qué ocurrirá al aplazar un pago.</p>
  </aside>;
}
