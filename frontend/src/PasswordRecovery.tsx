import { FormEvent, useState } from 'react';

export function PasswordRecovery({ route }: { route: string }) {
  const resetting = route.startsWith('#/reset-password');
  const query = new URLSearchParams(route.split('?')[1] || '');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError('');
    const body = Object.fromEntries(new FormData(event.currentTarget));
    if (resetting) { body.uid = query.get('uid') || ''; body.token = query.get('token') || ''; }
    try {
      const csrfResponse = await fetch('/api/auth/csrf/');
      if (!csrfResponse.ok) throw new Error('No se pudo verificar la sesión.');
      const csrf = await csrfResponse.json();
      const response = await fetch(`/api/auth/${resetting ? 'reset-password' : 'recover-password'}/`, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf.csrfToken }, body: JSON.stringify(body) });
      const result = await response.json();
      if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : Object.values(result).flat().join(' '));
      setNotice(result.detail);
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }
  return <main className="login"><a className="brand" href="#/">◈ HORIZONTE</a><h1>{resetting ? 'Elige una nueva contraseña.' : 'Recupera tu acceso.'}</h1>
    {notice ? <p role="status">{notice}</p> : <form onSubmit={submit}>{resetting ? <><label>Nueva contraseña<input name="password" type="password" autoComplete="new-password" minLength={10} maxLength={128} required /></label><label>Confirmar contraseña<input name="password_confirm" type="password" autoComplete="new-password" minLength={10} maxLength={128} required /></label></> : <><p>Introduce el usuario y correo registrados.</p><label>Usuario<input name="username" autoComplete="username" required maxLength={150} /></label><label>Correo electrónico<input name="email" type="email" autoComplete="email" required maxLength={254} /></label></>}
      {error && <p className="error" role="alert">{error}</p>}<button disabled={busy}>{busy ? 'Procesando…' : resetting ? 'Cambiar contraseña' : 'Solicitar enlace'}</button></form>}
    <p><a href="#/login">Volver a iniciar sesión</a></p>
  </main>;
}
