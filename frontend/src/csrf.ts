export async function getCsrf(): Promise<{ csrfToken: string }> {
  const response = await fetch('/api/auth/csrf/');
  if (!response.ok) throw new Error('No se pudo verificar la sesión. Reintenta cuando el servidor esté disponible.');
  const value = await response.json().catch(() => { throw new Error('Respuesta de sesión inválida. Recarga e intenta de nuevo.'); });
  if (!value || typeof value.csrfToken !== 'string' || !value.csrfToken.trim()) {
    throw new Error('Respuesta de sesión inválida. Recarga e intenta de nuevo.');
  }
  return { csrfToken: value.csrfToken };
}
