import { FormEvent, useState } from 'react';

export function Register({ onRegistered }: { onRegistered: (username: string) => void }) {
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setBusy(true);
    const body = Object.fromEntries(new FormData(event.currentTarget));
    try {
      const csrfResponse = await fetch('/api/auth/csrf/');
      if (!csrfResponse.ok) throw new Error('No se pudo verificar la sesión.');
      const csrf = await csrfResponse.json();
      const response = await fetch('/api/auth/register/', { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf.csrfToken }, body: JSON.stringify(body) });
      const result = await response.json();
      if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : Object.values(result).flat().join(' '));
      onRegistered(result.username);
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }
  return <main className="login" style={{ maxWidth: 850 }}><a className="brand" href="#/">◈ HORIZONTE</a><h1>Crea tu espacio de trabajo.</h1><p>Registra tu usuario, empresa y una cuenta manual para comenzar. El saldo es declarado por ti; no conecta un banco ni verifica su titularidad.</p>
    <form onSubmit={submit}><h2>Tu cuenta</h2><div className="obligation-form">
      <label>Usuario<input name="username" autoComplete="username" maxLength={150} required /></label><label>Correo electrónico<input name="email" type="email" autoComplete="email" maxLength={254} required /></label>
      <label>Contraseña (mínimo 10 caracteres)<input name="password" type="password" autoComplete="new-password" minLength={10} maxLength={128} required /></label><label>Confirmar contraseña<input name="password_confirm" type="password" autoComplete="new-password" minLength={10} maxLength={128} required /></label>
    </div><h2>Empresa y saldo de partida</h2><p>Este entorno sigue siendo académico. Utiliza datos sintéticos para las pruebas.</p><div className="obligation-form">
      <label>Nombre de la empresa<input name="company_name" maxLength={200} required /></label><label>NIT o identificador de prueba<input name="nit" maxLength={30} placeholder="TEST-EMPRESA-001" required /></label>
      <label>Nombre de la cuenta manual<input name="account_name" maxLength={120} placeholder="Cuenta principal" required /></label><label>Saldo disponible COP<input name="opening_balance" type="number" step="0.01" required /></label><label>Fecha de corte<input name="balance_date" type="date" required /></label>
    </div>{error && <p role="alert" className="error">{error}</p>}<button disabled={busy}>{busy ? 'Creando cuenta…' : 'Crear cuenta y empresa'}</button><p>¿Ya tienes cuenta? <a href="#/login">Iniciar sesión</a></p></form>
  </main>;
}
