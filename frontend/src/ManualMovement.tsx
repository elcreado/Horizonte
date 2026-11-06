import { FormEvent, useEffect, useRef, useState } from 'react';
import { getCsrf } from './csrf';

type Account = { id: number; name: string; connection_id: number | null; balance_date: string };
const businessToday = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Bogota', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
const income = ['Ventas', 'Servicios', 'Financiación', 'Otros'];
const expense = ['Nómina', 'Proveedores', 'Arriendo', 'Servicios públicos', 'Impuestos', 'Software', 'Transporte', 'Marketing', 'Deuda', 'Inventario', 'Otros'];

export function ManualMovement({ company, revision, onChanged }: { company: string; revision: number; onChanged: () => void }) {
  const [accounts, setAccounts] = useState<Account[] | null>(null);
  const [canEdit, setCanEdit] = useState(false);
  const [account, setAccount] = useState('');
  const [direction, setDirection] = useState('in');
  const [date, setDate] = useState(businessToday);
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [reload, setReload] = useState(0);
  const receipt = useRef<{ request_id: string; account_id: string; date: string; direction: string; amount: string; description: string; category: string } | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    fetch(`/api/companies/${company}/accounts/`, { signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error('No se pudieron consultar las cuentas.');
      const result = await response.json();
      if (controller.signal.aborted) return;
      const manual: Account[] = result.accounts.filter((item: Account) => !item.connection_id);
      setAccounts(manual); setCanEdit(result.can_import); setError('');
      setAccount(value => manual.some(item => String(item.id) === value) ? value : String(manual[0]?.id || ''));
    }).catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [company, revision, reload]);
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy) return;
    const form = event.currentTarget;
    const fields = new FormData(form);
    const body = receipt.current || {
      request_id: crypto.randomUUID(), account_id: account, direction,
      date: String(fields.get('date')), amount: String(fields.get('amount')),
      description: String(fields.get('description')), category: String(fields.get('category') || ''),
    };
    receipt.current = body; setBusy(true); setPending(true); setError(''); setNotice('');
    try {
      const csrf = await getCsrf();
      const response = await fetch(`/api/companies/${company}/movements/`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf.csrfToken }, body: JSON.stringify(body),
      });
      const result = await response.json();
      if (!response.ok) {
        if (response.status < 500) { receipt.current = null; setPending(false); }
        throw new Error(typeof result.detail === 'string' ? result.detail : Object.values(result).flat().join(' '));
      }
      receipt.current = null; setPending(false); form.reset(); setDate(businessToday());
      setNotice(body.date > (accounts?.find(item => String(item.id) === body.account_id)?.balance_date || '')
        ? 'Movimiento guardado e incluido en la estimación del Resumen. Para los pronósticos avanzados al corte, actualiza el saldo y la fecha en Cuentas y saldos.'
        : 'Movimiento guardado. La gráfica del Resumen se recalculó; el saldo declarado no se vuelve a sumar. Revisa la cobertura para los pronósticos avanzados.');
      onChanged();
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }
  const errorMessage = useRef<HTMLParagraphElement>(null);
  useEffect(() => { if (error) errorMessage.current?.focus(); }, [error]);
  const selected = accounts?.find(item => String(item.id) === account);
  return <section className="panel manual-entry"><div className="section-heading"><div><h2>Registrar movimiento</h2><p>¿Entró o salió dinero? Registra la operación aquí.</p></div><span className="section-badge">Captura manual</span></div>
    <details className="form-explainer"><summary>Cómo afecta este movimiento a tu caja</summary><p>Puedes registrar varios movimientos el mismo día, sin conectar un banco. El Resumen se recalcula al guardar: los movimientos posteriores al corte actualizan la caja; los anteriores alimentan la estimación sin sumarse otra vez al saldo declarado. Para un pago que aún no ocurrió, usa <a href="#/dashboard/obligations">Cobros y pagos</a>.</p></details>
    {selected && date > selected.balance_date && <p className="notice">El corte de esta cuenta es {selected.balance_date}. El Resumen incluirá esta operación al guardarla. Para los modelos avanzados actualiza el corte y el saldo en <a href="#/dashboard/accounts">Cuentas y saldos</a>.</p>}
    {error && <p ref={errorMessage} tabIndex={-1} role="alert" className="error">{error}</p>}{notice && <p role="status">{notice}</p>}
    {!accounts && !error && <p role="status">Cargando cuentas…</p>}
    {!accounts && error && <button onClick={() => setReload(value => value + 1)}>Reintentar consulta</button>}
    {accounts && !canEdit && <p>Tu rol permite consultar. Un propietario o contador puede registrar movimientos.</p>}
    {canEdit && accounts?.length === 0 && <p>Esta empresa no tiene cuentas manuales. En Empresa y equipo puedes crear una empresa con cuenta manual.</p>}
    {canEdit && Boolean(accounts?.length) && <form onSubmit={save} autoComplete="off">
      <fieldset className="manual-movement-fields" disabled={busy || pending}><legend className="sr-only">Datos del movimiento</legend>
        <label>Cuenta manual<select name="account" value={account} onChange={e => setAccount(e.target.value)}>{accounts?.map(item => <option key={item.id} value={item.id}>{item.name} · corte {item.balance_date}</option>)}</select></label>
        <label>Fecha del movimiento<input type="date" name="date" value={date} onChange={event => setDate(event.target.value)} max={businessToday()} aria-describedby="movement-date-help" required /><small id="movement-date-help">Hoy en Colombia. Puedes elegir una fecha anterior.</small></label>
        <fieldset className="movement-type"><legend>Tipo de movimiento</legend><div><label><input type="radio" name="direction" value="in" checked={direction === 'in'} onChange={() => setDirection('in')} /><span>Ingreso<small>Entró dinero</small></span></label><label><input type="radio" name="direction" value="out" checked={direction === 'out'} onChange={() => setDirection('out')} /><span>Egreso<small>Salió dinero</small></span></label></div></fieldset>
        <label>Valor del movimiento (COP)<input type="number" inputMode="decimal" name="amount" min="0.01" max="9999999999999999.99" step="0.01" aria-describedby="movement-amount-help" required /><small id="movement-amount-help">Escribe un valor positivo, sin signo ni separadores de miles.</small></label>
        <label>Descripción<input name="description" maxLength={250} placeholder="Ej.: Venta del día…" required /></label>
        <label>Categoría<select name="category" aria-describedby="movement-category-help" key={direction}><option value="">Clasificar automáticamente</option>{(direction === 'in' ? income : expense).map(value => <option key={value}>{value}</option>)}</select><small id="movement-category-help">Puedes dejar que Horizonte sugiera una categoría.</small></label>
      </fieldset>
      {pending && !busy && <p role="status">No se confirmó el guardado. Reintenta con la misma solicitud para evitar duplicados.</p>}
      <button disabled={busy}>{busy ? 'Guardando…' : pending ? 'Reintentar guardado' : 'Guardar movimiento'}</button>
    </form>}
  </section>;
}
