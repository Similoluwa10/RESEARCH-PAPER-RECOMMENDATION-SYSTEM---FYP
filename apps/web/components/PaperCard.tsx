'use client';

import Link from 'next/link';
import { Trash2, Download } from 'lucide-react';
import { usePathname, useSearchParams } from 'next/navigation';

interface PaperCardProps {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  publicationDate: string;
  category: string;
  onDownload?: (id: string) => void;
  onUnsave?: (id: string) => void;
}

export default function PaperCard({
  id,
  title,
  authors,
  abstract,
  publicationDate,
  category,
  onDownload = () => {},
  onUnsave,
}: PaperCardProps) {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const currentSearch = searchParams.toString();
  const returnPath = currentSearch ? `${pathname}?${currentSearch}` : pathname;

  return (
    <div className="card-base p-6 hover:shadow-lg hover:-translate-y-1 transition-all duration-300">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-start justify-between mb-2">
          <Link
            href={{
              pathname: `/paper/${id}`,
              query: { from: returnPath },
            }}
          >
            <h3 className="text-lg font-semibold text-foreground hover:text-primary transition-colors duration-200 line-clamp-2">
              {title}
            </h3>
          </Link>
          {/* <span className="ml-2 px-2 py-1 bg-muted text-muted-foreground text-xs rounded whitespace-nowrap">
            {category}
          </span> */}
        </div>
        <p className="text-sm text-muted-foreground">
          {authors.slice(0, 3).join(', ')}
          {authors.length > 3 && ` +${authors.length - 3}`}
        </p>
      </div>

      {/* Abstract */}
      <p className="text-sm text-muted-foreground mb-4 line-clamp-3">{abstract}</p>

      {/* Metadata */}
      <div className="flex items-center justify-between text-xs text-muted-foreground mb-4 pb-4 border-b border-border">
        <span>{publicationDate}</span>
        <div className="flex gap-4">
          {/* <span className="flex items-center gap-1">
            <Eye className="w-3 h-3" />
            {citations}
          </span> */}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between gap-2">
        {onUnsave ? (
          <button
            onClick={() => onUnsave(id)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-muted-foreground hover:bg-red-50 hover:text-red-600 transition-all duration-200 hover:-translate-y-0.5"
            title="Unsave this paper"
          >
            <Trash2 className="w-4 h-4" />
            <span className="text-sm">Unsave</span>
          </button>
        ) : (
          <button
            onClick={() => onDownload(id)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-all duration-200 hover:-translate-y-0.5"
          >
            <Download className="w-4 h-4" />
            <span className="text-sm">Save</span>
          </button>
        )}
        <Link
          href={{
            pathname: `/paper/${id}`,
            query: { from: returnPath },
          }}
          className="flex-1 px-3 py-2 rounded-lg bg-primary text-primary-foreground text-center text-sm font-medium hover:opacity-90 hover:-translate-y-0.5 transition-all duration-200"
        >
          View
        </Link>
      </div>
    </div>
  );
}
