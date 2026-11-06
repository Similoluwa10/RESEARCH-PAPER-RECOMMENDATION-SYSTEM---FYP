export interface AuthUser {
  id: string;
  email: string;
  name: string;
  role: string;
}

export interface AuthSession {
  accessToken: string;
  tokenType: string;
  user: AuthUser;
}

const SESSION_KEY = 'paperhub_session';

export function getStoredSession(): AuthSession | null {
  if (typeof window === 'undefined') return null;

  const raw = window.localStorage.getItem(SESSION_KEY);
  if (!raw) return null;

  try {
    return JSON.parse(raw) as AuthSession;
  } catch {
    window.localStorage.removeItem(SESSION_KEY);
    return null;
  }
}

export function setStoredSession(session: AuthSession): void {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function clearStoredSession(): void {
  if (typeof window === 'undefined') return;
  window.localStorage.removeItem(SESSION_KEY);
}

export function updateStoredSessionUser(updates: Partial<AuthUser>): AuthSession | null {
  if (typeof window === 'undefined') return null;

  const current = getStoredSession();
  if (!current) return null;

  const next: AuthSession = {
    ...current,
    user: {
      ...current.user,
      ...updates,
    },
  };

  setStoredSession(next);
  return next;
}

export function getAuthHeaderValue(session: AuthSession | null): string | undefined {
  if (!session?.accessToken) return undefined;
  const type = session.tokenType || 'bearer';
  return `${type} ${session.accessToken}`;
}
