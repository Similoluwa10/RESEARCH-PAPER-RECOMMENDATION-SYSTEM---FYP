'use client';

import { Search, X } from 'lucide-react';
import { useEffect, useState } from 'react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  onQueryChange?: (query: string) => void;
  value?: string;
  placeholder?: string;
  className?: string;
  inputClassName?: string;
}

export default function SearchBar({
  onSearch,
  onQueryChange,
  value,
  placeholder = 'Search papers...',
  className = '',
  inputClassName = '',
}: SearchBarProps) {
  const [internalQuery, setInternalQuery] = useState('');
  const isControlled = value !== undefined;
  const query = isControlled ? value : internalQuery;

  useEffect(() => {
    if (isControlled) {
      setInternalQuery(value ?? '');
    }
  }, [isControlled, value]);

  const updateQuery = (nextValue: string) => {
    if (!isControlled) {
      setInternalQuery(nextValue);
    }
    onQueryChange?.(nextValue);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(query);
  };

  const handleClear = () => {
    updateQuery('');
    onSearch('');
  };

  return (
    <form onSubmit={handleSubmit} className={`relative ${className}`}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground pointer-events-none" />
        <input
          type="text"
          value={query}
          onChange={(e) => {
            updateQuery(e.target.value);
          }}
          placeholder={placeholder}
          className={`input-field pl-10 pr-10 w-full ${inputClassName}`}
        />
        {query && (
          <button
            type="button"
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            aria-label="Clear search"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>
    </form>
  );
}
