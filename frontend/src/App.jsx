import { useState } from "react";
import Header from "./components/Header.jsx";
import Welcome from "./components/Welcome";
import Disclaimer from "./components/Disclaimer";
import SearchBox from "./components/SearchBox";
import Loading from "./components/Loading";
import Results from "./components/Results";

const API_URL = "http://127.0.0.1:8000";

export default function App() {
  // State = data that changes over time (like variables in Java that trigger UI updates)
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");
  const [dbCount, setDbCount] = useState(0);

  // This function runs when user clicks "Explain Medicine"
  async function handleSearch(medicineName) {
    if (!medicineName.trim()) {
      setError("Please enter a medicine name");
      return;
    }

    setLoading(true);
    setResults(null);
    setError("");

    try {
      const res = await fetch(`${API_URL}/lookup`, {
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

  return (
    <div className="min-h-screen bg-surface">
      <Header dbCount={dbCount} setDbCount={setDbCount} apiUrl={API_URL} />

      <main className="max-w-[900px] mx-auto px-6 py-8">
        <Welcome />
        <Disclaimer />

        {!results && !loading && (
          <SearchBox onSearch={handleSearch} apiUrl={API_URL} />
        )}

        {loading && <Loading />}

        {error && (
          <div className="bg-tertiary-fixed/35 rounded-card p-5 mb-7 text-on-surface font-medium">
            {error}
          </div>
        )}

        {results && <Results data={results} onReset={handleReset} />}
      </main>

      <footer className="max-w-[900px] mx-auto px-6 py-8 text-center text-sm text-on-surface/50">
        MediSimply — FYP by Sanura Wijerathne | Supervised by Ms. M.F.F. Nuha |
        Staffordshire University
      </footer>
    </div>
  );
}
