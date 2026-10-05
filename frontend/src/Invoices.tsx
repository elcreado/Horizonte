import { LinkInvoiceObligation } from './LinkInvoiceObligation';
import { FormEvent, useEffect, useState } from 'react';

type Invoice = { id: number; number: string; cufe: string; direction: string; issue_date: string; due_date: string | null; supplier: string; customer: string; subtotal: string; tax: string; total: string; payable: string; obligation_id: number | null; outstanding_amount: string | null; cancelled: boolean };
type Page = { results: Invoice[]; count: number; previous: string | null; next: string | null; can_edit: boolean };
type Job = { id: number; status: string; error: string; duplicate: boolean };
const money = (value: string) => new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP' }).format(Number(value));

export function Invoices({ company, onChange }: { company: string; onChange: () => void }) {
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Page | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [error, setError] = useState('');
  const [statusError, setStatusError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<Invoice | null>(null);
  const [revision, setRevision] = useState(0);
  const base = `/api/companies/${company}/invoices/`;
  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function load() {
      try {
        const [invoices, imports] = await Promise.all([fetch(`${base}?page=${page}`, { signal: controller.signal }), fetch(`${base}imports/`, { signal: controller.signal })]);
        if (!invoices.ok || !imports.ok) throw new Error('No se pudieron consultar las facturas.');
        const [invoiceData, importData] = await Promise.all([invoices.json(), imports.json()]);
        if (!controller.signal.aborted) { setData(invoiceData); setJobs(importData); setStatusError(''); }
      } catch (e) { if (!controller.signal.aborted) setStatusError((e as Error).message); }
      if (!controller.signal.aborted) timer = setTimeout(load, 4000);
    }
    setError(''); void load();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [base, page, revision]);

  async function send(url: string, body: FormData | object): Promise<boolean> {
    setBusy(true); setError(''); setNotice('');
    try {
      const csrfResponse = await fetch('/api/auth/csrf/');
      if (!csrfResponse.ok) throw new Error('No se pudo verificar la sesión.');
      const csrf = await csrfResponse.json();
      const headers: Record<string, string> = { 'X-CSRFToken': csrf.csrfToken };
      if (!(body instanceof FormData)) headers['Content-Type'] = 'application/json';
      const response = await fetch(url, { method: 'POST', headers, body: body instanceof FormData ? body : JSON.stringify(body) });
      const result = await response.json();
      if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : Object.values(result).flat().join(' '));
      setRevision(n => n + 1); return true;
    } catch (e) { setError((e as Error).message); return false; }
    finally { setBusy(false); }
  }
  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = event.currentTarget;
    if (await send(`${base}imports/`, new FormData(form))) { form.reset(); setNotice('Factura enviada a la cola de importación.'); }
  }
  async function confirm(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (!selected) return;
    if (await send(`${base}${selected.id}/confirm/`, Object.fromEntries(new FormData(event.currentTarget)))) {
      setSelected(null); onChange(); setNotice('Valor pendiente confirmado. La factura está vinculada a una única obligación.');
    }
  }
  return <section className="panel"><h2>Facturas XML</h2><p>Importa una factura emitida o recibida en UBL 2.1. El NIT de la empresa debe aparecer como emisor o receptor.</p>
    <p className="footnote">La lectura no valida la firma ni certifica aceptación DIAN. Confirma el pendiente antes de incorporarlo a tu proyección.</p>
    <p><a href="/factura-ejemplo.xml" download>Descargar ejemplo sintético para Café Horizonte</a></p>
    {data?.can_edit && <form className="toolbar" onSubmit={upload}><label>Factura XML UTF-8, hasta 2 MB<input name="file" type="file" accept=".xml,text/xml,application/xml" required /></label><button disabled={busy}>Importar factura</button></form>}
    {error && <p className="error" role="alert">{error}</p>}{notice && <p role="status">{notice}</p>}
    {statusError && <p className="error" role="alert">{statusError} Se volverá a consultar automáticamente.</p>}
    <div aria-live="polite">{jobs.slice(0, 5).map(j => <p key={j.id}>Importación #{j.id}: {j.status === 'queued' ? 'En cola o procesando. Puede tardar si el servicio se está reactivando; vuelve a consultar más tarde.' : j.status === 'failed' ? j.error : j.duplicate ? 'Factura ya existente; no se duplicó.' : 'Leída. Confirma el valor pendiente.'}</p>)}</div>
    {!data && !error && !statusError && <p role="status">Cargando facturas…</p>}
    {data && <><div className="table-wrap"><table><thead><tr><th>Factura</th><th>Contraparte</th><th>Total</th><th>Pendiente</th><th>Acción</th></tr></thead><tbody>{data.results.map(i => <tr key={i.id}><td>{i.number}<small>{i.issue_date} · {i.direction === 'in' ? 'Emitida' : 'Recibida'}</small></td><td>{i.direction === 'in' ? i.customer : i.supplier}</td><td>{money(i.total)}</td><td>{i.obligation_id ? `${money(i.outstanding_amount!)}${i.cancelled ? ' · cancelada' : ''}` : 'Por confirmar'}</td><td><button className="secondary" disabled={busy} onClick={() => setSelected(i)}>Revisar</button></td></tr>)}</tbody></table></div>
      {!data.count && <p>No hay facturas importadas.</p>}<div className="toolbar"><button className="secondary" disabled={!data.previous || busy} onClick={() => { setPage(n => n - 1); setSelected(null); }}>Anterior</button><span>Página {page} · {data.count} facturas</span><button className="secondary" disabled={!data.next || busy} onClick={() => { setPage(n => n + 1); setSelected(null); }}>Siguiente</button></div></>}
    {selected && <div className="panel" key={selected.id}><h3>Factura {selected.number}</h3><p style={{ overflowWrap: 'anywhere' }}>CUFE: {selected.cufe}</p><p>Subtotal {money(selected.subtotal)} · impuestos {money(selected.tax)} · importe pagadero XML {money(selected.payable)}</p>
      <p>El XML no demuestra el cobro o pago. El pendiente confirmado alimentará la proyección sin cambiar el saldo bancario.</p>
      {!selected.obligation_id && data?.can_edit && <LinkInvoiceObligation key={selected.id} company={company} invoice={selected.id} onLinked={() => { setSelected(null); setRevision(n => n + 1); onChange(); setNotice("Factura vinculada a la obligación existente, sin duplicar el pendiente."); }} />}
      {!selected.obligation_id && data?.can_edit && <form className="obligation-form" onSubmit={confirm}><label>Vencimiento o fecha esperada<input name="due_date" type="date" defaultValue={selected.due_date || ''} min={selected.issue_date} required /></label><label>Pendiente confirmado COP<input name="outstanding_amount" type="number" min="0" step="0.01" max={selected.payable} required /></label><button disabled={busy}>Crear nueva obligación con este pendiente</button></form>}
      {selected.obligation_id && <p>Vinculada a la obligación #{selected.obligation_id}. Puedes conciliar o cambiar su fecha en Cuentas por cobrar y pagar.</p>}
      <button className="secondary" disabled={busy} onClick={() => setSelected(null)}>Cerrar</button></div>}
  </section>;
}
