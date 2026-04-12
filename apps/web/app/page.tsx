'use client';

import Link from 'next/link';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { ArrowRight, Sparkles, Users, Zap } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AuthSession, clearStoredSession, getStoredSession } from '@/lib/auth';

export default function HomePage() {
  const [session, setSession] = useState<AuthSession | null>(null);
  const router = useRouter();

  useEffect(() => {
    const currentSession = getStoredSession();
    setSession(currentSession);
  }, []);

  const handleLogout = () => {
    clearStoredSession();
    setSession(null);
    router.push('/');
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header
        isAuthenticated={!!session}
        userName={session?.user.name}
        onLogout={handleLogout}
      />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 mb-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-6 text-balance animate-fade-up">
                Discover Research Papers That Matter
              </h1>
              <p className="text-xl text-muted-foreground mb-8 text-pretty animate-fade-up animate-delay-1">
                PaperHub connects researchers with the latest scientific discoveries. Get personalized recommendations, save papers, and build your research library.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 animate-fade-up animate-delay-2">
                <Link
                  href="/signup"
                  className="btn-primary flex items-center justify-center gap-2 transition-transform duration-200 hover:-translate-y-0.5"
                >
                  Get Started <ArrowRight className="w-5 h-5" />
                </Link>
                <Link
                  href="/recommendation"
                  className="btn-outline px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-all duration-200 hover:-translate-y-0.5 flex items-center justify-center gap-2"
                >
                  Get Recommendations
                </Link>
              </div>
            </div>
            <div className="hidden md:flex items-center justify-center">
              <div className="w-full aspect-square rounded-2xl bg-gradient-to-br from-primary/10 to-secondary/10 flex items-center justify-center animate-fade-up animate-delay-3 animate-float-soft">
                <Sparkles className="w-32 h-32 text-secondary/35" />
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="bg-muted py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 className="text-3xl font-bold text-foreground mb-12 text-center animate-fade-up">Why Choose PaperHub?</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="card-base animate-fade-up transition-transform duration-300 hover:-translate-y-1">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary/15 to-secondary/15 flex items-center justify-center mb-4">
                  <Sparkles className="w-6 h-6 text-secondary" />
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-3">Smart Recommendations</h3>
                <p className="text-muted-foreground">
                  AI-powered recommendations tailored to your research interests and reading history.
                </p>
              </div>

              <div className="card-base animate-fade-up animate-delay-1 transition-transform duration-300 hover:-translate-y-1">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary/15 to-secondary/15  flex items-center justify-center mb-4">
                  <Users className="w-6 h-6 text-secondary" />
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-3">Community Driven</h3>
                <p className="text-muted-foreground">
                  Connect with researchers worldwide. Share insights and collaborate on topics you care about.
                </p>
              </div>

              <div className="card-base animate-fade-up animate-delay-2 transition-transform duration-300 hover:-translate-y-1">
                <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary/15 to-secondary/15 flex items-center justify-center mb-4">
                  <Zap className="w-6 h-6 text-secondary" />
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-3">Lightning Fast</h3>
                <p className="text-muted-foreground">
                  Search and browse thousands of papers instantly with powerful filters and full-text search.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="rounded-2xl bg-gradient-to-r from-primary via-primary/90 to-secondary p-12 text-center animate-fade-up">
            <h2 className="text-3xl font-bold text-primary-foreground mb-6">
              Ready to Discover Your Next Paper?
            </h2>
            <p className="text-primary-foreground/90 mb-8 max-w-2xl mx-auto">
              Join thousands of researchers who use PaperHub to stay ahead of the curve.
            </p>
            <Link
              href="/signup"
              className="inline-block px-8 py-3 bg-primary-foreground text-primary font-semibold rounded-lg hover:opacity-90 transition-opacity"
            >
              Sign Up Free
            </Link>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
