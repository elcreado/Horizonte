import { AuditHistory } from './AuditHistory';
import { FormEvent, useEffect, useState } from 'react';

type Member = { id: number; username: string; role: string; active: boolean };
type TeamData = { results: Member[]; count: number; next: string | null; previous: string | null; can_manage: boolean; my_membership_id: number };
const roles = { owner: 'Propietario', accountant: 'Contador', viewer: 'Consulta' };

export function Team({ company, companyName }: { company: string; companyName: string }) {
  const [page, setPage] = useState(1);
  const [data, setData] = useState<TeamData | null>(null);
  const [revision, setRevision] = useState(0);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const base = `/api/companies/${company}/`;
  useEffect(() => {
    const controller = new AbortController(); setError('');
    fetch(`${base}team/?page=${page}`, { signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error('No se pudo consultar el equipo; comprueba tus permisos.');
      setData(await response.json());
    }).catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [base, page, revision]);
  async function change(path: string, method: string, body?: object, reload = false) {
    setBusy(true); setError(''); setNotice('');
    try {
      const csrfResponse = await fetch('/api/auth/csrf/');
      if (!csrfResponse.ok) throw new Error('No se pudo verificar la sesión.');
      const csrf = await csrfResponse.json();
      const response = await fetch(base+path, { method, headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf.csrfToken }, body: body ? JSON.stringify(body) : undefined });
      if (!response.ok) { const result = await response.json(); throw new Error(typeof result.detail === 'string' ? result.detail : Object.values(result).flat().join(' ')); }
      if (reload) { window.location.reload(); return; }
      setRevision(n => n + 1); setNotice('Cambios guardados.');
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }
  function add(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); void change('team/', 'POST', Object.fromEntries(new FormData(event.currentTarget)));
  }
  return <section className="panel"><h2>Equipo de {companyName}</h2><p>Propietario administra accesos; Contador puede importar y conciliar; Consulta solo puede leer.</p>
    {error && <p role="alert" className="error">{error}</p>}{notice && <p role="status">{notice}</p>}
    {!data && !error && <p role="status">Cargando equipo…</p>}
    {data?.can_manage && <><form className="toolbar" onSubmit={event => { event.preventDefault(); void change('name/', 'PATCH', Object.fromEntries(new FormData(event.currentTarget)), true); }}><label>Nombre de la empresa<input name="name" defaultValue={companyName} required maxLength={200} /></label><button disabled={busy}>Actualizar nombre</button></form>
      <form className="obligation-form" onSubmit={add}><label>Usuario ya registrado<input name="username" maxLength={150} required /></label><label>Rol<select name="role" defaultValue="viewer">{Object.entries(roles).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><p>Al añadirlo, le concedes acceso a los datos de esta empresa. No se envía una invitación por correo.</p><button disabled={busy}>Añadir al equipo</button></form></>}
    {data && <><div className="table-wrap"><table><thead><tr><th>Usuario</th><th>Rol y estado</th><th>Acciones</th></tr></thead><tbody>{data.results.map(member => <tr key={`${member.id}-${member.role}`}><td>{member.username}{member.id === data.my_membership_id ? ' (tú)' : ''}</td><td>{roles[member.role as keyof typeof roles]}{!member.active ? ' · cuenta inactiva' : ''}</td><td>{data.can_manage && <><form onSubmit={event => { event.preventDefault(); void change(`team/${member.id}/`, 'PATCH', Object.fromEntries(new FormData(event.currentTarget)), member.id === data.my_membership_id); }}><label>Nuevo rol de {member.username}<select name="role" defaultValue={member.role}>{Object.entries(roles).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><button disabled={busy}>Guardar rol</button></form><button className="secondary" disabled={busy} onClick={() => void change(`team/${member.id}/`, 'DELETE', undefined, member.id === data.my_membership_id)}>Retirar acceso</button></>}</td></tr>)}</tbody></table></div><div className="toolbar"><button className="secondary" disabled={!data.previous || busy} onClick={() => setPage(n => n - 1)}>Anterior</button><span>Página {page} · {data.count} integrantes</span><button className="secondary" disabled={!data.next || busy} onClick={() => setPage(n => n + 1)}>Siguiente</button></div></>}
    {data && <AuditHistory key={company} company={company} />}
  </section>;
}
