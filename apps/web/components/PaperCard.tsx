'use client';

import Link from 'next/link';
import { Heart, Download, Eye } from 'lucide-react';
import { useState } from 'react';

interface PaperCardProps {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  publicationDate: string;
  citations: number;
  likes: number;
  category: string;
  onLike?: (id: string, liked: boolean) => void;
  onDownload?: (id: string) => void;
  isLiked?: boolean;
}

export default function PaperCard({
  id,
  title,
  authors,
  abstract,
  publicationDate,
  citations,
  likes,
  category,
  onLike = () => {},
  onDownload = () => {},
  isLiked = false,
}: PaperCardProps) {
  const [liked, setLiked] = useState(isLiked);
  const [likeCount, setLikeCount] = useState(likes);

  const handleLike = () => {
    setLiked(!liked);
    setLikeCount(liked ? likeCount - 1 : likeCount + 1);
    onLike(id, !liked);
  };

  return (
    <div className="card-base hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-start justify-between mb-2">
          <Link href={`/paper/${id}`}>
            <h3 className="text-lg font-semibold text-foreground hover:text-primary transition-colors line-clamp-2">
              {title}
            </h3>
          </Link>
          <span className="ml-2 px-2 py-1 bg-muted text-muted-foreground text-xs rounded whitespace-nowrap">
            {category}
          </span>
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
          <span className="flex items-center gap-1">
            <Eye className="w-3 h-3" />
            {citations}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between gap-2">
        <button
          onClick={handleLike}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
            liked
              ? 'bg-red-50 text-red-600'
              : 'text-muted-foreground hover:bg-muted hover:text-foreground'
          }`}
        >
          <Heart className={`w-4 h-4 ${liked ? 'fill-current' : ''}`} />
          <span className="text-sm">{likeCount}</span>
        </button>
        <button
          onClick={() => onDownload(id)}
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          <Download className="w-4 h-4" />
          <span className="text-sm">Save</span>
        </button>
        <Link
          href={`/paper/${id}`}
          className="flex-1 px-3 py-2 rounded-lg bg-primary text-primary-foreground text-center text-sm font-medium hover:opacity-90 transition-opacity"
        >
          View
        </Link>
      </div>
    </div>
  );
}
