import { useEffect, useRef, useState } from 'react';

type Suggestion = { status: string; category: string | null; examples: number; notice: string };

export function CategorySuggestion({ company, movement, disabled, onChoose }: {
  company: string; movement: number; disabled: boolean; onChoose: (category: string) => void;
}) {
  const [suggestion, setSuggestion] = useState<Suggestion | null>(null);
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const controller = useRef<AbortController | null>(null);
  useEffect(() => () => controller.current?.abort(), []);
  async function requestSuggestion() {
    controller.current?.abort();
    const current = new AbortController(); controller.current = current;
    setBusy(true); setSuggestion(null); setNotice('');
    try {
      const response = await fetch(`/api/companies/${company}/movements/${movement}/category-suggestion/`, { signal: current.signal });
      const result = await response.json();
      if (current.signal.aborted) return;
      if (response.status === 409) { setNotice(result.detail || 'Aún no hay suficientes correcciones revisadas.'); return; }
      if (!response.ok) throw new Error(result.detail || 'No se pudo consultar la sugerencia.');
      setSuggestion(result);
    } catch (error) {
      if (!current.signal.aborted) setNotice((error as Error).message);
    } finally {
      if (!current.signal.aborted) setBusy(false);
    }
  }
  return <div className="panel"><p>Consulta una sugerencia aprendida de correcciones manuales de esta empresa. Revisarla no cambia el movimiento.</p>
    <button type="button" className="secondary" disabled={disabled || busy} onClick={requestSuggestion}>{busy ? 'Consultando…' : 'Sugerir categoría'}</button>
    {notice && <p role="status">{notice}</p>}
    {suggestion && <div aria-live="polite"><p>{suggestion.notice} Entrenamiento: {suggestion.examples} descripciones distintas.</p>
      {suggestion.category ? <><p>Sugerencia: <strong>{suggestion.category}</strong>.</p><button type="button" disabled={disabled} onClick={() => { if (suggestion.category) onChoose(suggestion.category); }}>Seleccionar {suggestion.category}</button><p>Revisa la selección y pulsa Guardar categoría para aplicarla.</p></> : <p>El modelo se abstuvo: no hay evidencia suficiente para distinguir una categoría. Puedes clasificar manualmente.</p>}
    </div>}
  </div>;
}
