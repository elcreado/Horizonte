import React, { FormEvent, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './style.css';
import { ScreenBoundary } from './ScreenBoundary';
const History = React.lazy(() => import('./History').then(module => ({ default: module.History })));
import { ClassificationRules } from './ClassificationRules';
import { CreateCompany } from './CreateCompany';
import { Profile } from './Profile';
import { Coverage, CoverageData } from './Coverage';
import { AccountBalances } from './AccountBalances';
import { BankConnections } from './BankConnections';
import { LiquidityAlert, AlertData } from './LiquidityAlert';
import { AlertHistory } from './AlertHistory';
const ForecastPreview = React.lazy(() => import('./ForecastPreview').then(module => ({ default: module.ForecastPreview })));
import { Home } from './Home';
import { Register } from './Register';
import { Team } from './Team';
import { PasswordRecovery } from './PasswordRecovery';
const Invoices = React.lazy(() => import('./Invoices').then(module => ({ default: module.Invoices })));
const Obligations = React.lazy(() => import('./Obligations').then(module => ({ default: module.Obligations })));
const ObligationCalendar = React.lazy(() => import('./ObligationCalendar').then(module => ({ default: module.ObligationCalendar })));
import { Recurrences } from './Recurrences';
const Movements = React.lazy(() => import('./Movements').then(module => ({ default: module.Movements })));
const Merchants = React.lazy(() => import('./Merchants').then(module => ({ default: module.Merchants })));
import { ImportPanel } from './ImportPanel';
import { PlatformUsers } from './PlatformUsers';

const DashboardChart = React.lazy(() => import('./DashboardChart').then(module => ({ default: module.DashboardChart })));

type Company = { id: number; name: string };
type Dashboard = {
  liquidity_alert: AlertData;
  coverage: CoverageData;
  company: string; as_of: string; balance: string; receivable: string; payable: string;
  method: string; notice: string; first_deficit: string | null; minimum_balance: string;
  overdue_count: number; points: { date: string; balance: string }[];
  obligations: { id: number; description: string; due_date: string; direction: string; amount: string }[];
  transactions: { id: number; description: string; date: string; category: string; amount: string }[];
};
const money = (value: string | number) => new Intl.NumberFormat('es-CO', {
  style: 'currency', currency: 'COP', maximumFractionDigits: 0,
}).format(Number(value));
const dateLabel = (value: string) => new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'short' }).format(new Date(`${value}T12:00:00`));

async function api<T>(path: string, body?: object, signal?: AbortSignal): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (body) {
    const response = await fetch('/api/auth/csrf/');
    const token = await response.json();
    headers['X-CSRFToken'] = token.csrfToken;
  }
  const response = await fetch(`/api${path}`, {
    method: body ? 'POST' : 'GET', headers, body: body ? JSON.stringify(body) : undefined, signal,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'No se pudo completar la solicitud. Comprueba tu conexión y vuelve a intentarlo.');
  }
  return response.status === 204 ? undefined as T : response.json();
}

