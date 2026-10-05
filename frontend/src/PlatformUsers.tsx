import { useEffect, useState } from 'react';

type User = { id: number; username: string; email: string; is_active: boolean; is_staff: boolean; is_superuser: boolean; company_count: number };
type Page = { count: number; next: string | null; previous: string | null; results: User[] };

export function PlatformUsers() {
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Page | null>(null);
  const [error, setError] = useState('');
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController(); setData(null); setError('');
    fetch(`/api/platform/users/?page=${page}`, { signal: controller.signal }).then(async response => {
      if (!response.ok) throw new Error(response.status === 403 ? 'Tu sesión no tiene permisos de administración de plataforma.' : 'No se pudieron consultar los usuarios.');
      const result = await response.json();
      if (!controller.signal.aborted) setData(result);
    }).catch(error => { if (!controller.signal.aborted) setError(error.message); });
    return () => controller.abort();
  }, [page, revision]);
  return <main><h1>Administración de plataforma</h1><p>Consulta de cuentas y membresías. La creación, desactivación y cambio de privilegios todavía no están disponibles aquí.</p><button className="secondary" onClick={() => setRevision(value => value + 1)}>Actualizar</button>
    {error && <p className="error" role="alert">{error}</p>}
    {!data && !error && <p role="status">Cargando usuarios…</p>}
    {data && <><p>{data.count} cuentas registradas</p><div className="table-wrap"><table><thead><tr><th>Usuario</th><th>Correo</th><th>Activo</th><th>Staff</th><th>Superusuario</th><th>Membresías</th></tr></thead><tbody>{data.results.map(user => <tr key={user.id}><td>{user.username}</td><td>{user.email}</td><td>{user.is_active ? 'Sí' : 'No'}</td><td>{user.is_staff ? 'Sí' : 'No'}</td><td>{user.is_superuser ? 'Sí' : 'No'}</td><td>{user.company_count}</td></tr>)}</tbody></table></div><button disabled={!data.previous} onClick={() => setPage(value => value - 1)}>Anterior</button> <span>Página {page}</span> <button disabled={!data.next} onClick={() => setPage(value => value + 1)}>Siguiente</button></>}
  </main>;
}
