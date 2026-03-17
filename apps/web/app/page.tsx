'use client';

import Link from 'next/link';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { ArrowRight, Sparkles, Users, Zap } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-4xl md:text-5xl font-bold text-foreground mb-6 text-balance">
                Discover Research Papers That Matter
              </h1>
              <p className="text-xl text-muted-foreground mb-8 text-pretty">
                PaperHub connects researchers with the latest scientific discoveries. Get personalized recommendations, save papers, and build your research library.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  href="/signup"
                  className="btn-primary flex items-center justify-center gap-2"
                >
                  Get Started <ArrowRight className="w-5 h-5" />
                </Link>
                <Link
                  href="/explore"
                  className="btn-outline flex items-center justify-center gap-2"
                >
                  Browse Papers
                </Link>
              </div>
            </div>
            <div className="hidden md:flex items-center justify-center">
              <div className="w-full aspect-square rounded-2xl bg-gradient-to-br from-primary/10 to-secondary/10 flex items-center justify-center">
                <Sparkles className="w-32 h-32 text-primary/30" />
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="bg-muted py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 className="text-3xl font-bold text-foreground mb-12 text-center">Why Choose PaperHub?</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="card-base">
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                  <Sparkles className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-3">Smart Recommendations</h3>
                <p className="text-muted-foreground">
                  AI-powered recommendations tailored to your research interests and reading history.
                </p>
              </div>

              <div className="card-base">
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                  <Users className="w-6 h-6 text-primary" />
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-3">Community Driven</h3>
                <p className="text-muted-foreground">
                  Connect with researchers worldwide. Share insights and collaborate on topics you care about.
                </p>
              </div>

              <div className="card-base">
                <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4">
                  <Zap className="w-6 h-6 text-primary" />
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
          <div className="rounded-2xl bg-gradient-to-r from-primary to-primary/80 p-12 text-center">
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
