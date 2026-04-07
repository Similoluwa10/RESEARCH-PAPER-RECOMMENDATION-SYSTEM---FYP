'use client';

import Link from 'next/link';
import { useState } from 'react';
import { ArrowLeft, Mail } from 'lucide-react';
import { requestPasswordResetWithDetails } from '@/lib/api';

const formInputClass =
  'w-full rounded-lg border border-granite/60 bg-light px-3 py-2 text-foreground placeholder:text-granite/75 transition-colors focus-visible:outline-none focus-visible:border-secondary focus-visible:ring-2 focus-visible:ring-secondary/40';

const submitButtonClass =
  'w-full inline-flex items-center justify-center gap-2 rounded-lg border border-secondary/70 bg-secondary px-4 py-2.5 text-secondary-foreground font-semibold shadow-sm transition-all hover:bg-secondary/90 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-secondary/40 disabled:opacity-50 disabled:cursor-not-allowed';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isSent, setIsSent] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [resetUrl, setResetUrl] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email) {
      setError('Please enter your email address.');
      return;
    }

    setIsLoading(true);
    setResetUrl(null);

    try {
      const response = await requestPasswordResetWithDetails(email);
      setSuccessMessage(response.message);
      setResetUrl(response.resetUrl ?? null);
      setIsSent(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unable to process your request right now. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <main className="min-h-screen grid lg:grid-cols-2">
        <aside className="hidden lg:flex flex-col justify-around bg-dark/12 bg-gradient-to-br from-primary via-primary/95 to-secondary/60 bg-blend-multiply p-12 text-secondary-foreground">
          <div>
            <p className="text-sm uppercase tracking-[0.2em] text-secondary-foreground/85">PaperHub</p>
            <h2 className="mt-6 text-4xl font-bold leading-tight">Regain access to your workspace</h2>
            <p className="mt-4 text-secondary-foreground/90">
              Enter your account email and we will send password reset instructions.
            </p>
          </div>
          <div className="rounded-xl border border-secondary-foreground/25 bg-secondary-foreground/10 p-4 text-sm">
            If an account exists for the entered email, reset instructions will be sent.
          </div>
        </aside>

        <section className="flex items-center justify-center bg-card px-6 py-10 sm:px-10 lg:px-16">
          <div className="w-full max-w-md">
            <Link
              href="/login"
              className="mb-6 inline-flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to sign in
            </Link>

            <div className="mb-8 text-center">
              <h1 className="text-3xl font-bold text-foreground mb-2">Forgot Password</h1>
              <p className="text-muted-foreground">We will email you a secure reset link.</p>
            </div>

            {error && (
              <div className="mb-6 rounded-lg border border-secondary/30 bg-secondary/10 p-3 text-sm text-secondary">
                {error}
              </div>
            )}

            {isSent ? (
              <div className="space-y-3 rounded-lg border border-primary/35 bg-primary/10 p-4 text-sm text-foreground">
                <p>
                  {successMessage || 'Check your inbox. If that email is registered, you will receive reset instructions shortly.'}
                </p>
                {resetUrl && (
                  <p>
                    Development reset link:{' '}
                    <Link href={resetUrl} className="font-semibold text-secondary hover:underline">
                      Open reset page
                    </Link>
                  </p>
                )}
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">Email Address</label>
                  <div className="relative">
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@example.com"
                      className={`${formInputClass} pl-10`}
                      required
                    />
                    <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-granite" />
                  </div>
                </div>

                <button type="submit" disabled={isLoading} className={submitButtonClass}>
                  {isLoading ? 'Sending reset link...' : 'Send Reset Link'}
                </button>
              </form>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
