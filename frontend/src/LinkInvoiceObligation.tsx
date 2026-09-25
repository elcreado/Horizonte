import { FormEvent, useEffect, useState } from 'react';

type Candidate = { id: number; reference: string; description: string; counterparty: string; due_date: string; outstanding_amount: string };
type Page = { results: Candidate[]; next: string | null; previous: string | null; count: number };

export function LinkInvoiceObligation({ company, invoice, onLinked }: { company: string; invoice: number; onLinked: () => void }) {
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Page | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const base = `/api/companies/${company}/invoices/${invoice}/obligation-link/`;
  useEffect(() => {
    const controller = new AbortController(); setData(null); setError('');
    fetch(`${base}?page=${page}`, { signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error('No se pudieron consultar las obligaciones compatibles.');
      setData(await response.json());
    }).catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [base, page]);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError('');
    const fields = new FormData(event.currentTarget);
    try {
      const csrfResponse = await fetch('/api/auth/csrf/');
      if (!csrfResponse.ok) throw new Error('No se pudo verificar la sesión.');
      const csrf = await csrfResponse.json();
      const response = await fetch(base, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf.csrfToken }, body: JSON.stringify({ obligation_id: Number(fields.get('obligation_id')) }) });
      const result = await response.json();
      if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : Object.values(result).flat().join(' '));
      onLinked();
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }
  return <div className="panel"><h3>¿Ya registraste esta cuenta por cobrar o pagar?</h3><p>Vincula la obligación existente para evitar contarla dos veces. Se conservarán su pendiente, fecha y conciliaciones. Revisa la contraparte y referencia antes de elegir.</p>
    {error && <p className="error" role="alert">{error}</p>}
    {!data && !error && <p role="status">Cargando obligaciones compatibles…</p>}
    {data && <>{data.count ? <form onSubmit={submit}><label>Obligación existente<select name="obligation_id" required>{data.results.map(o => <option key={o.id} value={o.id}>{o.reference} · {o.description} · {o.counterparty || 'Sin contraparte'} · {o.due_date} · pendiente {o.outstanding_amount} COP</option>)}</select></label><p className="footnote">Solo se muestran obligaciones del mismo sentido, vigentes y aún no vinculadas a una factura.</p><button disabled={busy}>{busy ? 'Vinculando…' : 'Vincular sin crear otra obligación'}</button></form> : <p>No hay obligaciones compatibles sin vincular.</p>}
      <div className="toolbar"><button className="secondary" disabled={busy || !data.previous} onClick={() => setPage(n => n - 1)}>Anterior</button><span>Página {page}</span><button className="secondary" disabled={busy || !data.next} onClick={() => setPage(n => n + 1)}>Siguiente</button></div></>}
  </div>;
}
