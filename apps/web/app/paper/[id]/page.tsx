'use client';

import { useState } from 'react';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import { Heart, Download, Share2, ExternalLink, ChevronLeft } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

interface PaperDetailProps {
  params: {
    id: string;
  };
}

// Mock paper data
const mockPaperData: Record<string, any> = {
  '1': {
    id: '1',
    title: 'Attention Is All You Need',
    authors: ['Ashish Vaswani', 'Noam Shazeer', 'Parmar Niki', 'Jakob Uszkoreit', 'Llion Jones'],
    abstract:
      'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks in an encoder-decoder configuration. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.',
    publicationDate: '2017-06-12',
    citations: 45000,
    likes: 1200,
    category: 'Machine Learning',
    doi: '10.5555/3295222.3295349',
    arxivId: '1706.03762',
    fullText: `This paper introduces the Transformer architecture, which has become fundamental to modern deep learning...`,
    keywords: ['Transformers', 'Attention Mechanism', 'Sequence-to-Sequence', 'Neural Networks'],
    relatedPapers: [
      {
        id: '2',
        title: 'BERT: Pre-training of Deep Bidirectional Transformers',
        authors: ['Devlin, J.', 'Chang, M.'],
      },
      {
        id: '3',
        title: 'Language Models are Unsupervised Multitask Learners',
        authors: ['Radford, A.', 'Wu, J.'],
      },
    ],
  },
};

function buildFallbackPaper(id: string) {
  return {
    id,
    title: `Recommended Research Paper ${id}`,
    authors: ['PaperHub Recommender', 'Research Assistant'],
    abstract:
      'This paper was generated from your recommendation results. Open this page to review details, metadata, and related works while backend recommendation integration is in progress.',
    publicationDate: '2024-01-15',
    citations: 0,
    likes: 0,
    category: 'Recommended',
    doi: `10.0000/paperhub.${id}`,
    arxivId: `paperhub-${id}`,
    fullText: 'Recommendation detail placeholder content.',
    keywords: ['Recommendation', 'Research Discovery', 'PaperHub'],
    relatedPapers: [
      {
        id: '1',
        title: 'Attention Is All You Need',
        authors: ['Vaswani, A.', 'Shazeer, N.'],
      },
    ],
  };
}

export default function PaperDetailPage({ params }: PaperDetailProps) {
  const router = useRouter();
  const [isLiked, setIsLiked] = useState(false);
  const paper = mockPaperData[params.id] ?? buildFallbackPaper(params.id);

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />

      <main className="flex-1">
        {/* Header */}
        <section className="bg-muted border-b border-border">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <button
              onClick={() => router.back()}
              className="flex items-center gap-2 text-primary hover:text-primary/80 mb-6 transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              Back
            </button>
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h1 className="text-4xl font-bold text-foreground mb-4 text-balance">
                  {paper.title}
                </h1>
                <p className="text-lg text-muted-foreground mb-4">
                  {paper.authors.join(', ')}
                </p>
                <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                  <span>{paper.publicationDate}</span>
                  <span>{paper.category}</span>
                  <span>{paper.citations.toLocaleString()} citations</span>
                </div>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setIsLiked(!isLiked)}
                  className={`p-2 rounded-lg transition-colors ${
                    isLiked
                      ? 'bg-red-50 text-red-600'
                      : 'bg-muted text-muted-foreground hover:text-foreground'
                  }`}
                  title="Like this paper"
                >
                  <Heart className={`w-6 h-6 ${isLiked ? 'fill-current' : ''}`} />
                </button>
                <button
                  className="p-2 rounded-lg bg-muted text-muted-foreground hover:text-foreground transition-colors"
                  title="Share this paper"
                >
                  <Share2 className="w-6 h-6" />
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Content */}
        <section className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Main Content */}
            <div className="md:col-span-2 space-y-8">
              {/* Abstract */}
              <div>
                <h2 className="text-2xl font-bold text-foreground mb-4">Abstract</h2>
                <p className="text-muted-foreground leading-relaxed">{paper.abstract}</p>
              </div>

              {/* Keywords */}
              <div>
                <h2 className="text-2xl font-bold text-foreground mb-4">Keywords</h2>
                <div className="flex flex-wrap gap-2">
                  {paper.keywords.map((keyword: string) => (
                    <span
                      key={keyword}
                      className="px-3 py-1 bg-primary/10 text-primary text-sm rounded-full"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>

              {/* Related Papers */}
              <div>
                <h2 className="text-2xl font-bold text-foreground mb-4">Related Papers</h2>
                <div className="space-y-3">
                  {paper.relatedPapers.map((related: any) => (
                    <Link
                      key={related.id}
                      href={`/paper/${related.id}`}
                      className="block p-4 border border-border rounded-lg hover:bg-muted transition-colors"
                    >
                      <h3 className="font-semibold text-foreground mb-1 hover:text-primary">
                        {related.title}
                      </h3>
                      <p className="text-sm text-muted-foreground">{related.authors.join(', ')}</p>
                    </Link>
                  ))}
                </div>
              </div>
            </div>

            {/* Sidebar */}
            <div className="md:col-span-1">
              <div className="card-base sticky top-20">
                <h3 className="font-semibold text-foreground mb-4">Paper Information</h3>
                <div className="space-y-4 text-sm">
                  <div>
                    <p className="text-muted-foreground mb-1">DOI</p>
                    <p className="text-foreground font-mono">{paper.doi}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground mb-1">arXiv ID</p>
                    <p className="text-foreground font-mono">{paper.arxivId}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground mb-1">Citation Count</p>
                    <p className="text-foreground">{paper.citations.toLocaleString()}</p>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="mt-6 space-y-3">
                  <button className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity font-medium">
                    <Download className="w-4 h-4" />
                    Download PDF
                  </button>
                  <a
                    href="#"
                    className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-border text-foreground rounded-lg hover:bg-muted transition-colors font-medium"
                  >
                    <ExternalLink className="w-4 h-4" />
                    View on arXiv
                  </a>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
