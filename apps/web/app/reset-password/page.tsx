'use client';

import Link from 'next/link';
import { useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { ArrowLeft, Eye, EyeOff, Lock } from 'lucide-react';
import { resetPassword } from '@/lib/api';

const formInputClass =
  'w-full rounded-lg border border-granite/60 bg-light px-3 py-2 text-foreground placeholder:text-granite/75 transition-colors focus-visible:outline-none focus-visible:border-secondary focus-visible:ring-2 focus-visible:ring-secondary/40';

const submitButtonClass =
  'w-full inline-flex items-center justify-center gap-2 rounded-lg border border-secondary/70 bg-secondary px-4 py-2.5 text-secondary-foreground font-semibold shadow-sm transition-all hover:bg-secondary/90 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-secondary/40 disabled:opacity-50 disabled:cursor-not-allowed';

export default function ResetPasswordPage() {
  const params = useSearchParams();
  const token = useMemo(() => params.get('token') ?? '', [params]);

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');

    if (!token) {
      setError('Missing reset token. Please open the link from your email again.');
      return;
    }

    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setIsLoading(true);

    try {
      const message = await resetPassword(token, newPassword);
      setSuccessMessage(message);
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unable to reset password. Please try again.');
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
            <h2 className="mt-6 text-4xl font-bold leading-tight">Create a new password</h2>
            <p className="mt-4 text-secondary-foreground/90">
              Use a strong password to keep your research profile and saved papers secure.
            </p>
          </div>
          <div className="rounded-xl border border-secondary-foreground/25 bg-secondary-foreground/10 p-4 text-sm">
            Password reset links expire automatically for security.
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
              <h1 className="text-3xl font-bold text-foreground mb-2">Reset Password</h1>
              <p className="text-muted-foreground">Enter and confirm your new password.</p>
            </div>

            {error && (
              <div className="mb-6 rounded-lg border border-secondary/30 bg-secondary/10 p-3 text-sm text-secondary">
                {error}
              </div>
            )}

            {successMessage && (
              <div className="mb-6 rounded-lg border border-primary/35 bg-primary/10 p-3 text-sm text-foreground">
                {successMessage}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">New Password</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="••••••••"
                    className={`${formInputClass} pl-10 pr-11`}
                    required
                  />
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-granite" />
                  <button
                    type="button"
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    onClick={() => setShowPassword((prev) => !prev)}
                    className="absolute inset-y-0 right-0 flex items-center px-3 text-granite hover:text-secondary transition-colors"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-2">Confirm New Password</label>
                <div className="relative">
                  <input
                    type={showConfirmPassword ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    className={`${formInputClass} pl-10 pr-11`}
                    required
                  />
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-granite" />
                  <button
                    type="button"
                    aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                    onClick={() => setShowConfirmPassword((prev) => !prev)}
                    className="absolute inset-y-0 right-0 flex items-center px-3 text-granite hover:text-secondary transition-colors"
                  >
                    {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <button type="submit" disabled={isLoading} className={submitButtonClass}>
                {isLoading ? 'Resetting password...' : 'Reset Password'}
              </button>
            </form>
          </div>
        </section>
      </main>
    </div>
  );
}
