import { useOutletContext } from "react-router-dom";
import Welcome from "../components/Welcome.jsx";
import Disclaimer from "../components/Disclaimer.jsx";
import SearchBox from "../components/SearchBox.jsx";
import Loading from "../components/Loading.jsx";
import Results from "../components/Results.jsx";

export default function SearchPage() {
  const { apiUrl, loading, results, error, handleSearch, handleReset } =
    useOutletContext();

  return (
    <main className="max-w-[900px] mx-auto px-6 py-8">
      <Welcome />
      <Disclaimer />

      {!results && !loading && (
        <SearchBox onSearch={handleSearch} apiUrl={apiUrl} />
      )}

      {loading && <Loading />}

      {error && (
        <div className="bg-tertiary-fixed/35 rounded-card p-5 mb-7 text-on-surface font-medium">
          {error}
        </div>
      )}

      {results && <Results data={results} onReset={handleReset} />}
    </main>
  );
}
