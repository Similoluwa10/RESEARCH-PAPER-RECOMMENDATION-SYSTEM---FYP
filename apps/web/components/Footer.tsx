'use client';

import Link from 'next/link';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-foreground border-t border-granite/40 mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand */}
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <span className="text-primary-foreground font-bold">P</span>
              </div>
              <span className="font-bold text-lg text-background">PaperHub</span>
            </div>
            <p className="text-sm text-background">
              Discover and share research papers that matter.
            </p>
          </div>

          {/* Links */}
          <div>
            <h3 className="font-semibold text-background mb-4">Platform</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/recommendation" className="text-background hover:opacity-80 transition-all hover:translate-x-0.5 inline-block">
                  Recommendations
                </Link>
              </li>
              <li>
                <Link href="/dashboard" className="text-background hover:opacity-80 transition-all hover:translate-x-0.5 inline-block">
                  Dashboard
                </Link>
              </li>              
            </ul>
          </div>

          {/* Support */}
          <div>
            <h3 className="font-semibold text-background mb-4">Support</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/help" className="text-background hover:opacity-80 transition-all hover:translate-x-0.5 inline-block">
                  Help Center
                </Link>
              </li>
              <li>
                <Link href="/contact" className="text-background hover:opacity-80 transition-all hover:translate-x-0.5 inline-block">
                  Contact Us
                </Link>
              </li>
              <li>
                <Link href="/faq" className="text-background hover:opacity-80 transition-all hover:translate-x-0.5 inline-block">
                  FAQ
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="font-semibold text-background mb-4">Legal</h3>
            <ul className="space-y-2 text-sm">
              <li>
                <Link href="/privacy" className="text-background hover:opacity-80 transition-all hover:translate-x-0.5 inline-block">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/terms" className="text-background hover:opacity-80 transition-all hover:translate-x-0.5 inline-block">
                  Terms of Service
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-background/30 pt-8">
          <p className="text-center text-sm text-background">
            &copy; {currentYear} PaperHub. All rights reserved. <br /> Copyright, devWithSimiloluwa.
          </p>
        </div>
      </div>
    </footer>
  );
}
