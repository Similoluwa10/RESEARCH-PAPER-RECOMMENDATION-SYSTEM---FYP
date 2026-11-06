const GOOGLE_SCRIPT_ID = 'google-identity-services';
const GOOGLE_SCRIPT_SRC = 'https://accounts.google.com/gsi/client';

function loadGoogleScript(): Promise<void> {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('Google sign-in is only available in browser'));
  }

  if (window.google?.accounts?.id) {
    return Promise.resolve();
  }

  const existing = document.getElementById(GOOGLE_SCRIPT_ID) as HTMLScriptElement | null;
  if (existing) {
    return new Promise((resolve, reject) => {
      existing.addEventListener('load', () => resolve(), { once: true });
      existing.addEventListener('error', () => reject(new Error('Failed to load Google script')), {
        once: true,
      });
    });
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.id = GOOGLE_SCRIPT_ID;
    script.src = GOOGLE_SCRIPT_SRC;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Failed to load Google script'));
    document.head.appendChild(script);
  });
}

export async function getGoogleIdToken(): Promise<string> {
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
  if (!clientId) {
    throw new Error('NEXT_PUBLIC_GOOGLE_CLIENT_ID is not configured');
  }

  await loadGoogleScript();

  return new Promise((resolve, reject) => {
    if (!window.google?.accounts?.id) {
      reject(new Error('Google Identity SDK unavailable'));
      return;
    }

    const timeout = window.setTimeout(() => {
      reject(new Error('Google sign-in timed out'));
    }, 30000);

    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: (response) => {
        window.clearTimeout(timeout);
        if (!response?.credential) {
          reject(new Error('Google credential was not returned'));
          return;
        }
        resolve(response.credential);
      },
    });

    window.google.accounts.id.prompt((notification) => {
      if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
        window.clearTimeout(timeout);
        reject(new Error('Google sign-in was cancelled or unavailable'));
      }
    });
  });
}
