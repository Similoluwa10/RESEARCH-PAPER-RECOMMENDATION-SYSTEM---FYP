'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import PaperGrid from '@/components/PaperGrid';
import Link from 'next/link';
import {
  fetchPersonalizedRecommendations,
  listSavedPapers,
  savePaper,
  unsavePaper,
  UIPaper,
} from '@/lib/api';
import { AuthSession, clearStoredSession, getStoredSession } from '@/lib/auth';

export default function DashboardPage() {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [savedPapers, setSavedPapers] = useState<UIPaper[]>([]);
  const [recommendations, setRecommendations] = useState<UIPaper[]>([]);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const currentSession = getStoredSession();
    if (!currentSession) {
      router.push('/login');
      return;
    }

    setSession(currentSession);

    const loadData = async () => {
      try {
        const [saved, personalized] = await Promise.all([
          listSavedPapers(currentSession),
          fetchPersonalizedRecommendations(currentSession),
        ]);
        setSavedPapers(saved);
        setRecommendations(personalized);
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : 'Failed to load dashboard data';
        if (message.toLowerCase().includes('validate credentials')) {
          clearStoredSession();
          router.push('/login');
          return;
        }
        setError(message);
      } finally {
        setIsLoading(false);
      }
    };

    void loadData();
  }, [router]);

  const handleLogout = () => {
    clearStoredSession();
    setSession(null);
    router.push('/');
  };

  const handleSavePaper = async (paperId: string) => {
    if (!session) return;

    try {
      await savePaper(paperId, session);
      const updated = await listSavedPapers(session);
      setSavedPapers(updated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update saved paper');
    }
  };

  const handleUnsavePaper = async (paperId: string) => {
    if (!session) return;

    try {
      await unsavePaper(paperId, session);
      const updated = await listSavedPapers(session);
      setSavedPapers(updated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to unsave paper');
    }
  };

  if (!session) {
    return null;
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header isAuthenticated={true} userName={session.user.name} onLogout={handleLogout} />

      <main className="flex-1">
        {/* Welcome Section */}
        <section className="bg-gradient-to-r from-primary/5 to-secondary/5 border-b border-border">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <h1 className="text-3xl font-bold text-foreground mb-2">Welcome back, {session.user.name}!</h1>
            <p className="text-muted-foreground">
              You have {savedPapers.length} saved paper{savedPapers.length !== 1 ? 's' : ''}. Manage your collection and get recommendations.
            </p>
          </div>
        </section>

        {/* Stats Section */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {error ? (
            <div className="mb-6 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-600">
              {error}
            </div>
          ) : null}

          <div className="space-y-12">
            <div>
              <h2 className="text-2xl font-bold text-foreground mb-6">Your saved papers</h2>
              <PaperGrid
                papers={savedPapers}
                isLoading={isLoading}
                isEmpty={!isLoading && savedPapers.length === 0}
                onUnsave={handleUnsavePaper}
              />
            </div>

            <div>
              <h2 className="text-2xl font-bold text-foreground mb-6">Papers recommended for you</h2>
              <PaperGrid
                papers={recommendations}
                isLoading={isLoading}
                isEmpty={!isLoading && recommendations.length === 0}
                onDownload={handleSavePaper}
              />
            </div>
          </div>

          {/* Browse More */}
          <div className="mt-12 text-center">
            <p className="text-muted-foreground mb-4">
              Want to discover more papers?
            </p>
            <Link
              href="/recommendation"
              className="inline-block px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity font-medium"
            >
              Get Research Recommendations
            </Link>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
