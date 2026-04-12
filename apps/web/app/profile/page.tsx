'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import ProfileCard from '@/components/ProfileCard';
import PaperGrid from '@/components/PaperGrid';
import { Mail, Edit2 } from 'lucide-react';
import Link from 'next/link';
import { listSavedPapers, unsavePaper, UIPaper } from '@/lib/api';
import { AuthSession, clearStoredSession, getStoredSession } from '@/lib/auth';

export default function ProfilePage() {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [savedPapers, setSavedPapers] = useState<UIPaper[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const currentSession = getStoredSession();
    if (!currentSession) {
      router.push('/login');
      return;
    }

    setSession(currentSession);

    const loadSavedPapers = async () => {
      try {
        const papers = await listSavedPapers(currentSession);
        setSavedPapers(papers);
      } catch {
        clearStoredSession();
        router.push('/login');
      } finally {
        setIsLoading(false);
      }
    };

    void loadSavedPapers();
  }, [router]);

  const handleLogout = () => {
    clearStoredSession();
    setSession(null);
    router.push('/');
  };

  const handleUnsavePaper = async (paperId: string) => {
    if (!session) return;

    try {
      await unsavePaper(paperId, session);
      const updated = await listSavedPapers(session);
      setSavedPapers(updated);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to unsave paper';
      if (message.toLowerCase().includes('validate credentials')) {
        clearStoredSession();
        router.push('/login');
        return;
      }
    }
  };

  if (!session) {
    return null;
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header isAuthenticated={true} userName={session.user.name} onLogout={handleLogout} />

      <main className="flex-1">
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Profile Sidebar */}
            <div className="md:col-span-1">
              <ProfileCard
                name={session.user.name}
                email={session.user.email}
                bio="Passionate researcher interested in machine learning and AI."
                affiliation="Research Institute"
                joinDate="January 2024"
                savedPapers={savedPapers.length}
                recommendations={0}
              />

              {/* Edit Profile Button */}
              <Link
                href="/profile/edit"
                className="w-full mt-4 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border border-border text-foreground hover:bg-muted transition-colors font-medium"
              >
                <Edit2 className="w-4 h-4" />
                Edit Profile
              </Link>

              {/* Settings Section */}
              <div className="mt-8 card-base">
                <h3 className="font-semibold text-foreground mb-4">Settings</h3>
                <div className="space-y-2">
                  <Link
                    href="#"
                    className="block px-3 py-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors text-sm"
                  >
                    Preferences
                  </Link>
                  <Link
                    href="#"
                    className="block px-3 py-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors text-sm"
                  >
                    Research Interests
                  </Link>
                  <Link
                    href="#"
                    className="block px-3 py-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors text-sm"
                  >
                    Notifications
                  </Link>
                  <Link
                    href="#"
                    className="block px-3 py-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors text-sm"
                  >
                    Security
                  </Link>
                </div>
              </div>
            </div>

            {/* Main Content */}
            <div className="md:col-span-2">
              {/* About Section */}
              <div className="card-base mb-8">
                <h2 className="text-2xl font-bold text-foreground mb-6">About</h2>
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">Email</p>
                    <p className="text-foreground flex items-center gap-2">
                      <Mail className="w-4 h-4" />
                      {session.user.email}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">Member Since</p>
                    <p className="text-foreground">January 2024</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">Research Fields</p>
                    <div className="flex flex-wrap gap-2">
                      {['Machine Learning', 'AI', 'NLP'].map((field) => (
                        <span
                          key={field}
                          className="px-3 py-1 bg-primary/10 text-primary text-sm rounded-full"
                        >
                          {field}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Recent Activity */}
              <div>
                <h2 className="text-2xl font-bold text-foreground mb-6">Recently Saved Papers</h2>
                <PaperGrid
                  papers={savedPapers}
                  isLoading={isLoading}
                  isEmpty={!isLoading && savedPapers.length === 0}
                  onUnsave={handleUnsavePaper}
                />
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