function App() {
  const [route, setRoute] = useState(window.location.hash || '#/');
  useEffect(() => {
    const onRoute = () => { setRoute(window.location.hash || '#/'); window.scrollTo(0, 0); };
    window.addEventListener('hashchange', onRoute);
    return () => window.removeEventListener('hashchange', onRoute);
  }, []);
  const [user, setUser] = useState<string | null>(null);
  const [platformAdmin, setPlatformAdmin] = useState(false);
  useEffect(() => {
    setPlatformAdmin(false);
    if (!user) return;
    const controller = new AbortController();
    api<{ platform_admin: boolean }>('/auth/me/', undefined, controller.signal)
      .then(value => { if (!controller.signal.aborted) setPlatformAdmin(value.platform_admin); }).catch(() => {});
    return () => controller.abort();
  }, [user]);
  const [checking, setChecking] = useState(true);
  const [sessionError, setSessionError] = useState('');
  const [sessionRevision, setSessionRevision] = useState(0);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [company, setCompany] = useState('');
  const [financialRevision, setFinancialRevision] = useState(0);
  const [horizon, setHorizon] = useState(30);
  const [data, setData] = useState<Dashboard | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    setChecking(true); setSessionError('');
    async function checkSession() {
      try {
        const response = await fetch('/api/auth/me/', { signal: controller.signal });
        if (response.status === 403) { if (!controller.signal.aborted) setUser(null); return; }
        if (!response.ok) throw new Error('No se pudo comprobar la sesión. El servicio puede estar reactivándose.');
        const result = await response.json();
        if (typeof result.username !== 'string') throw new Error('Respuesta de sesión inválida. Reintenta la conexión.');
        if (!controller.signal.aborted) setUser(result.username);
      } catch (error) {
        if (!controller.signal.aborted) setSessionError(error instanceof Error ? error.message : 'No se pudo comprobar la sesión.');
      } finally { if (!controller.signal.aborted) setChecking(false); }
    }
    void checkSession();
    return () => controller.abort();
  }, [sessionRevision]);
  useEffect(() => {
    if (!user) return;
    const controller = new AbortController();
    api<Company[]>('/companies/', undefined, controller.signal).then(value => {
      setCompanies(value); setCompany(value[0] ? String(value[0].id) : '');
    }).catch(e => { if (e.name !== 'AbortError') setError(e.message); });
    return () => controller.abort();
  }, [user]);
  useEffect(() => {
    if (!company || !user) return;
    const controller = new AbortController();
    setData(null); setError('');
    api<Dashboard>(`/companies/${company}/dashboard/?horizon=${horizon}`, undefined, controller.signal)
      .then(setData).catch(e => { if (e.name !== 'AbortError') setError(e.message); });
    return () => controller.abort();
  }, [company, horizon, user, financialRevision]);

  async function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError('');
    const form = new FormData(event.currentTarget);
    try {
      const result = await api<{ username: string }>('/auth/login/', { username: form.get('username'), password: form.get('password') });
      setUser(result.username);
      window.location.hash = '/dashboard';
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  }
  async function signOut() {
    try {
      await api('/auth/logout/', {});
      setUser(null); setData(null); setCompanies([]); setCompany(''); setError('');
      window.location.hash = '/';
    } catch (e) { setError((e as Error).message); }
  }
  if (route === '#/recover-password' || route.startsWith('#/reset-password?')) return <PasswordRecovery key={route} route={route} />;
  if (route === '#/register' && !user) return <Register onRegistered={username => { setUser(username); window.location.hash = '/dashboard'; }} />;
  if (route === '#/' || !['#/login', '#/dashboard', '#/register', '#/team', '#/account', '#/platform'].includes(route)) return <Home authenticated={Boolean(user)} />;
  if (checking) return <main><p role="status">Cargando sesión…</p></main>;
  if (sessionError) return <main className="login"><a href="#/">Volver al inicio</a><h1>No se pudo comprobar tu sesión</h1><p role="alert">{sessionError}</p><button onClick={() => setSessionRevision(value => value + 1)}>Reintentar conexión</button></main>;
  if (!user) return <main className="login"><a className="brand" href="#/">◈ HORIZONTE</a><p className="back-home"><a href="#/">← Volver al inicio</a></p>
    <h1>Tu caja, con perspectiva.</h1><p>Explora la liquidez de tu empresa y anticipa tus próximos compromisos.</p>
    <form onSubmit={signIn}><h2>Entrar a la aplicación</h2>
      <label>Usuario<input name="username" autoComplete="username" required defaultValue="demo" /></label>
      <label>Contraseña<input name="password" type="password" autoComplete="current-password" required /></label>
      {error && <p role="alert" className="error">{error}</p>}
      <button disabled={busy}>{busy ? 'Ingresando…' : 'Ingresar'}</button>
      <p><a href="#/recover-password">Olvidé mi contraseña</a></p>
      <p>¿No tienes cuenta? <a href="#/register">Crear cuenta y empresa</a></p>
      <small>Entorno académico · utiliza la contraseña configurada con DEMO_PASSWORD.</small>
    </form></main>;
  if (route === '#/account') return <Profile />;
  if (route === '#/platform') return <><header><a href="#/dashboard">Volver al dashboard</a><button onClick={signOut}>Cerrar sesión</button></header><PlatformUsers key={user} /></>;
  if (route === '#/team') return <><header><a className="brand" href="#/">◈ HORIZONTE</a><a href="#/dashboard">Volver al dashboard</a><button className="secondary" onClick={signOut}>Cerrar sesión</button></header><main><h1>Empresa y equipo</h1><CreateCompany onCreated={created => { setCompanies(items => [...items, created]); setCompany(String(created.id)); }} /><label>Empresa<select value={company} onChange={e => setCompany(e.target.value)}>{companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label>{company ? <Team key={company} company={company} companyName={companies.find(c => String(c.id) === company)?.name || ''} /> : <p>No tienes empresas disponibles.</p>}</main></>;
  return <><header><a className="brand" href="#/">◈ HORIZONTE</a><a href="#/">Inicio</a><a href="#/team">Empresa y equipo</a><a href="#/account">Mi cuenta</a>{platformAdmin && <a href="#/platform">Administración</a>}<span>Inteligencia de liquidez</span><button className="secondary" onClick={signOut}>Cerrar sesión</button></header>
    <main><div className="toolbar"><div><p className="eyebrow">PANORAMA FINANCIERO</p><h1>Anticipa lo que viene.</h1></div>
      <label>Empresa<select value={company} onChange={e => setCompany(e.target.value)}>{companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label></div>
      {error && <p role="alert" className="error">{error}</p>}
      {!company && !error && <p role="status">No tienes empresas disponibles. <a href="#/team">Crea tu empresa</a> o solicita acceso a su propietario.</p>}
      {company && !data && !error && <p role="status">Cargando panorama…</p>}
      {company && <AccountBalances key={company} company={company} revision={financialRevision} onChanged={() => setFinancialRevision(n => n + 1)} />}
      {company && <BankConnections key={company} company={company} onChanged={() => setFinancialRevision(n => n + 1)} />}
      {company && <ImportPanel key={company} company={company} revision={financialRevision} onChanged={() => setFinancialRevision(n => n + 1)} />}
      {data && <><LiquidityAlert key={company} company={company} alert={data.liquidity_alert} onChanged={() => setFinancialRevision(n => n + 1)} /><Coverage data={data.coverage} /><div className="notice"><strong>ESCENARIO DE OBLIGACIONES</strong> {data.notice} Corte: {dateLabel(data.as_of)}.</div>
        <section className="cards" aria-label="Resumen financiero">
          {[['Saldo disponible', data.balance], [`Por cobrar · ${horizon} días`, data.receivable], [`Por pagar · ${horizon} días`, data.payable]].map(([label, value]) => <article key={label}><p>{label}</p><strong>{money(value)}</strong><small>COP · pesos colombianos</small></article>)}
          <article className={data.first_deficit ? 'risk' : ''}><p>Escenario de liquidez</p><strong>{data.first_deficit ? `Déficit: ${dateLabel(data.first_deficit)}` : 'Sin déficit previsto'}</strong><small>Según las obligaciones registradas</small></article>
        </section>
        <section className="panel"><div className="toolbar"><div><h2>La trayectoria de tu caja</h2><p>{data.method}</p></div><div className="periods" aria-label="Horizonte">{[30, 60, 90].map(n => <button className={horizon === n ? 'active' : 'secondary'} aria-pressed={horizon === n} key={n} onClick={() => setHorizon(n)}>{n} días</button>)}</div></div>
          <div className="chart" role="img" aria-label={`Saldo mínimo proyectado ${money(data.minimum_balance)}. ${data.first_deficit ? `Primer déficit ${data.first_deficit}` : 'Sin déficit en el horizonte'}`}>
            <React.Suspense fallback={<p role="status">Cargando gráfico…</p>}><DashboardChart points={data.points} dateLabel={dateLabel} money={money} /></React.Suspense>
          </div><p className="footnote">Saldo mínimo: {money(data.minimum_balance)}. Este escenario no equivale a P50 ni tiene intervalos de confianza.</p>
        </section>
        {data.first_deficit && <aside className="warning"><strong>Revisa tus compromisos antes del {dateLabel(data.first_deficit)}.</strong><p>Las obligaciones registradas llevan el saldo por debajo de cero. Revisa el calendario de cobros y pagos que se muestra abajo.</p></aside>}
        {data.overdue_count > 0 && <p role="status">Hay {data.overdue_count} obligaciones vencidas o con vencimiento en la fecha de corte. Requieren una nueva fecha estimada; no se incluyen como futuros cobros o pagos.</p>}
        <div className="columns"><section className="panel"><h2>Próximos compromisos</h2><p>Fechas y valores pendientes del período</p><div className="table-wrap"><table><thead><tr><th>Concepto</th><th>Fecha</th><th>Valor</th></tr></thead><tbody>{data.obligations.map(o => <tr key={o.id}><td>{o.description}<small>{o.direction === 'in' ? 'Por cobrar' : 'Por pagar'}</small></td><td>{dateLabel(o.due_date)}</td><td className={o.direction === 'in' ? 'positive' : ''}>{o.direction === 'in' ? '+' : '−'}{money(o.amount)}</td></tr>)}</tbody></table>{!data.obligations.length && <p>No hay obligaciones en este período.</p>}</div></section>
</div>
      </>}
      {company && <AlertHistory key={company} company={company} horizon={horizon} />}
      {company && <ForecastPreview key={company} company={company} horizon={horizon} revision={financialRevision} />}
      {company && <History key={company} company={company} refresh={financialRevision} />}
      {company && <Invoices key={company} company={company} onChange={() => setFinancialRevision(n => n + 1)} />}
      {company && <Obligations key={company} company={company} refresh={financialRevision} onChange={() => setFinancialRevision(n => n + 1)} />}
      {company && <ObligationCalendar key={company} company={company} refresh={financialRevision} />}
      {company && <Movements key={company} company={company} refresh={financialRevision} onChanged={() => setFinancialRevision(n => n + 1)} />}
      {company && <Merchants key={company} company={company} />}
      {company && <ClassificationRules key={company} company={company} />}
      {company && <Recurrences key={company} company={company} horizon={horizon} onChanged={() => setFinancialRevision(n => n + 1)} />}
      <footer>Horizonte · Prototipo académico v0.1 · Los pronósticos requieren revisión</footer>
    </main></>;
}

createRoot(document.getElementById('root')!).render(<React.StrictMode><ScreenBoundary><React.Suspense fallback={<main><p role="status">Cargando pantalla…</p></main>}><App /></React.Suspense></ScreenBoundary></React.StrictMode>);
