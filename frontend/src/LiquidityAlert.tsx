import { FormEvent, useEffect, useState } from 'react';
export type AlertData = { threshold: string; currently_below: boolean; first_below: string | null; projected_days_below: number; shortfall_at_minimum: string };
export function LiquidityAlert({ company, alert, onChanged }: { company: string; alert: AlertData; onChanged: () => void }) {
  const [canEdit, setCanEdit] = useState(false); const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    fetch(`/api/companies/${company}/liquidity-threshold/`, { signal: controller.signal }).then(async response => { if (!response.ok) throw new Error('No se pudo consultar el umbral.'); setCanEdit((await response.json()).can_edit); }).catch(e => { if (!controller.signal.aborted) setError(e.message); });
    return () => controller.abort();
  }, [company]);
  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const body = Object.fromEntries(new FormData(event.currentTarget)); setBusy(true); setError('');
    try {
      const csrf = await (await fetch('/api/auth/csrf/')).json();
      const response = await fetch(`/api/companies/${company}/liquidity-threshold/`, { method: 'PATCH', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf.csrfToken }, body: JSON.stringify(body) });
      const result = await response.json(); if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : Object.values(result).flat().join(' ')); onChanged();
    } catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  return <section className={alert.first_below ? 'panel warning' : 'panel'}><h2>Umbral de liquidez</h2><p>Saldo mínimo deseado: {alert.threshold} COP.</p>{alert.first_below ? <p role="status">{alert.currently_below ? 'El saldo al corte ya está por debajo del umbral.' : `Primera fecha prevista por debajo: ${alert.first_below}.`} {alert.projected_days_below} días futuros por debajo. Diferencia máxima respecto al mínimo deseado: {alert.shortfall_at_minimum} COP.</p> : <p>El escenario no baja del umbral en este horizonte.</p>}<p>Se calcula con el saldo declarado y las obligaciones registradas; no representa una probabilidad de riesgo.</p>{error && <p className="error" role="alert">{error}</p>}{canEdit && <form onSubmit={save}><label>Nuevo umbral COP<input name="threshold" type="number" min="0" step="0.01" required defaultValue={alert.threshold} /></label><button disabled={busy}>Guardar umbral</button></form>}</section>;
}
