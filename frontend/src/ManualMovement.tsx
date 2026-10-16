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
        ? 'Movimiento guardado después del corte actual. Actualiza el saldo y la fecha de corte en Cuentas y saldos para incluirlo en la predicción.'
        : 'Movimiento guardado. El saldo declarado no cambia. Revisa la cobertura del historial en Cuentas y saldos antes de recalcular el pronóstico.');
      onChanged();
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }
  const selected = accounts?.find(item => String(item.id) === account);
  return <section className="panel"><h2>Registrar movimiento</h2>
    <p>Lleva tus transacciones manualmente sin conectar un banco. La fecha inicial es hoy (hora de Colombia); puedes cambiarla si la operación ocurrió antes. Puedes registrar varios movimientos el mismo día. El historial hasta el corte alimenta la estimación; el saldo declarado ya incluye esas operaciones y no se suma otra vez. Los compromisos futuros van en Cobros y pagos.</p>
    {selected && date > selected.balance_date && <p className="notice">El corte de esta cuenta es {selected.balance_date}. Puedes guardar el movimiento; para incorporarlo a la predicción, actualiza después el corte y el saldo en <a href="#/dashboard/accounts">Cuentas y saldos</a>.</p>}
    {error && <p role="alert" className="error">{error}</p>}{notice && <p role="status">{notice}</p>}
    {!accounts && !error && <p role="status">Cargando cuentas…</p>}
    {!accounts && error && <button onClick={() => setReload(value => value + 1)}>Reintentar consulta</button>}
    {accounts && !canEdit && <p>Tu rol permite consultar. Un propietario o contador puede registrar movimientos.</p>}
    {canEdit && accounts?.length === 0 && <p>Esta empresa no tiene cuentas manuales. En Empresa y equipo puedes crear una empresa con cuenta manual.</p>}
    {canEdit && Boolean(accounts?.length) && <form onSubmit={save}>
      <fieldset className="manual-movement-fields" disabled={busy || pending}>
        <label>Cuenta manual<select value={account} onChange={e => setAccount(e.target.value)}>{accounts?.map(item => <option key={item.id} value={item.id}>{item.name} · corte {item.balance_date}</option>)}</select></label>
        <label>Fecha del movimiento<input type="date" name="date" value={date} onChange={event => setDate(event.target.value)} max={businessToday()} required /></label>
        <label>Tipo<select value={direction} onChange={e => setDirection(e.target.value)}><option value="in">Ingreso</option><option value="out">Egreso</option></select></label>
        <label>Importe positivo COP<input type="number" name="amount" min="0.01" max="9999999999999999.99" step="0.01" required /></label>
        <label>Descripción<input name="description" maxLength={250} required /></label>
        <label>Categoría<select name="category" key={direction}><option value="">Clasificar automáticamente</option>{(direction === 'in' ? income : expense).map(value => <option key={value}>{value}</option>)}</select></label>
      </fieldset>
      {pending && !busy && <p role="status">No se confirmó el guardado. Reintenta con la misma solicitud para evitar duplicados.</p>}
      <button disabled={busy}>{busy ? 'Guardando…' : pending ? 'Reintentar guardado' : 'Guardar movimiento'}</button>
    </form>}
  </section>;
}
