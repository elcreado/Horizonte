import { FormEvent, useEffect, useState } from 'react';
type Account = { id: number; name: string; connection_id: number | null; balance: string; balance_date: string; history_complete_from: string | null; history_complete_through: string | null };
export function AccountBalances({ company, revision, onChanged }: { company: string; revision: number; onChanged: () => void }) {
  const [accounts, setAccounts] = useState<Account[]>([]); const [canEdit, setCanEdit] = useState(false);
  const [error, setError] = useState(''); const [notice, setNotice] = useState(''); const [busy, setBusy] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    fetch(`/api/companies/${company}/accounts/`, { signal: controller.signal }).then(async response => { if (!response.ok) throw new Error('No se pudieron consultar los saldos.'); const result = await response.json(); setAccounts(result.accounts); setCanEdit(result.can_import); }).catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [company, revision]);
  async function save(event: FormEvent<HTMLFormElement>, account: Account) {
    event.preventDefault(); const body = Object.fromEntries(new FormData(event.currentTarget)); setBusy(true); setError(''); setNotice('');
    try {
      const csrf = await (await fetch('/api/auth/csrf/')).json();
      const response = await fetch(`/api/companies/${company}/accounts/${account.id}/balance/`, { method: 'PATCH', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf.csrfToken }, body: JSON.stringify(body) });
      const result = await response.json();
      if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : Object.values(result).flat().join(' '));
      setAccounts(items => items.map(item => item.id === account.id ? { ...item, ...result } : item)); setNotice('Saldo y corte actualizados.'); onChanged();
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  async function setCoverage(account: Account, start: string, confirmed: boolean) {
    setBusy(true); setError(''); setNotice('');
    try {
      const csrf = await (await fetch('/api/auth/csrf/')).json();
      const response = await fetch(`/api/companies/${company}/accounts/${account.id}/coverage/`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf.csrfToken },
        body: JSON.stringify({ start, confirmed }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : Object.values(result).flat().join(' '));
      setAccounts(items => items.map(item => item.id === account.id ? { ...item, ...result } : item));
      setNotice(confirmed ? 'Periodo completo confirmado.' : 'Confirmación retirada.'); onChanged();
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  return <section className="panel"><h2>Saldos de cuentas</h2><p>En cuentas manuales, declara el saldo al corte, incluidos los movimientos de ese día. Las cuentas conectadas se actualizan desde su fuente. Todas deben tener el mismo corte para proyectar.</p>{error && <p className="error" role="alert">{error}</p>}{notice && <p role="status">{notice}</p>}{accounts.map(account => account.connection_id ? <div key={account.id} className="toolbar"><strong>{account.name}</strong><span>Saldo COP: {account.balance} · corte {account.balance_date} · fuente conectada</span></div> : <form key={account.id} className="toolbar" onSubmit={event => save(event, account)}><strong>{account.name}</strong><label>Saldo COP<input name="balance" type="number" step="0.01" required defaultValue={account.balance} disabled={!canEdit || busy} /></label><label>Fecha de corte<input name="balance_date" type="date" required defaultValue={account.balance_date} disabled={!canEdit || busy} /></label>{canEdit && <button disabled={busy}>Actualizar saldo y corte</button>}</form>)}<details><summary>Confirmar historial completo para pronóstico experimental</summary><p>En cuentas manuales, confirma solo si conoces todos los movimientos, incluidos días sin actividad, desde la fecha elegida hasta el corte. Importar movimientos nuevos dentro de ese periodo o cambiar el corte retira la confirmación.</p>{accounts.map(account => account.connection_id ? <p key={account.id}>{account.name}: {account.history_complete_from ? `cobertura de la fuente ${account.history_complete_from} a ${account.history_complete_through}` : 'cobertura pendiente de sincronización'}</p> : <form key={account.id} className="toolbar" onSubmit={event => { event.preventDefault(); void setCoverage(account, String(new FormData(event.currentTarget).get('start') || ''), true); }}><strong>{account.name}</strong><span>{account.history_complete_from ? `Confirmado: ${account.history_complete_from} a ${account.history_complete_through}` : 'Sin confirmar'}</span>{canEdit && <><label>Primer día completo<input name="start" type="date" required max={account.balance_date} defaultValue={account.history_complete_from || ''} /></label><button disabled={busy}>Confirmar periodo</button>{account.history_complete_from && <button className="secondary" type="button" disabled={busy} onClick={() => void setCoverage(account, account.history_complete_from || account.balance_date, false)}>Retirar confirmación</button>}</>}</form>)}</details></section>;
}
