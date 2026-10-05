import { FormEvent, useEffect, useState } from 'react';

type Account = { id: number; name: string; balance_date: string; connection_id: number | null };
type Job = { id: number; status: string; created_count: number; duplicate_count: number; error: string };

export function ImportPanel({ company, revision }: { company: string; revision: number }) {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [canImport, setCanImport] = useState(false);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [error, setError] = useState('');
  const [statusError, setStatusError] = useState('');
  const [accountsError, setAccountsError] = useState('');
  const [sending, setSending] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    let accountsLoaded = false;
    async function load() {
      if (!accountsLoaded && !controller.signal.aborted) {
        try {
          const response = await fetch(`/api/companies/${company}/accounts/`, { signal: controller.signal });
          if (!response.ok) throw new Error('No se pudieron consultar las cuentas.');
          const result = await response.json();
          if (!controller.signal.aborted) {
            setAccounts(result.accounts.filter((account: Account) => !account.connection_id));
            setCanImport(result.can_import); setAccountsError(''); accountsLoaded = true;
          }
        } catch (error) { if (!controller.signal.aborted) setAccountsError((error as Error).message); }
      }
      try {
        const response = await fetch(`/api/companies/${company}/imports/`, { signal: controller.signal });
        if (!response.ok) throw new Error('No se pudo consultar el estado de las importaciones.');
        const result = await response.json();
        if (!controller.signal.aborted) { setJobs(result); setStatusError(''); }
      } catch (e) { if (!controller.signal.aborted) setStatusError((e as Error).message); }
      if (!controller.signal.aborted) timer = setTimeout(load, 3000);
    }
    void load();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [company, revision]);

  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setSending(true); setError('');
    const form = event.currentTarget;
    try {
      const tokenResponse = await fetch('/api/auth/csrf/');
      const token = await tokenResponse.json();
      const response = await fetch(`/api/companies/${company}/imports/`, {
        method: 'POST', headers: { 'X-CSRFToken': token.csrfToken }, body: new FormData(form),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'No se pudo cargar el archivo.');
      setJobs(previous => [result, ...previous].slice(0, 20)); form.reset();
    } catch (e) { setError((e as Error).message); }
    finally { setSending(false); }
  }

  return <section className="panel"><h2>Importar movimientos</h2>
    <p>CSV o XLSX en pesos colombianos · máximo 2 MB y 10.000 filas. Los ingresos son positivos y los egresos negativos.</p>
    <p><a href="/movimientos-ejemplo.csv" download>Descargar CSV de ejemplo</a></p>
    <p className="footnote">Columnas: external_id, date, amount, description. Fechas AAAA-MM-DD; decimales con punto. Cada movimiento necesita un ID estable. En XLSX: una sola hoja, columnas A–D, IDs como texto y sin fórmulas. Importar historial no cambia el saldo disponible ni las obligaciones.</p>
    {canImport && <form onSubmit={upload} className="toolbar">
      <label>Cuenta<select name="account_id" required>{accounts.map(a => <option value={a.id} key={a.id}>{a.name} · corte {a.balance_date}</option>)}</select></label>
      <label>Archivo CSV o XLSX<input name="file" type="file" accept=".csv,.xlsx,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" required /></label>
      <button disabled={sending || !accounts.length}>{sending ? 'Enviando…' : 'Importar archivo'}</button>
    </form>}
    {!canImport && <p>El propietario o contador puede importar movimientos.</p>}
    {error && <p role="alert" className="error">{error}</p>}
    {statusError && <p className="error" role="alert">{statusError} Se volverá a consultar automáticamente.</p>}
    {accountsError && <p className="error" role="alert">{accountsError} Se volverá a consultar automáticamente.</p>}
    <div aria-live="polite">{jobs.map(job => <p key={job.id}><strong>Importación #{job.id}: </strong>
      {job.status === 'queued' ? 'En cola o procesando. Puede tardar si el servicio se está reactivando. Si no avanza, vuelve a consultar más tarde o contacta al administrador.' : job.status === 'completed' ? `${job.created_count} movimientos nuevos y ${job.duplicate_count} duplicados omitidos. Recarga el panorama para verlos.` : job.error}
    </p>)}</div>
  </section>;
}
