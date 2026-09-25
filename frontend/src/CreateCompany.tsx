import { FormEvent, useState } from 'react';
export function CreateCompany({ onCreated }: { onCreated: (company: { id: number; name: string }) => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = event.currentTarget;
    const body = Object.fromEntries(new FormData(form)); setBusy(true); setError('');
    try {
      const csrf = await (await fetch('/api/auth/csrf/')).json();
      const response = await fetch('/api/companies/create/', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf.csrfToken }, body: JSON.stringify(body) });
      const result = await response.json();
      if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : Object.values(result).flat().join(' '));
      form.reset(); onCreated(result);
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }
  return <section className="panel"><details><summary>Crear otra empresa</summary><p>Serás su propietario. Declara una cuenta y su saldo al corte; esta acción no conecta con un banco.</p><form className="obligation-form" onSubmit={submit}><label>Nombre de empresa<input name="company_name" required maxLength={200} /></label><label>NIT<input name="nit" required maxLength={30} pattern="[A-Za-z0-9-]+" /></label><label>Nombre de cuenta<input name="account_name" required maxLength={120} /></label><label>Saldo COP al corte<input name="opening_balance" type="number" step="0.01" required /></label><label>Fecha de corte<input name="balance_date" type="date" required /></label>{error && <p className="error" role="alert">{error}</p>}<button disabled={busy}>{busy ? 'Creando…' : 'Crear empresa'}</button></form></details></section>;
}
