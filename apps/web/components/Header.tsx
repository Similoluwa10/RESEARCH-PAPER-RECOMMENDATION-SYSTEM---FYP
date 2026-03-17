'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Menu, X, LogOut, Settings } from 'lucide-react';

interface HeaderProps {
  isAuthenticated?: boolean;
  userName?: string;
  onLogout?: () => void;
}

export default function Header({
  isAuthenticated = false,
  userName = '',
  onLogout = () => {},
}: HeaderProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const router = useRouter();

  const handleLogout = () => {
    onLogout();
    router.push('/');
  };

  return (
    <header className="sticky top-0 z-50 bg-card border-b border-border shadow-sm animate-fade-up">
      <div className="max-w-7xl mx-auto px-5 py-1 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-lg">P</span>
            </div>
            <span className="text-xl font-bold text-foreground hidden sm:inline">
              PaperHub
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-8">
            {isAuthenticated ? (
              <>
                <Link
                  href="/dashboard"
                  className="text-foreground hover:text-secondary transition-all hover:-translate-y-0.5"
                >
                  Dashboard
                </Link>
                <Link
                  href="/recommendation"
                  className="text-foreground hover:text-secondary transition-all hover:-translate-y-0.5"
                >
                  Get Recommendations
                </Link>
                <Link
                  href="/profile"
                  className="text-foreground hover:text-secondary transition-all hover:-translate-y-0.5"
                >
                  Profile
                </Link>
                <div className="flex items-center gap-3 pl-4 border-l border-border">
                  <span className="text-sm text-muted-foreground">{userName}</span>
                  <button
                    onClick={handleLogout}
                    className="p-2 hover:bg-muted rounded-lg transition-colors"
                    aria-label="Logout"
                  >
                    <LogOut className="w-5 h-5 text-foreground" />
                  </button>
                </div>
              </>
            ) : (
              <>
                <Link
                  href="/recommendation"
                  className="text-foreground hover:text-secondary transition-all hover:-translate-y-0.5"
                >
                  Get Recommendations
                </Link>
                <Link
                  href="/login"
                  className="px-4 py-2 rounded-lg border border-border text-foreground hover:bg-muted transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  href="/signup"
                  className="px-4 py-2 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                >
                  Sign Up
                </Link>
              </>
            )}
          </nav>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2"
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            aria-label="Toggle menu"
          >
            {isMenuOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <nav className="md:hidden pb-4 space-y-2 animate-scale-in-soft">
            {isAuthenticated ? (
              <>
                <Link
                  href="/dashboard"
                  className="block px-3 py-2 rounded-lg hover:bg-muted text-foreground transition-transform hover:translate-x-1"
                >
                  Dashboard
                </Link>
                <Link
                  href="/recommendation"
                  className="block px-3 py-2 rounded-lg hover:bg-muted text-foreground transition-transform hover:translate-x-1"
                >
                  Recommendation
                </Link>
                <Link
                  href="/profile"
                  className="block px-3 py-2 rounded-lg hover:bg-muted text-foreground transition-transform hover:translate-x-1"
                >
                  Profile
                </Link>
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-3 py-2 rounded-lg hover:bg-muted text-foreground flex items-center gap-2 transition-transform hover:translate-x-1"
                >
                  <LogOut className="w-4 h-4" />
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/recommendation"
                  className="block px-3 py-2 rounded-lg hover:bg-muted text-foreground transition-transform hover:translate-x-1"
                >
                  Recommendation
                </Link>
                <Link
                  href="/login"
                  className="block px-3 py-2 rounded-lg border border-border text-foreground"
                >
                  Sign In
                </Link>
                <Link
                  href="/signup"
                  className="block px-3 py-2 rounded-lg bg-secondary text-secondary-foreground"
                >
                  Sign Up
                </Link>
              </>
            )}
          </nav>
        )}
      </div>
    </header>
  );
}
