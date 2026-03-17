'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import PaperGrid from '@/components/PaperGrid';
import { BookOpen, Heart, Zap } from 'lucide-react';
import Link from 'next/link';

interface User {
  email: string;
  name: string;
}

const mockSavedPapers = [
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
];

const mockRecommendations = [
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
  {
    id: '4',
    title: 'An Image is Worth 16x16 Words',
    authors: ['Dosovitskiy, A.', 'Beyer, L.'],
    abstract: 'While the Transformer architecture has become the de-facto standard.',
    publicationDate: '2020-10-22',
    citations: 18000,
    likes: 720,
    category: 'Computer Vision',
  },
];

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);
  const [activeTab, setActiveTab] = useState<'recommendations' | 'saved'>('recommendations');
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
        {/* Welcome Section */}
        <section className="bg-gradient-to-r from-primary/5 to-secondary/5 border-b border-border">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
            <h1 className="text-3xl font-bold text-foreground mb-2">Welcome back, {user.name}!</h1>
            <p className="text-muted-foreground">
              Manage your saved papers and get personalized recommendations
            </p>
          </div>
        </section>

        {/* Stats Section */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <div className="card-base">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Saved Papers</p>
                  <p className="text-3xl font-bold text-foreground">{mockSavedPapers.length}</p>
                </div>
                <BookOpen className="w-8 h-8 text-primary/20" />
              </div>
            </div>

            <div className="card-base">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Recommendations</p>
                  <p className="text-3xl font-bold text-foreground">{mockRecommendations.length}</p>
                </div>
                <Zap className="w-8 h-8 text-primary/20" />
              </div>
            </div>

            <div className="card-base">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Favorite Topics</p>
                  <p className="text-3xl font-bold text-foreground">5</p>
                </div>
                <Heart className="w-8 h-8 text-primary/20" />
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-4 border-b border-border mb-8">
            <button
              onClick={() => setActiveTab('recommendations')}
              className={`px-4 py-3 font-medium transition-colors border-b-2 ${
                activeTab === 'recommendations'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              Personalized Recommendations
            </button>
            <button
              onClick={() => setActiveTab('saved')}
              className={`px-4 py-3 font-medium transition-colors border-b-2 ${
                activeTab === 'saved'
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              Saved Papers
            </button>
          </div>

          {/* Content */}
          <div>
            {activeTab === 'recommendations' ? (
              <>
                <h2 className="text-2xl font-bold text-foreground mb-6">
                  Papers recommended for you
                </h2>
                <PaperGrid papers={mockRecommendations} />
              </>
            ) : (
              <>
                <h2 className="text-2xl font-bold text-foreground mb-6">
                  Your saved papers
                </h2>
                <PaperGrid papers={mockSavedPapers} />
              </>
            )}
          </div>

          {/* Browse More */}
          <div className="mt-12 text-center">
            <p className="text-muted-foreground mb-4">
              Want to discover more papers?
            </p>
            <Link
              href="/explore"
              className="inline-block px-6 py-3 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity font-medium"
            >
              Explore Papers
            </Link>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
