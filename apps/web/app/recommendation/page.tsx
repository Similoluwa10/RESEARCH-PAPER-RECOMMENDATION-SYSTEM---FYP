'use client';

import { useState } from 'react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import SearchBar from '@/components/SearchBar';
import PaperGrid from '@/components/PaperGrid';
import { Sparkles } from 'lucide-react';

interface Paper {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  publicationDate: string;
  citations: number;
  likes: number;
  category: string;
}

/*
  Pre-generated papers and category filters are intentionally commented out.
  Recommendation results should be generated only after user action.

  const mockPapers = [ ... ]
  const categories = [ ... ]
*/

const recommendationTemplates = [
  'Survey of Recent Advances in',
  'Benchmarking Techniques for',
  'A Practical Framework for',
  'Explainable Approaches to',
  'Evaluation Methods in',
  'Scalable Architectures for',
];

const recommendationCategories = [
  'Machine Learning',
  'Natural Language Processing',
  'Artificial Intelligence',
  'Data Science',
  'Computer Vision',
  'Software Engineering',
];

function buildRecommendations(query: string): Paper[] {
  const q = query.trim();

  return recommendationTemplates.map((template, index) => ({
    id: `rec-${index + 1}`,
    title: `${template} ${q}`,
    authors: [`Researcher ${index + 1}`, `Scholar ${index + 2}`],
    abstract: `This recommended paper discusses ${q.toLowerCase()} with a focus on methods, evaluation metrics, and practical adoption in modern research systems.`,
    publicationDate: `202${index % 5}-0${(index % 9) + 1}-15`,
    citations: 800 + index * 230,
    likes: 90 + index * 17,
    category: recommendationCategories[index % recommendationCategories.length],
  }));
}

export default function RecommendationPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [generatedPapers, setGeneratedPapers] = useState<Paper[]>([]);
  const [hasGenerated, setHasGenerated] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerateRecommendations = () => {
    const query = searchQuery.trim();
    if (!query) return;

    setIsGenerating(true);
    setHasGenerated(true);

    window.setTimeout(() => {
      setGeneratedPapers(buildRecommendations(query));
      setIsGenerating(false);
    }, 350);
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header isAuthenticated={false} />

      <main className="flex-1">
        {/* Search Section */}
        <section className="bg-muted border-b border-border">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <h1 className="text-3xl font-bold text-foreground mb-6">Recommendation Papers</h1>
            <div className="flex flex-col gap-3 md:flex-row md:items-center">
              <div className="flex-1">
                <SearchBar
                  onSearch={setSearchQuery}
                  onQueryChange={setSearchQuery}
                  placeholder="Enter a research topic or query..."
                  inputClassName="h-12"
                />
              </div>
              <button
                type="button"
                onClick={handleGenerateRecommendations}
                disabled={!searchQuery.trim() || isGenerating}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-secondary px-6 py-2.5 text-secondary-foreground font-semibold hover:bg-secondary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Sparkles className={`h-4 w-4 ${isGenerating ? 'animate-pulse' : ''}`} />
                {isGenerating ? 'Generating...' : 'Generate Recommendations'}
              </button>
            </div>
          </div>
        </section>

        {/* Results */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          {hasGenerated && isGenerating ? (
            <div className="flex min-h-[280px] items-center justify-center">
              <div className="relative flex flex-col items-center gap-3 text-center">
                <span className="absolute inline-flex h-20 w-20 animate-ping rounded-full bg-secondary/20" />
                <span className="absolute inline-flex h-28 w-28 animate-pulse rounded-full border border-secondary/20" />
                <div className="relative z-10 flex h-16 w-16 items-center justify-center rounded-full bg-secondary text-secondary-foreground shadow-md">
                  <Sparkles className="h-7 w-7 animate-pulse" />
                </div>
                <p className="relative z-10 text-sm text-muted-foreground">
                  Generating recommendations for "{searchQuery}"...
                </p>
              </div>
            </div>
          ) : hasGenerated ? (
            <>
              <div className="mb-6 text-sm text-muted-foreground">
                {`Found ${generatedPapers.length} paper${generatedPapers.length !== 1 ? 's' : ''} for "${searchQuery}"`}
              </div>
              <PaperGrid papers={generatedPapers} isEmpty={generatedPapers.length === 0} />
            </>
          ) : (
            <div className="rounded-lg border border-border bg-muted/30 p-8 text-center">
              <p className="text-muted-foreground">Use the search bar, then click Generate Recommendations to view suggested papers.</p>
            </div>
          )}
        </section>
      </main>

      <Footer />
    </div>
  );
}
