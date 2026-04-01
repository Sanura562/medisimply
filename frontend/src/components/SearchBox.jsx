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
    <div className="bg-white rounded-2xl p-7 mb-7 shadow-sm border border-gray-100">
      <div className="text-lg font-bold text-gray-800 mb-1">
        🔍 Enter Medicine Name
      </div>
      <p className="font-['Noto_Sans_Sinhala'] text-[15px] text-gray-400 mb-4">
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
          className="flex-1 px-5 py-4 border-2 border-gray-200 rounded-xl text-xl text-gray-800 bg-[#FAFCFB] focus:outline-none focus:border-[#1A6B4F] focus:ring-4 focus:ring-[#1A6B4F]/10 focus:bg-white transition-all placeholder:text-gray-300 placeholder:text-lg"
        />
        <button
          type="submit"
          className="px-8 py-4 bg-gradient-to-r from-[#1A6B4F] to-[#0D4A35] text-white rounded-xl text-lg font-bold hover:-translate-y-0.5 hover:shadow-lg active:translate-y-0 transition-all whitespace-nowrap"
        >
          ✨ Explain
        </button>

        {/* Live search dropdown */}
        {showDrop && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-white border border-gray-200 rounded-xl shadow-xl max-h-[350px] overflow-y-auto z-50">
            {suggestions.map((s, i) => (
              <div
                key={i}
                onClick={() => handleSelect(s.name)}
                className="px-4 py-3 flex items-center gap-3 cursor-pointer hover:bg-[#E8F5EE] border-b border-gray-50 last:border-0"
              >
                <img
                  src={s.image_url}
                  alt={s.name}
                  className="w-12 h-12 rounded-lg object-cover bg-gray-100 flex-shrink-0"
                  onError={(e) => {
                    e.target.src =
                      "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 48 48'><rect fill='%23E8F5EE' width='48' height='48' rx='8'/><text x='24' y='30' text-anchor='middle' font-size='20'>💊</text></svg>";
                  }}
                />
                <div className="min-w-0">
                  <div className="font-semibold text-gray-800 truncate">
                    {s.name}
                  </div>
                  <div className="text-sm text-gray-400 truncate">
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
