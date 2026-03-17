'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Eye, EyeOff } from 'lucide-react';

const formInputClass =
  'w-full rounded-lg border border-granite/60 bg-light px-3 py-2 text-foreground placeholder:text-granite/75 transition-colors focus-visible:outline-none focus-visible:border-secondary focus-visible:ring-2 focus-visible:ring-secondary/40';

const submitButtonClass =
  'w-full inline-flex items-center justify-center gap-2 rounded-lg border border-secondary/70 bg-secondary px-4 py-2.5 text-secondary-foreground font-semibold shadow-sm transition-all hover:bg-secondary/90 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-secondary/40 disabled:opacity-50 disabled:cursor-not-allowed';

const googleButtonClass =
  'w-full inline-flex items-center justify-center gap-3 rounded-lg border border-granite/45 bg-light px-4 py-2.5 text-foreground shadow-sm transition-all hover:-translate-y-0.5 hover:bg-muted/50 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-secondary/40';

export default function SignUpPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const router = useRouter();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      // Validation
      if (!formData.name || !formData.email || !formData.password) {
        setError('Please fill in all fields');
        return;
      }

      if (formData.password !== formData.confirmPassword) {
        setError('Passwords do not match');
        return;
      }

      if (formData.password.length < 8) {
        setError('Password must be at least 8 characters');
        return;
      }

      // Simulate registration
      localStorage.setItem('user', JSON.stringify({ 
        email: formData.email, 
        name: formData.name 
      }));
      router.push('/dashboard');
    } catch (err) {
      setError('Sign up failed. Please try again.');
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
            <h2 className="mt-6 text-4xl font-bold leading-tight">
              Start your personalized research journey
            </h2>
            <p className="mt-4 text-secondary-foreground/90">
              Create your account to get tailored paper recommendations and organize your discoveries in one place.
            </p>
          </div>
          <div className="rounded-xl border border-secondary-foreground/25 bg-secondary-foreground/10 p-4 text-sm">
            Trusted by students and researchers for smarter literature discovery.
          </div>
        </aside>

        <section className="flex items-center justify-center bg-card px-6 py-10 sm:px-10 lg:px-16">
          <div className="w-full max-w-md">
                <div className="mb-8 text-center">
                  <h1 className="text-3xl font-bold text-foreground mb-2">Create Account</h1>
                  <p className="text-muted-foreground">Join PaperHub to discover and share research papers</p>
                </div>

                {error && (
                  <div className="mb-6 rounded-lg border border-secondary/30 bg-secondary/10 p-3 text-sm text-secondary">
                    {error}
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4 mb-6">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">Full Name</label>
                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      placeholder="John Doe"
                      className={formInputClass}
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">Email Address</label>
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      placeholder="you@example.com"
                      className={formInputClass}
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">Password</label>
                    <div className="relative">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        name="password"
                        value={formData.password}
                        onChange={handleChange}
                        placeholder="••••••••"
                        className={`${formInputClass} pr-11`}
                        required
                      />
                      <button
                        type="button"
                        aria-label={showPassword ? 'Hide password' : 'Show password'}
                        onClick={() => setShowPassword((prev) => !prev)}
                        className="absolute inset-y-0 right-0 flex items-center px-3 text-granite hover:text-secondary transition-colors"
                      >
                        {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">At least 8 characters</p>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">Confirm Password</label>
                    <div className="relative">
                      <input
                        type={showConfirmPassword ? 'text' : 'password'}
                        name="confirmPassword"
                        value={formData.confirmPassword}
                        onChange={handleChange}
                        placeholder="••••••••"
                        className={`${formInputClass} pr-11`}
                        required
                      />
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

                  <div className="flex items-start gap-2">
                    <input
                      type="checkbox"
                      id="terms"
                      required
                      className="mt-1 h-4 w-4 rounded border border-granite/70 accent-secondary"
                    />
                    <label htmlFor="terms" className="text-sm text-muted-foreground">
                      I agree to the{' '}
                      <Link href="/terms" className="text-secondary hover:underline">
                        Terms of Service
                      </Link>{' '}
                      and{' '}
                      <Link href="/privacy" className="text-secondary hover:underline">
                        Privacy Policy
                      </Link>
                    </label>
                  </div>

                  <button type="submit" disabled={isLoading} className={submitButtonClass}>
                    {isLoading ? 'Creating account...' : 'Create Account'}
                  </button>
                </form>

                <div className="flex items-center gap-4 mb-6">
                  <div className="flex-1 h-px bg-border" />
                  <span className="text-sm text-muted-foreground">or</span>
                  <div className="flex-1 h-px bg-border" />
                </div>

                <div className="mb-6">
                  <button type="button" className={googleButtonClass}>
                    <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden="true">
                      <path
                        fill="#EA4335"
                        d="M12 10.2v3.9h5.5c-.2 1.1-1.3 3.3-5.5 3.3A6.1 6.1 0 1 1 12 5.2c1.8 0 3 .8 3.7 1.5l2.5-2.4C16.7 2.9 14.5 2 12 2a10 10 0 1 0 0 20c5.8 0 9.6-4.1 9.6-9.8 0-.7-.1-1.3-.2-2Z"
                      />
                      <path
                        fill="#34A853"
                        d="M3.9 7.7 7.1 10A6.2 6.2 0 0 1 12 5.2c1.8 0 3 .8 3.7 1.5l2.5-2.4C16.7 2.9 14.5 2 12 2 8.2 2 4.9 4.2 3.3 7.4Z"
                      />
                      <path
                        fill="#FBBC05"
                        d="M12 22c2.4 0 4.5-.8 6-2.3l-2.8-2.2c-.8.5-1.8.9-3.2.9-2.6 0-4.8-1.7-5.6-4l-3.3 2.5A10 10 0 0 0 12 22Z"
                      />
                      <path
                        fill="#4285F4"
                        d="M21.6 12.2c0-.7-.1-1.3-.2-1.9H12v3.9h5.5c-.3 1.3-1.1 2.5-2.3 3.2l2.8 2.2c2.2-2 3.6-5 3.6-8.4Z"
                      />
                    </svg>
                    Continue with Google
                  </button>
                </div>

                <p className="text-center text-sm text-muted-foreground">
                  Already have an account?{' '}
                  <Link href="/login" className="text-secondary hover:underline font-medium">
                    Sign in
                  </Link>
                </p>
          </div>
        </section>
      </main>
    </div>
  );
}
