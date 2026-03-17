'use client';

import PaperCard from './PaperCard';

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

interface PaperGridProps {
  papers: Paper[];
  onLike?: (id: string, liked: boolean) => void;
  onDownload?: (id: string) => void;
  isLoading?: boolean;
  isEmpty?: boolean;
}

export default function PaperGrid({
  papers,
  onLike,
  onDownload,
  isLoading = false,
  isEmpty = false,
}: PaperGridProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[...Array(6)].map((_, i) => (
          <div
            key={i}
            className="card-base p-6 animate-pulse animate-fade-up"
            style={{ animationDelay: `${i * 70}ms` }}
          >
            <div className="h-24 bg-muted rounded mb-4" />
            <div className="h-4 bg-muted rounded mb-3" />
            <div className="h-4 bg-muted rounded w-2/3" />
          </div>
        ))}
      </div>
    );
  }

  if (isEmpty || papers.length === 0) {
    return (
      <div className="text-center py-12 animate-fade-up">
        <p className="text-muted-foreground mb-2">No papers found</p>
        <p className="text-sm text-muted-foreground">
          Try adjusting your search or filters
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {papers.map((paper, index) => (
        <div key={paper.id} className="animate-fade-up" style={{ animationDelay: `${index * 60}ms` }}>
          <PaperCard
            {...paper}
            onLike={onLike}
            onDownload={onDownload}
          />
        </div>
      ))}
    </div>
  );
}
