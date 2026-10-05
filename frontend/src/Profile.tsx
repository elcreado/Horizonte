import { getCsrf } from './csrf';
import { FormEvent, useEffect, useState } from 'react';
export function Profile() {
  const [data, setData] = useState<{ username: string; email: string } | null>(null);
  const [error, setError] = useState(''); const [notice, setNotice] = useState(''); const [busy, setBusy] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    fetch('/api/auth/profile/', { signal: controller.signal }).then(async response => { if (!response.ok) throw new Error('No se pudo consultar tu cuenta.'); setData(await response.json()); }).catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, []);
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = event.currentTarget;
    const values = Object.fromEntries(new FormData(form));
    if (!values.password) { delete values.password; delete values.password_confirm; }
    setBusy(true); setError(''); setNotice('');
    try {
      const csrf = await getCsrf();
      const response = await fetch('/api/auth/profile/', { method: 'PATCH', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf.csrfToken }, body: JSON.stringify(values) });
      const result = await response.json();
      if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : Object.values(result).flat().join(' '));
      setData(result); form.reset(); setNotice('Cuenta actualizada. Si cambiaste la contraseña, las otras sesiones requerirán iniciar sesión de nuevo.');
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  return <main><a href="#/dashboard">Volver al dashboard</a><h1>Mi cuenta</h1>{error && <p role="alert" className="error">{error}</p>}{notice && <p role="status">{notice}</p>}{!data && !error && <p>Cargando cuenta…</p>}{data && <form className="panel" onSubmit={save}><p>Usuario: {data.username}</p><label>Correo para recuperación<input name="email" type="email" required maxLength={254} defaultValue={data.email} /></label><label>Contraseña actual<input name="current_password" type="password" autoComplete="current-password" required maxLength={128} /></label><label>Nueva contraseña (opcional)<input name="password" type="password" autoComplete="new-password" minLength={10} maxLength={128} /></label><label>Repite la nueva contraseña<input name="password_confirm" type="password" autoComplete="new-password" maxLength={128} /></label><p>La nueva contraseña debe tener al menos 10 caracteres y superar las validaciones de seguridad.</p><button disabled={busy}>{busy ? 'Guardando…' : 'Guardar cambios'}</button></form>}</main>;
}
