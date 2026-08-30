import { useState } from "react";
import { useRecentSearches } from "./useRecentSearches";

// Shared by every entry point that can trigger a lookup (Home hero search,
// quick-search chips, recent-search clicks, the dedicated Search page) so
// there is exactly one place that owns the /lookup call and its state.
export function useMedicineSearch(apiUrl) {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");
  const { recentSearches, addRecentSearch } = useRecentSearches();

  async function handleSearch(medicineName) {
    if (!medicineName.trim()) {
      setError("Please enter a medicine name");
      return;
    }

    addRecentSearch(medicineName.trim());
    setLoading(true);
    setResults(null);
    setError("");

    try {
      const res = await fetch(`${apiUrl}/lookup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ medicine_name: medicineName }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Something went wrong");
      }

      const data = await res.json();
      setResults(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setResults(null);
    setError("");
  }

  return {
    loading,
    results,
    error,
    handleSearch,
    handleReset,
    recentSearches,
  };
}
