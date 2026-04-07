'use client';

import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { updateCurrentUserProfile } from '@/lib/api';
import {
  AuthSession,
  clearStoredSession,
  getStoredSession,
  updateStoredSessionUser,
} from '@/lib/auth';

const formInputClass =
  'w-full rounded-lg border border-granite/60 bg-light px-3 py-2 text-foreground placeholder:text-granite/75 transition-colors focus-visible:outline-none focus-visible:border-secondary focus-visible:ring-2 focus-visible:ring-secondary/40';

const primaryButtonClass =
  'inline-flex items-center justify-center gap-2 rounded-lg border border-secondary/70 bg-secondary px-4 py-2.5 text-secondary-foreground font-semibold shadow-sm transition-all hover:bg-secondary/90 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-secondary/40 disabled:opacity-50 disabled:cursor-not-allowed';

export default function EditProfilePage() {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [bio, setBio] = useState('');
  const [affiliation, setAffiliation] = useState('');
  const [interests, setInterests] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const currentSession = getStoredSession();
    if (!currentSession) {
      router.push('/login');
      return;
    }

    setSession(currentSession);
    setName(currentSession.user.name || '');
    setEmail(currentSession.user.email || '');

    const existingBio = window.localStorage.getItem('paperhub_profile_bio') || '';
    const existingAffiliation = window.localStorage.getItem('paperhub_profile_affiliation') || '';
    const existingInterests = window.localStorage.getItem('paperhub_profile_interests') || '';

    setBio(existingBio);
    setAffiliation(existingAffiliation);
    setInterests(existingInterests);
  }, [router]);

  const isUnchanged = useMemo(() => {
    if (!session) return true;

    const initialBio = window.localStorage.getItem('paperhub_profile_bio') || '';
    const initialAffiliation = window.localStorage.getItem('paperhub_profile_affiliation') || '';
    const initialInterests = window.localStorage.getItem('paperhub_profile_interests') || '';

    return (
      name.trim() === (session.user.name || '').trim() &&
      email.trim() === (session.user.email || '').trim() &&
      bio.trim() === initialBio.trim() &&
      affiliation.trim() === initialAffiliation.trim() &&
      interests.trim() === initialInterests.trim()
    );
  }, [session, name, email, bio, affiliation, interests]);

  const handleLogout = () => {
    clearStoredSession();
    setSession(null);
    router.push('/');
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!session) {
      router.push('/login');
      return;
    }

    if (!name.trim()) {
      setError('Name is required.');
      return;
    }

    if (!email.trim()) {
      setError('Email is required.');
      return;
    }

    setIsSaving(true);

    try {
      const preferredCategories = interests
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean);

      const updatedUser = await updateCurrentUserProfile(session, {
        name: name.trim(),
        email: email.trim(),
        preferred_categories: preferredCategories.length > 0 ? preferredCategories : [],
      });

      const next = updateStoredSessionUser({
        name: updatedUser.name,
        email: updatedUser.email,
        role: updatedUser.role,
      });

      if (next) {
        setSession(next);
      }

      window.localStorage.setItem('paperhub_profile_bio', bio.trim());
      window.localStorage.setItem('paperhub_profile_affiliation', affiliation.trim());
      window.localStorage.setItem('paperhub_profile_interests', interests.trim());

      await new Promise((resolve) => setTimeout(resolve, 500));
      setSuccess('Profile updated successfully.');
    } catch {
      setError('Unable to update profile right now. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  if (!session) {
    return null;
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header isAuthenticated={true} userName={session.user.name} onLogout={handleLogout} />

      <main className="flex-1">
        <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="text-3xl font-bold text-foreground">Edit Profile</h1>
              <p className="text-muted-foreground mt-1">Update your public and account information.</p>
            </div>
            <Link
              href="/profile"
              className="inline-flex items-center justify-center rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted"
            >
              Back to Profile
            </Link>
          </div>

          <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
            {error && (
              <div className="mb-5 rounded-lg border border-secondary/30 bg-secondary/10 p-3 text-sm text-secondary">
                {error}
              </div>
            )}

            {success && (
              <div className="mb-5 rounded-lg border border-primary/35 bg-primary/10 p-3 text-sm text-foreground">
                {success}
              </div>
            )}

            <form onSubmit={handleSave} className="space-y-5">
              <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
                <div>
                  <label className="mb-2 block text-sm font-medium text-foreground">Name</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className={formInputClass}
                    placeholder="Your full name"
                    required
                  />
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-foreground">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className={formInputClass}
                    placeholder="you@example.com"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-foreground">Affiliation</label>
                <input
                  type="text"
                  value={affiliation}
                  onChange={(e) => setAffiliation(e.target.value)}
                  className={formInputClass}
                  placeholder="University, lab, or organization"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-foreground">Research Interests</label>
                <input
                  type="text"
                  value={interests}
                  onChange={(e) => setInterests(e.target.value)}
                  className={formInputClass}
                  placeholder="e.g., NLP, software architecture, machine learning"
                />
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-foreground">Bio</label>
                <textarea
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  rows={5}
                  className={`${formInputClass} resize-y`}
                  placeholder="Tell others a bit about your research focus."
                />
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <button type="submit" disabled={isSaving || isUnchanged} className={primaryButtonClass}>
                  {isSaving ? 'Saving...' : 'Save Changes'}
                </button>
                <Link
                  href="/profile"
                  className="inline-flex items-center justify-center rounded-lg border border-border px-4 py-2.5 text-sm font-medium text-foreground transition-colors hover:bg-muted"
                >
                  Cancel
                </Link>
              </div>
            </form>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
