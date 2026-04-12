'use client';

import { useEffect, useState } from 'react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { Download, ExternalLink, ChevronLeft } from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { fetchPaperById, UIPaperDetail } from '@/lib/api';
import { AuthSession, clearStoredSession, getStoredSession } from '@/lib/auth';

interface PaperDetailProps {
  params: {
    id: string;
  };
}

export default function PaperDetailPage({ params }: PaperDetailProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [session, setSession] = useState<AuthSession | null>(null);
  const [paper, setPaper] = useState<UIPaperDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const returnTo = searchParams.get('from');

  const handleBack = () => {
    if (returnTo && returnTo.startsWith('/')) {
      router.push(returnTo);
      return;
    }
    router.back();
  };

  const handleLogout = () => {
    clearStoredSession();
    setSession(null);
    router.push('/');
  };

  // Load session on mount
  useEffect(() => {
    const currentSession = getStoredSession();
    setSession(currentSession);
  }, []);

  useEffect(() => {
    let isMounted = true;

    const loadPaper = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const payload = await fetchPaperById(params.id);
        if (isMounted) {
          setPaper(payload);
        }
      } catch (err) {
        if (isMounted) {
          setPaper(null);
          setError(err instanceof Error ? err.message : 'Unable to load paper details');
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    loadPaper();
    return () => {
      isMounted = false;
    };
  }, [params.id]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col bg-background">
        <Header
          isAuthenticated={!!session}
          userName={session?.user.name}
          onLogout={handleLogout}
        />
        <main className="flex-1 max-w-4xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-12">
          <p className="text-muted-foreground">Loading paper details...</p>
        </main>
        <Footer />
      </div>
    );
  }

  if (error || !paper) {
    return (
      <div className="min-h-screen flex flex-col bg-background">
        <Header
          isAuthenticated={!!session}
          userName={session?.user.name}
          onLogout={handleLogout}
        />
        <main className="flex-1 max-w-4xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-12 space-y-4">
          <button
            onClick={handleBack}
            className="flex items-center gap-2 text-primary hover:text-primary/80 transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            Back
          </button>
          <h1 className="text-2xl font-bold text-foreground">Paper unavailable</h1>
          <p className="text-muted-foreground">{error ?? 'Paper details could not be loaded.'}</p>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header
        isAuthenticated={!!session}
        userName={session?.user.name}
        onLogout={handleLogout}
      />

      <main className="flex-1">
        {/* Header */}
        <section className="bg-muted border-b border-border">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <button
              onClick={handleBack}
              className="flex items-center gap-2 text-primary hover:text-primary/80 mb-6 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              Back
            </button>
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h1 className="text-4xl font-bold text-foreground mb-4 text-balance">
                  {paper.title}
                </h1>
                <p className="text-lg text-muted-foreground mb-4">
                  {paper.authors.join(', ')}
                </p>
                <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                  <span>{paper.publicationDate}</span>
                  {/* <span>{paper.category}</span> */}
                  <span>{paper.venue}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Content */}
        <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="md:col-span-2 space-y-8">
              {/* Abstract */}
              <div>
                <h2 className="text-2xl font-bold text-foreground mb-4">Abstract</h2>
                <p className="text-muted-foreground leading-relaxed">{paper.abstract}</p>
              </div>

              {/* Keywords */}
              {/* <div>
                <h2 className="text-2xl font-bold text-foreground mb-4">Keywords</h2>
                <div className="flex flex-wrap gap-2">
                  {paper.keywords.length === 0 && (
                    <span className="text-sm text-muted-foreground">No keywords available.</span>
                  )}
                  {paper.keywords.map((keyword) => (
                    <span
                      key={keyword}
                      className="px-3 py-1 bg-primary/10 text-primary text-sm rounded-full"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div> */}
            </div>

            {/* Sidebar */}
            <div className="md:col-span-1">
              <div className="card-base sticky top-20">
                <h3 className="font-semibold text-foreground mb-4">Paper Information</h3>
                <div className="space-y-4 text-sm">
                  <div>
                    <p className="text-muted-foreground mb-1">DOI</p>
                    <p className="text-foreground font-mono">{paper.doi}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground mb-1">Source</p>
                    <p className="text-foreground">{paper.source}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground mb-1">Publication Year</p>
                    <p className="text-foreground">{paper.publicationDate}</p>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="mt-6 space-y-3">
                  <a
                    href={paper.url || '#'}
                    target="_blank"
                    rel="noreferrer"
                    className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity font-medium"
                  >
                    <Download className="w-4 h-4" />
                    Download PDF
                  </a>
                  <a
                    href={paper.url || '#'}
                    target="_blank"
                    rel="noreferrer"
                    className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-border text-foreground rounded-lg hover:bg-muted transition-colors font-medium"
                  >
                    <ExternalLink className="w-4 h-4" />
                    View Source
                  </a>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
