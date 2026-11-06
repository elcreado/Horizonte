type CompanyId = { id: number };
type Preference = { username: string; companyId: string };
type PreferenceStorage = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>;

const preferenceKey = 'horizonte.active-company.v1';

// Storage is optional: browser privacy settings can even block its getter.
export function readCompanyPreference(storage: () => PreferenceStorage): Preference | null {
  try {
    const value: unknown = JSON.parse(storage().getItem(preferenceKey) || 'null');
    if (!value || typeof value !== 'object') return null;
    const preference = value as Partial<Preference>;
    return typeof preference.username === 'string' && typeof preference.companyId === 'string'
      ? { username: preference.username, companyId: preference.companyId } : null;
  } catch { return null; }
}

export function resolveCompany(companies: readonly CompanyId[], username: string, preference: Preference | null): string {
  if (preference?.username === username && companies.some(company => String(company.id) === preference.companyId)) {
    return preference.companyId;
  }
  return companies.length ? String(companies[0].id) : '';
}

export function rememberCompany(storage: () => PreferenceStorage, username: string, companyId: string): void {
  try {
    if (companyId) storage().setItem(preferenceKey, JSON.stringify({ username, companyId }));
    else storage().removeItem(preferenceKey);
  } catch { /* The current in-memory choice still works without persistence. */ }
}

export function forgetCompany(storage: () => PreferenceStorage): void {
  try { storage().removeItem(preferenceKey); } catch { /* Storage is optional. */ }
}
