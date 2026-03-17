'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import ProfileCard from '@/components/ProfileCard';
import PaperGrid from '@/components/PaperGrid';
import { Mail, Edit2 } from 'lucide-react';
import Link from 'next/link';

interface User {
  email: string;
  name: string;
}

const mockUserPapers = [
  {
    id: '1',
    title: 'Attention Is All You Need',
    authors: ['Vaswani, A.', 'Shazeer, N.'],
    abstract: 'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.',
    publicationDate: '2017-06-12',
    citations: 45000,
    likes: 1200,
    category: 'Machine Learning',
  },
  {
    id: '2',
    title: 'BERT: Pre-training of Deep Bidirectional Transformers',
    authors: ['Devlin, J.', 'Chang, M.'],
    abstract: 'We introduce BERT, a new method of pre-training language representations.',
    publicationDate: '2018-10-11',
    citations: 35000,
    likes: 980,
    category: 'NLP',
  },
  {
    id: '3',
    title: 'Language Models are Unsupervised Multitask Learners',
    authors: ['Radford, A.', 'Wu, J.'],
    abstract: 'Natural language processing tasks are typically approached with supervised learning.',
    publicationDate: '2019-02-14',
    citations: 28000,
    likes: 850,
    category: 'Machine Learning',
  },
];

export default function ProfilePage() {
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();

  useEffect(() => {
    const userData = localStorage.getItem('user');
    if (!userData) {
      router.push('/login');
      return;
    }
    setUser(JSON.parse(userData));
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem('user');
    router.push('/');
  };

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header isAuthenticated={true} userName={user.name} onLogout={handleLogout} />

      <main className="flex-1">
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Profile Sidebar */}
            <div className="md:col-span-1">
              <ProfileCard
                name={user.name}
                email={user.email}
                bio="Passionate researcher interested in machine learning and AI."
                affiliation="Research Institute"
                joinDate="January 2024"
                savedPapers={12}
                recommendations={8}
              />

              {/* Edit Profile Button */}
              <button className="w-full mt-4 flex items-center justify-center gap-2 px-4 py-3 rounded-lg border border-border text-foreground hover:bg-muted transition-colors font-medium">
                <Edit2 className="w-4 h-4" />
                Edit Profile
              </button>

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
                      {user.email}
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
                <PaperGrid papers={mockUserPapers} />
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
