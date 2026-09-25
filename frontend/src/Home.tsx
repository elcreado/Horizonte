type HomeProps = { authenticated: boolean };

export function Home({ authenticated }: HomeProps) {
  return <>
    <header className="public-header">
      <a className="brand" href="#/">◈ HORIZONTE</a>
      <nav aria-label="Navegación principal"><a href="#/login">{authenticated ? 'Mi cuenta' : 'Iniciar sesión'}</a><a className="button-link" href={authenticated ? '#/dashboard' : '#/login'}>{authenticated ? 'Ir al dashboard' : 'Entrar a Horizonte'} →</a></nav>
    </header>
    <main className="home">
      <section className="home-hero">
        <div><p className="eyebrow">PARA QUIENES HACEN CRECER SU NEGOCIO</p>
          <h1>El futuro de tu caja,<br /><em>más claro desde hoy.</em></h1>
          <p className="hero-copy">Pon tus cobros y pagos en perspectiva. Conoce tus próximos compromisos y descubre cuándo podrían superar el dinero disponible de tu empresa.</p>
          <a className="button-link" href={authenticated ? '#/dashboard' : '#/login'}>{authenticated ? 'Ver mi panorama' : 'Iniciar sesión'} <span aria-hidden="true">↗</span></a>
          {!authenticated && <p><a href="#/register">Crear una cuenta y registrar mi empresa</a></p>}
          <p className="home-caption">Puedes conocer Horizonte sin una cuenta. Tu información financiera requiere iniciar sesión.</p>
        </div>
        <div className="home-preview" aria-label="Ejemplo ilustrativo, no son datos de una empresa">
          <div className="preview-heading"><span>UNA MIRADA HACIA ADELANTE</span><span className="example-badge">Ejemplo</span></div>
          <p>Tu próximo mes, en perspectiva</p>
          <div className="preview-steps"><div><span>01</span><strong>Dinero disponible</strong><small>El punto de partida</small></div><div><span>02</span><strong>Cobros y pagos</strong><small>Lo que viene en el calendario</small></div><div><span>03</span><strong>Escenario de caja</strong><small>Los días que merecen atención</small></div></div>
          <div className="preview-note">↗ Anticipar tus compromisos empieza por verlos juntos.</div>
        </div>
      </section>
      <section className="home-features" aria-labelledby="features-title"><p className="eyebrow">MENOS INCERTIDUMBRE, MÁS CONTEXTO</p><h2 id="features-title">Tres preguntas. Un panorama.</h2>
        <div className="feature-grid"><article><span>01 / DISPONIBILIDAD</span><h3>¿Con cuánto cuento?</h3><p>Consulta el saldo disponible y su fecha de corte para entender desde dónde parte tu escenario.</p></article><article><span>02 / COMPROMISOS</span><h3>¿Qué viene después?</h3><p>Revisa las cuentas por cobrar y pagar junto con sus fechas y valores pendientes.</p></article><article><span>03 / ANTICIPACIÓN</span><h3>¿Cuándo debo prestar atención?</h3><p>Explora escenarios a 30, 60 y 90 días e identifica cuándo el saldo podría quedar por debajo de cero.</p></article></div>
      </section>
      <section className="home-scope"><div><p className="eyebrow">UN PROYECTO EN CONSTRUCCIÓN</p><h2>Conoce la primera versión.</h2></div><p>Esta versión académica utiliza datos sintéticos y escenarios basados en obligaciones. Todavía no conecta bancos reales ni genera predicciones estadísticas. Horizonte no realiza pagos ni transferencias.</p></section>
      <footer>Horizonte · Inteligencia de liquidez para microempresas · Prototipo académico</footer>
    </main>
  </>;
}
