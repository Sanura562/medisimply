import { useCallback, useState } from "react";

const STORAGE_KEY = "medisimply_recent_searches";
const MAX_RECENT = 6;

function loadRecent() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

// Recent searches live in localStorage, not a backend table - there is no
// /recent-searches endpoint, so history is per-browser only.
export function useRecentSearches() {
  const [recentSearches, setRecentSearches] = useState(loadRecent);

  const addRecentSearch = useCallback((name) => {
    setRecentSearches((prev) => {
      const deduped = prev.filter((n) => n.toLowerCase() !== name.toLowerCase());
      const next = [name, ...deduped].slice(0, MAX_RECENT);
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      } catch {
        // localStorage unavailable (private mode, etc.) - history just won't persist
      }
      return next;
    });
  }, []);

  return { recentSearches, addRecentSearch };
}
