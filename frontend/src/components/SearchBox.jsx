import { useState, useEffect, useRef } from "react";

export default function SearchBox({ onSearch, apiUrl }) {
  const [query, setQuery] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [showDrop, setShowDrop] = useState(false);
  const timerRef = useRef(null);

  // Live search - debounced (waits 300ms after user stops typing)
  useEffect(() => {
    if (query.length < 2) return;

    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(async () => {
      try {
        const res = await fetch(
          `${apiUrl}/search/${encodeURIComponent(query)}`,
        );
        const data = await res.json();
        setSuggestions(data);
        setShowDrop(data.length > 0);
      } catch {
        setShowDrop(false);
      }
    }, 300);
  }, [query, apiUrl]);

  function handleSelect(name) {
    setQuery(name);
    setShowDrop(false);
    onSearch(name);
  }

  function handleSubmit(e) {
    e.preventDefault();
    setShowDrop(false);
    onSearch(query);
  }

  return (
    <div className="bg-surface-container-lowest rounded-card p-7 mb-7">
      <div className="font-display text-lg font-bold text-on-surface mb-1">
        🔍 Enter Medicine Name
      </div>
      <p className="font-sinhala leading-sinhala text-[15px] text-on-surface/50 mb-4">
        බෙහෙතේ නම ඇතුළත් කරන්න
      </p>

      <form onSubmit={handleSubmit} className="flex gap-3 relative">
        <input
          type="text"
          value={query}
          onChange={(e) => {
            const val = e.target.value;
            setQuery(val);
            if (val.length < 2) {
              setSuggestions([]);
              setShowDrop(false);
            }
          }}
          placeholder="e.g. Augmentin, Metformin, Aspirin..."
          className="flex-1 px-5 py-4 border-2 border-transparent rounded-xl text-xl text-on-surface bg-surface-container-low focus:outline-none focus:border-primary/40 focus:bg-surface-container-lowest transition-all placeholder:text-on-surface/30 placeholder:text-lg"
        />
        <button
          type="submit"
          className="min-h-14 px-8 bg-[linear-gradient(135deg,var(--color-primary),var(--color-primary-container))] text-white rounded-cta text-lg font-bold hover:-translate-y-0.5 hover:shadow-ambient active:translate-y-0 transition-all whitespace-nowrap"
        >
          ✨ Explain
        </button>

        {/* Live search dropdown - the one element here that actually floats,
            so it gets the ambient shadow + a ghost border for definition
            (No-Line Rule alone isn't enough contrast on a floating overlay). */}
        {showDrop && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-surface-container-lowest border border-outline-variant/15 rounded-card shadow-ambient max-h-[350px] overflow-y-auto z-50">
            {suggestions.map((s, i) => (
              <div
                key={i}
                onClick={() => handleSelect(s.name)}
                className="px-4 py-3 flex items-center gap-3 cursor-pointer hover:bg-surface-container-low"
              >
                <img
                  src={s.image_url}
                  alt={s.name}
                  className="w-12 h-12 rounded-lg object-cover bg-surface-container-low flex-shrink-0"
                  onError={(e) => {
                    e.target.src =
                      "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'><rect fill='%23f5f3ee' width='48' height='48' rx='8'/><text x='24' y='30' text-anchor='middle' font-size='20'>💊</text></svg>";
                  }}
                />
                <div className="min-w-0">
                  <div className="font-semibold text-on-surface truncate">
                    {s.name}
                  </div>
                  <div className="text-sm text-on-surface/50 truncate">
                    {s.composition}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </form>
    </div>
  );
}
