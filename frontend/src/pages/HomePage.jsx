import { useNavigate, useOutletContext } from "react-router-dom";
import SearchBox from "../components/SearchBox.jsx";

const QUICK_SEARCHES = ["Augmentin", "Metformin", "Aspirin"];

export default function HomePage() {
  const navigate = useNavigate();
  const { apiUrl, handleSearch, recentSearches } = useOutletContext();

  // Same handleSearch the Search page uses - navigate afterwards so the
  // loading/results state (owned by RootLayout) is visible on /search.
  function runSearch(name) {
    handleSearch(name);
    navigate("/search");
  }

  return (
    <main className="max-w-[900px] mx-auto px-6 py-10">
      <div className="mb-8">
        <h1 className="font-display text-3xl sm:text-4xl font-bold text-on-surface mb-2">
          Welcome back, How can we help today?
        </h1>
        <p className="font-sinhala leading-sinhala text-lg text-primary-container">
          නැවත සාදරයෙන් පිළිගනිමු, අද අපිට ඔබට කෙසේ උදව් කළ හැකිද?
        </p>
      </div>

      <SearchBox onSearch={runSearch} apiUrl={apiUrl} variant="hero" />

      <div className="flex flex-wrap items-center gap-2 mb-10 -mt-3">
        <span className="text-sm text-on-surface/40 mr-1">Try:</span>
        {QUICK_SEARCHES.map((name) => (
          <button
            key={name}
            type="button"
            onClick={() => runSearch(name)}
            className="px-4 py-2 bg-surface-container-lowest border border-outline-variant/25 rounded-full text-sm font-semibold text-primary hover:bg-primary hover:text-white hover:border-primary transition-all"
          >
            {name}
          </button>
        ))}
      </div>

      <div className="grid sm:grid-cols-2 gap-5 mb-10">
        <div className="bg-surface-container-lowest rounded-card p-6">
          <h2 className="font-display text-lg font-bold text-on-surface mb-1">
            🕘 Recent Searches
          </h2>
          <p className="font-sinhala leading-sinhala text-[13px] text-on-surface/40 mb-4">
            ඔබගේ මෑත සෙවීම්
          </p>

          {recentSearches.length === 0 ? (
            <p className="text-sm text-on-surface/50">
              Medicines you search for will show up here.
            </p>
          ) : (
            <div className="flex flex-col gap-2">
              {recentSearches.map((name) => (
                <button
                  key={name}
                  type="button"
                  onClick={() => runSearch(name)}
                  className="text-left px-4 py-3 bg-surface-container-low rounded-xl text-on-surface font-medium hover:bg-primary/10 hover:text-primary transition-colors"
                >
                  {name}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="bg-surface-container-lowest rounded-card p-6">
          <h2 className="font-display text-lg font-bold text-on-surface mb-2">
            📖 Understand Your Meds
          </h2>
          <p className="text-sm text-on-surface/60 mb-1">
            MediSimply turns confusing medicine labels into simple English and
            Sinhala explanations — what a medicine is for, how to take it,
            and what to watch out for.
          </p>
          <p className="font-sinhala leading-sinhala text-sm text-on-surface/50 mb-4">
            සංකීර්ණ බෙහෙත් ලේබල සරල ඉංග්‍රීසි සහ සිංහල පැහැදිලි කිරීම් බවට
            හරවමු.
          </p>

          {/* Static illustrative example - not a live/interactive definition lookup */}
          <div className="inline-flex flex-col gap-0.5 bg-tertiary-fixed/30 rounded-xl px-4 py-3 -rotate-1 shadow-ambient text-sm">
            <span className="font-display font-bold text-primary">
              Metformin
            </span>
            <span className="text-on-surface/70">
              Helps control blood sugar levels.
            </span>
          </div>
        </div>
      </div>
    </main>
  );
}
