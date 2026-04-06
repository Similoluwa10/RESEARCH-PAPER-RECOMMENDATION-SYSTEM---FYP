'use client';

import { useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import SearchBar from '@/components/SearchBar';
import PaperGrid from '@/components/PaperGrid';
import { Sparkles } from 'lucide-react';
import { fetchRecommendations, savePaper, UIPaper } from '@/lib/api';
import { AuthSession, clearStoredSession, getStoredSession } from '@/lib/auth';

const RECOMMENDATION_STATE_KEY = 'recommendation_page_state_v1';
const INITIAL_VISIBLE_PAPERS = 9;
const VISIBLE_PAPERS_STEP = 9;

interface RecommendationPageState {
  searchQuery: string;
  generatedPapers: UIPaper[];
  hasGenerated: boolean;
}

export default function RecommendationPage() {
  const router = useRouter();
  const [session, setSession] = useState<AuthSession | null>(null);
  const [isStateHydrated, setIsStateHydrated] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [generatedPapers, setGeneratedPapers] = useState<UIPaper[]>([]);
  const [visibleCount, setVisibleCount] = useState(INITIAL_VISIBLE_PAPERS);
  const [hasGenerated, setHasGenerated] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const loadMoreRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setSession(getStoredSession());

    try {
      const raw = window.sessionStorage.getItem(RECOMMENDATION_STATE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as RecommendationPageState;
        setSearchQuery(parsed.searchQuery ?? '');
        setGeneratedPapers(Array.isArray(parsed.generatedPapers) ? parsed.generatedPapers : []);
        setHasGenerated(Boolean(parsed.hasGenerated));
      }
    } catch {
      window.sessionStorage.removeItem(RECOMMENDATION_STATE_KEY);
    } finally {
      setIsStateHydrated(true);
    }
  }, []);

  useEffect(() => {
    if (!isStateHydrated) {
      return;
    }

    const snapshot: RecommendationPageState = {
      searchQuery,
      generatedPapers,
      hasGenerated,
    };
    window.sessionStorage.setItem(RECOMMENDATION_STATE_KEY, JSON.stringify(snapshot));
  }, [isStateHydrated, searchQuery, generatedPapers, hasGenerated]);

  useEffect(() => {
    if (!hasGenerated) {
      setVisibleCount(INITIAL_VISIBLE_PAPERS);
      return;
    }

    setVisibleCount((prev) => {
      const nextBase = Math.max(prev, INITIAL_VISIBLE_PAPERS);
      return Math.min(nextBase, generatedPapers.length || INITIAL_VISIBLE_PAPERS);
    });
  }, [generatedPapers, hasGenerated]);

  const visiblePapers = useMemo(
    () => generatedPapers.slice(0, visibleCount),
    [generatedPapers, visibleCount],
  );

  const hasMorePapers = visibleCount < generatedPapers.length;

  useEffect(() => {
    if (!hasGenerated || isGenerating || !hasMorePapers || !loadMoreRef.current) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (!entries[0]?.isIntersecting) {
          return;
        }

        setVisibleCount((prev) => Math.min(prev + VISIBLE_PAPERS_STEP, generatedPapers.length));
      },
      {
        root: null,
        rootMargin: '240px 0px',
        threshold: 0,
      },
    );

    observer.observe(loadMoreRef.current);

    return () => {
      observer.disconnect();
    };
  }, [generatedPapers.length, hasGenerated, hasMorePapers, isGenerating]);

  const handleUnauthorized = () => {
    clearStoredSession();
    setSession(null);
    router.push('/login');
  };

  const handleGenerateRecommendations = async () => {
    const query = searchQuery.trim();
    if (!query) return;

    setError('');
    setSuccessMessage('');
    setIsGenerating(true);
    setHasGenerated(true);

    try {
      const papers = await fetchRecommendations(query);
      setGeneratedPapers(papers);
      setVisibleCount(Math.min(INITIAL_VISIBLE_PAPERS, papers.length || INITIAL_VISIBLE_PAPERS));
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to generate recommendations';
      setError(message);
      setGeneratedPapers([]);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSavePaper = async (paperId: string) => {
    setError('');
    setSuccessMessage('');

    if (!session) {
      router.push('/login');
      return;
    }

    try {
      await savePaper(paperId, session);
      setSuccessMessage('Paper saved to your library.');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to save paper';
      if (message.toLowerCase().includes('validate credentials')) {
        handleUnauthorized();
        return;
      }
      setError(message);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header
        isAuthenticated={Boolean(session)}
        userName={session?.user.name ?? ''}
        onLogout={() => {
          clearStoredSession();
          setSession(null);
          router.push('/');
        }}
      />

      <main className="flex-1">
        {/* Search Section */}
        <section className="bg-muted border-b border-border">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <h1 className="text-3xl font-bold text-foreground mb-6">Recommendation Papers</h1>
            <div className="flex flex-col gap-3 md:flex-row md:items-center">
              <div className="flex-1">
                <SearchBar
                  value={searchQuery}
                  onSearch={setSearchQuery}
                  onQueryChange={setSearchQuery}
                  placeholder="Enter a research topic or query..."
                  inputClassName="h-12"
                />
              </div>
              <button
                type="button"
                onClick={handleGenerateRecommendations}
                disabled={!searchQuery.trim() || isGenerating}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-secondary px-6 py-2.5 text-secondary-foreground font-semibold hover:bg-secondary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Sparkles className={`h-4 w-4 ${isGenerating ? 'animate-pulse' : ''}`} />
                {isGenerating ? 'Generating...' : 'Generate Recommendations'}
              </button>
            </div>
          </div>
        </section>

        {/* Results */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {error ? (
            <div className="mb-4 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-600">
              {error}
            </div>
          ) : null}
          {successMessage ? (
            <div className="mb-4 rounded-lg border border-emerald-300 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
              {successMessage}
            </div>
          ) : null}

          {hasGenerated && isGenerating ? (
            <div className="flex min-h-[280px] items-center justify-center">
              <div className="relative flex flex-col items-center gap-3 text-center">
                <span className="absolute inline-flex h-20 w-20 animate-ping rounded-full bg-secondary/20" />
                <span className="absolute inline-flex h-16 w-16 animate-pulse rounded-full border border-secondary/20" />
                <div className="relative z-10 flex h-16 w-16 items-center justify-center rounded-full bg-secondary text-secondary-foreground shadow-md">
                  <Sparkles className="h-7 w-7 animate-pulse" />
                </div>
                {/* <p className="relative z-10 text-sm text-muted-foreground">
                  Generating recommendations for "{searchQuery}"...
                </p> */}
              </div>
            </div>
          ) : hasGenerated ? (
            <>
              <div className="mb-6 text-sm text-muted-foreground">
                {`Found ${generatedPapers.length} paper${generatedPapers.length !== 1 ? 's' : ''} for "${searchQuery}"`}
              </div>
              <PaperGrid
                papers={visiblePapers}
                isEmpty={generatedPapers.length === 0}
                onDownload={handleSavePaper}
              />
              {hasMorePapers ? (
                <div ref={loadMoreRef} className="mt-8 flex justify-center">
                  <p className="text-sm text-muted-foreground">Scroll to load more recommendations...</p>
                </div>
              ) : null}
            </>
          ) : (
            <div className="rounded-lg border border-border bg-muted/30 p-8 text-center">
              <p className="text-muted-foreground">Use the search bar, then click Generate Recommendations to view suggested papers.</p>
            </div>
          )}
        </section>
      </main>

      <Footer />
    </div>
  );
}
