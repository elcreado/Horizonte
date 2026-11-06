import { useEffect, useRef, useState } from 'react';
import { readCompanyPreference, rememberCompany, resolveCompany } from './companySelection';

type Company = { id: number; name: string };
type CompanyState = {
  username: string | null;
  companies: Company[];
  company: string;
  status: 'loading' | 'ready' | 'error';
  error: string;
};
const browserStorage = () => window.localStorage;

export function useCompanySelection(user: string | null, load: (signal: AbortSignal) => Promise<Company[]>) {
  const [revision, setRevision] = useState(0);
  const [state, setState] = useState<CompanyState>({ username: null, companies: [], company: '', status: 'loading', error: '' });
  const currentUser = useRef(user);
  currentUser.current = user;

  useEffect(() => {
    const controller = new AbortController();
    setState({ username: user, companies: [], company: '', status: 'loading', error: '' });
    if (user) {
      load(controller.signal).then(companies => {
        if (controller.signal.aborted || currentUser.current !== user) return;
        const company = resolveCompany(companies, user, readCompanyPreference(browserStorage));
        rememberCompany(browserStorage, user, company);
        setState({ username: user, companies, company, status: 'ready', error: '' });
      }).catch(error => {
        if (controller.signal.aborted || currentUser.current !== user) return;
        setState({ username: user, companies: [], company: '', status: 'error', error: error instanceof Error ? error.message : 'No se pudieron cargar tus empresas.' });
      });
    }
    return () => controller.abort();
  }, [user, load, revision]);

  // Never expose the previous user's list while a new session is loading.
  const visible = state.username === user ? state : { username: user, companies: [], company: '', status: 'loading' as const, error: '' };
  function selectCompany(company: string) {
    if (!user || currentUser.current !== user || visible.status !== 'ready' || !visible.companies.some(item => String(item.id) === company)) return;
    rememberCompany(browserStorage, user, company);
    setState(previous => ({ ...previous, company }));
  }
  function addCompany(created: Company) {
    if (!user || currentUser.current !== user || visible.status !== 'ready') return;
    const company = String(created.id);
    rememberCompany(browserStorage, user, company);
    setState(previous => ({ ...previous, companies: [...previous.companies.filter(item => item.id !== created.id), created], company }));
  }
  return { ...visible, selectCompany, addCompany, retryCompanies: () => setRevision(value => value + 1) };
}
