import { Component, type ReactNode } from 'react';

export class ScreenBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  render() {
    if (this.state.failed) return <main><h1>No se pudo abrir la pantalla</h1><p>Comprueba tu conexión y vuelve a cargar la aplicación.</p><button onClick={() => window.location.reload()}>Volver a cargar</button></main>;
    return this.props.children;
  }
}
