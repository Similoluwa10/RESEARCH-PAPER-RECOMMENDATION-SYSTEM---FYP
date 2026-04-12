'use client';

import { usePathname } from 'next/navigation';
import { useEffect } from 'react';

const NAVIGATION_CURRENT_PATH_KEY = 'app_navigation_current_path_v1';
const NAVIGATION_PREVIOUS_PATH_KEY = 'app_navigation_previous_path_v1';

export default function NavigationHistoryTracker() {
  const pathname = usePathname();

  useEffect(() => {
    if (!pathname) {
      return;
    }

    const currentPath = window.sessionStorage.getItem(NAVIGATION_CURRENT_PATH_KEY);

    if (currentPath && currentPath !== pathname) {
      window.sessionStorage.setItem(NAVIGATION_PREVIOUS_PATH_KEY, currentPath);
      console.log('[NavigationTracker] Previous path updated:', currentPath);
    }

    if (currentPath !== pathname) {
      window.sessionStorage.setItem(NAVIGATION_CURRENT_PATH_KEY, pathname);
      console.log('[NavigationTracker] Current path set to:', pathname);
    }
  }, [pathname]);

  return null;
}
