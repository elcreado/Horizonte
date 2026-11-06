// Manual integration fixture, served by Vite only; not imported by the application.
import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { useCompanySelection } from '../src/useCompanySelection';

type Company = { id: number; name: string };
type Pending = { id: number; resolve: (companies: Company[]) => void; reject: (reason: Error) => void };
let nextId = 0;
let pending: Pending[] = [];
const load = (_signal: AbortSignal) => new Promise<Company[]>((resolve, reject) => {
  // Deliberately ignore cancellation: the hook must reject obsolete responses itself.
  pending.push({ id: ++nextId, resolve, reject });
});

function Harness() {
  const [user, setUser] = useState<string | null>('fixture-a');
  const state = useCompanySelection(user, load);
  const [requests, setRequests] = useState<Pending[]>([]);
  function complete(request: Pending, result: 'ok' | 'empty' | 'error') {
    pending = pending.filter(item => item.id !== request.id);
    setRequests([...pending]);
    if (result === 'error') request.reject(new Error('Fallo sintético de empresas'));
    else request.resolve(result === 'empty' ? [] : [{ id: 701, name: 'Empresa A' }, { id: 702, name: 'Empresa B' }]);
  }
  return <main><h1>Prueba aislada de selección de empresa</h1>
    <p>Usuario: {user || 'sin sesión'}</p><p>Estado: {state.status}</p>
    <p>Empresa activa: {state.company || 'ninguna'}</p><p>Empresas visibles: {state.companies.map(item => item.name).join(', ') || 'ninguna'}</p>
    <p role="alert">{state.error}</p>
    <button onClick={() => setUser('fixture-a')}>Usuario A</button>
    <button onClick={() => setUser('fixture-b')}>Usuario B</button>
    <button onClick={() => setUser(null)}>Sin sesión</button>
    <button onClick={state.retryCompanies}>Reintentar</button>
    <button onClick={() => state.selectCompany('702')}>Seleccionar B</button>
    <button onClick={() => state.selectCompany('999')}>Intentar empresa ajena</button>
    <button onClick={() => state.addCompany({ id: 703, name: 'Empresa creada' })}>Simular creación</button>
    <button onClick={() => setRequests([...pending])}>Ver solicitudes pendientes</button>
    {requests.map(request => <section key={request.id}><h2>Solicitud {request.id}</h2>
      <button onClick={() => complete(request, 'ok')}>Completar {request.id}</button>
      <button onClick={() => complete(request, 'empty')}>Vaciar {request.id}</button>
      <button onClick={() => complete(request, 'error')}>Fallar {request.id}</button>
    </section>)}
  </main>;
}
createRoot(document.getElementById('root')!).render(<Harness />);
