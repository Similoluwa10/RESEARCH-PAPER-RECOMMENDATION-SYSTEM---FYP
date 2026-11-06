import { AuthSession, AuthUser, getAuthHeaderValue } from '@/lib/auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1';

interface ApiErrorPayload {
  detail?: string | { msg?: string }[];
}

interface TokenResponse {
  access_token: string;
  token_type: string;
}

interface MessageResponse {
  message: string;
  reset_url?: string | null;
}

interface ProfileUpdatePayload {
  email?: string;
  name?: string;
  preferred_categories?: string[];
}

interface RecommendationPaper {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  year: number | null;
  category: string;
}

interface PaperDetailResponse {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  year: number | null;
  venue: string | null;
  keywords: string[];
  doi: string | null;
  url: string | null;
  category: string;
  source: string;
}

interface Explanation {
  summary: string;
}

interface RecommendationItem {
  paper: RecommendationPaper;
  score: number;
  explanation?: Explanation;
}

interface RecommendationResponse {
  recommendations: RecommendationItem[];
  total: number;
}

interface SavedPaperListResponse {
  papers: RecommendationPaper[];
  total: number;
  page: number;
  page_size: number;
}

export interface UIPaper {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  publicationDate: string;
  citations: number;
  likes: number;
  category: string;
  explanation?: Explanation;
}

export interface UIPaperDetail extends UIPaper {
  venue: string;
  keywords: string[];
  doi: string;
  url: string;
  source: string;
}

function toErrorMessage(payload: ApiErrorPayload | null, fallback: string): string {
  if (!payload?.detail) return fallback;
  if (typeof payload.detail === 'string') return payload.detail;
  if (Array.isArray(payload.detail) && payload.detail.length > 0) {
    return payload.detail[0]?.msg ?? fallback;
  }
  return fallback;
}

async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  session?: AuthSession | null,
): Promise<T> {
  const headers = new Headers(options.headers ?? {});

  if (!headers.has('Content-Type') && options.body) {
    headers.set('Content-Type', 'application/json');
  }

  const authHeader = getAuthHeaderValue(session ?? null);
  if (authHeader) {
    headers.set('Authorization', authHeader);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let payload: ApiErrorPayload | null = null;
    try {
      payload = (await response.json()) as ApiErrorPayload;
    } catch {
      payload = null;
    }
    throw new Error(toErrorMessage(payload, 'Request failed'));
  }

  if (response.status === 204) {
    return null as T;
  }

  return (await response.json()) as T;
}

export async function registerUser(name: string, email: string, password: string): Promise<void> {
  await apiRequest('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ name, email, password }),
  });
}

export async function loginWithPassword(email: string, password: string): Promise<TokenResponse> {
  const body = new URLSearchParams({
    username: email,
    password,
  });

  return apiRequest<TokenResponse>('/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: body.toString(),
  });
}

export async function loginWithGoogleToken(idToken: string): Promise<TokenResponse> {
  return apiRequest<TokenResponse>('/auth/google/login', {
    method: 'POST',
    body: JSON.stringify({ id_token: idToken }),
  });
}

export async function getCurrentUser(accessToken: string, tokenType = 'bearer'): Promise<AuthUser> {
  const payload = await apiRequest<AuthUser>(
    '/auth/me',
    { method: 'GET' },
    { accessToken, tokenType, user: { id: '', email: '', name: '', role: '' } },
  );
  return payload;
}

export async function requestPasswordReset(email: string): Promise<string> {
  const payload = await apiRequest<MessageResponse>('/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });

  return payload.message;
}

export async function requestPasswordResetWithDetails(
  email: string,
): Promise<{ message: string; resetUrl?: string | null }> {
  const payload = await apiRequest<MessageResponse>('/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email }),
  });

  return {
    message: payload.message,
    resetUrl: payload.reset_url,
  };
}

export async function updateCurrentUserProfile(
  session: AuthSession,
  updates: ProfileUpdatePayload,
): Promise<AuthUser> {
  return apiRequest<AuthUser>(
    '/auth/me',
    {
      method: 'PATCH',
      body: JSON.stringify(updates),
    },
    session,
  );
}

export async function resetPassword(token: string, newPassword: string): Promise<string> {
  const payload = await apiRequest<MessageResponse>('/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify({ token, new_password: newPassword }),
  });

  return payload.message;
}

export async function fetchRecommendations(queryText: string): Promise<UIPaper[]> {
  const requestPayload: Record<string, unknown> = {
    query_text: queryText,
    include_explanation: true,
  };

  const payload = await apiRequest<RecommendationResponse>('/recommendations/', {
    method: 'POST',
    body: JSON.stringify(requestPayload),
  });

  return payload.recommendations.map((item) => toUIPaper(item.paper, item.explanation));
}

export async function fetchPersonalizedRecommendations(session: AuthSession): Promise<UIPaper[]> {
  const payload = await apiRequest<RecommendationResponse>(
    '/recommendations/personalized',
    { method: 'GET' },
    session,
  );
  return payload.recommendations.map((item) => toUIPaper(item.paper));
}

export async function savePaper(paperId: string, session: AuthSession): Promise<void> {
  await apiRequest(`/papers/${paperId}/save`, { method: 'POST' }, session);
}

export async function unsavePaper(paperId: string, session: AuthSession): Promise<void> {
  await apiRequest(`/papers/${paperId}/save`, { method: 'DELETE' }, session);
}

export async function listSavedPapers(session: AuthSession): Promise<UIPaper[]> {
  const payload = await apiRequest<SavedPaperListResponse>(
    '/papers/saved?page=1&page_size=50',
    { method: 'GET' },
    session,
  );

  return payload.papers.map((paper) => toUIPaper(paper));
}

export async function fetchPaperById(paperId: string): Promise<UIPaperDetail> {
  const payload = await apiRequest<PaperDetailResponse>(`/papers/${paperId}`, {
    method: 'GET',
  });

  return toUIPaperDetail(payload);
}

export function toUIPaper(paper: RecommendationPaper, explanation?: Explanation): UIPaper {
  return {
    id: paper.id,
    title: paper.title,
    authors: paper.authors,
    abstract: paper.abstract,
    publicationDate: paper.year ? `${paper.year}` : 'N/A',
    citations: 0,
    likes: 0,
    category: paper.category || 'Other',
    explanation,
  };
}

export function toUIPaperDetail(paper: PaperDetailResponse): UIPaperDetail {
  return {
    id: paper.id,
    title: paper.title,
    authors: paper.authors,
    abstract: paper.abstract,
    publicationDate: paper.year ? `${paper.year}` : 'N/A',
    citations: 0,
    likes: 0,
    category: paper.category || 'Other',
    venue: paper.venue || 'N/A',
    keywords: paper.keywords ?? [],
    doi: paper.doi || 'N/A',
    url: paper.url || '',
    source: paper.source || 'Unknown',
  };
}
