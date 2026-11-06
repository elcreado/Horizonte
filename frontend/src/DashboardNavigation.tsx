import { useEffect, useRef, useState } from 'react';
import { dashboardSections } from './dashboardSections';

const icons: Record<string, string> = {
  overview: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
  movements: 'M4 7h16m-4-4 4 4-4 4M20 17H4m4-4-4 4 4 4',
  obligations: 'M4 5h16v16H4z M8 3v4m8-4v4M4 11h16m-12 4h3m2 3h3',
  invoices: 'M6 3h9l4 4v14H6z M14 3v5h5M9 12h7m-7 4h7',
  forecasts: 'M3 3v18h18M6 16l5-6 4 3 6-8m-5 0h5v5',
  history: 'M4 20V10h4v10m4 0V4h4v16m4 0v-7',
  alerts: 'M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4',
  accounts: 'M3 6h18v15H3z M3 10h18m-6 5h3M6 3h12',
  sources: 'M12 3v12m-4-4 4 4 4-4M4 16v5h16v-5',
  rules: 'M4 6h16M4 12h16M4 18h16M8 3v6m8 0v6m-6 0v6',
};

export function DashboardNavigation({ sectionId }: { sectionId: string }) {
  const [open, setOpen] = useState(false);
  const toggle = useRef<HTMLButtonElement>(null);
  useEffect(() => setOpen(false), [sectionId]);
  const section = dashboardSections.find(item => item.id === sectionId);
  return <aside className="dashboard-sidebar" data-open={open} onKeyDown={event => {
    if (event.key === 'Escape' && open) { setOpen(false); toggle.current?.focus(); }
  }}>
    <button ref={toggle} className="mobile-nav-toggle secondary" aria-expanded={open} aria-controls="dashboard-navigation" onClick={() => setOpen(value => !value)}>
      <span><span aria-hidden="true">☰</span> {section?.label || 'Dashboard'}</span><span>{open ? 'Cerrar menú' : 'Cambiar sección'}</span>
    </button>
    <div id="dashboard-navigation" className="dashboard-navigation">
      <p className="sidebar-title">Tu espacio de trabajo</p>
      <nav aria-label="Secciones del dashboard">{['Operación', 'Análisis', 'Configuración'].map(group => <div className="sidebar-group" key={group}>
        <p>{group}</p>{dashboardSections.filter(item => item.group === group).map(item => <a key={item.id} href={item.id === 'overview' ? '#/dashboard' : `#/dashboard/${item.id}`} aria-current={sectionId === item.id ? 'page' : undefined} onClick={() => { setOpen(false); if (sectionId === item.id) toggle.current?.focus(); }}>
          <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"><path d={icons[item.id]} /></svg><span>{item.label}</span>
        </a>)}
      </div>)}</nav>
      <div className="sidebar-help"><strong>Tu negocio, al día</strong><p>Registra tus movimientos manualmente. Conectar un banco es opcional.</p><a href="#/dashboard/movements" onClick={() => setOpen(false)}>Registrar un movimiento →</a></div>
    </div>
  </aside>;
}
