'use client';

import { useState } from 'react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import SearchBar from '@/components/SearchBar';
import PaperGrid from '@/components/PaperGrid';
import { Filter } from 'lucide-react';

// Mock data for papers
const mockPapers = [
  {
    id: '1',
    title: 'Attention Is All You Need',
    authors: ['Vaswani, A.', 'Shazeer, N.', 'Parmar, N.'],
    abstract: 'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks in an encoder-decoder configuration.',
    publicationDate: '2017-06-12',
    citations: 45000,
    likes: 1200,
    category: 'Machine Learning',
  },
  {
    id: '2',
    title: 'BERT: Pre-training of Deep Bidirectional Transformers',
    authors: ['Devlin, J.', 'Chang, M.', 'Lee, K.'],
    abstract: 'We introduce BERT, a new method of pre-training language representations that obtains state-of-the-art results.',
    publicationDate: '2018-10-11',
    citations: 35000,
    likes: 980,
    category: 'Natural Language Processing',
  },
  {
    id: '3',
    title: 'Language Models are Unsupervised Multitask Learners',
    authors: ['Radford, A.', 'Wu, J.', 'Child, R.'],
    abstract: 'Natural language processing tasks are typically approached with supervised learning on task-specific datasets.',
    publicationDate: '2019-02-14',
    citations: 28000,
    likes: 850,
    category: 'Machine Learning',
  },
  {
    id: '4',
    title: 'An Image is Worth 16x16 Words: Transformers for Image Recognition',
    authors: ['Dosovitskiy, A.', 'Beyer, L.', 'Kolesnikov, A.'],
    abstract: 'While the Transformer architecture has become the de-facto standard for natural language processing tasks.',
    publicationDate: '2020-10-22',
    citations: 18000,
    likes: 720,
    category: 'Computer Vision',
  },
  {
    id: '5',
    title: 'Scaling Laws for Neural Language Models',
    authors: ['Hoffmann, J.', 'Borgeaud, S.', 'Mensch, A.'],
    abstract: 'We investigate the scaling properties of language model loss on the LAMBADA dataset.',
    publicationDate: '2022-01-20',
    citations: 12000,
    likes: 540,
    category: 'Machine Learning',
  },
  {
    id: '6',
    title: 'Emergent Abilities of Large Language Models',
    authors: ['Wei, J.', 'Tay, Y.', 'Bommasani, R.'],
    abstract: 'We investigate the emergent abilities in large language models and analyze the underlying mechanisms.',
    publicationDate: '2022-06-15',
    citations: 8000,
    likes: 420,
    category: 'Artificial Intelligence',
  },
];

const categories = [
  'All',
  'Machine Learning',
  'Natural Language Processing',
  'Computer Vision',
  'Artificial Intelligence',
  'Deep Learning',
];

export default function ExplorePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  const filteredPapers = mockPapers.filter((paper) => {
    const matchesSearch =
      paper.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      paper.abstract.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'All' || paper.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header isAuthenticated={false} />

      <main className="flex-1">
        {/* Search Section */}
        <section className="bg-muted border-b border-border">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <h1 className="text-3xl font-bold text-foreground mb-6">Explore Papers</h1>
            <SearchBar onSearch={setSearchQuery} placeholder="Search by title, author, or keywords..." />
          </div>
        </section>

        {/* Filters and Results */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {/* Filter Bar */}
          <div className="mb-8">
            <button
              onClick={() => setIsFilterOpen(!isFilterOpen)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border hover:bg-muted transition-colors md:hidden mb-4"
            >
              <Filter className="w-4 h-4" />
              Filters
            </button>

            <div className={`grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 ${isFilterOpen ? 'block' : 'hidden md:grid'}`}>
              {categories.map((category) => (
                <button
                  key={category}
                  onClick={() => setSelectedCategory(category)}
                  className={`px-4 py-2 rounded-lg transition-colors text-sm font-medium ${
                    selectedCategory === category
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-foreground hover:bg-border'
                  }`}
                >
                  {category}
                </button>
              ))}
            </div>
          </div>

          {/* Results Info */}
          <div className="mb-6 text-sm text-muted-foreground">
            Found {filteredPapers.length} paper{filteredPapers.length !== 1 ? 's' : ''}
            {searchQuery && ` for "${searchQuery}"`}
          </div>

          {/* Papers Grid */}
          <PaperGrid papers={filteredPapers} isEmpty={filteredPapers.length === 0} />
        </section>
      </main>

      <Footer />
    </div>
  );
}
