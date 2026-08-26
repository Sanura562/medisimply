import { useEffect } from "react";

export default function Header({ dbCount, setDbCount, apiUrl }) {
  useEffect(() => {
    // useEffect runs when the component first appears (like @PostConstruct in Spring)
    fetch(apiUrl)
      .then((res) => res.json())
      .then((data) => setDbCount(data.databases?.total || 0))
      .catch(() => setDbCount(0));
  }, [apiUrl, setDbCount]);

  return (
    <header className="sticky top-0 z-50 backdrop-blur-md bg-gradient-to-r from-primary/95 to-primary-container/95">
      <div className="max-w-[900px] mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 bg-white/15 rounded-xl flex items-center justify-center text-2xl">
            💊
          </div>
          <div>
            <h1 className="font-display text-xl font-bold text-white">
              MediSimply
            </h1>
            <p className="text-xs text-white/60">Medicine Made Simple</p>
          </div>
        </div>
        <div className="px-4 py-1.5 bg-white/10 rounded-full text-sm text-white/80">
          {dbCount > 0
            ? `${dbCount.toLocaleString()} medicines`
            : "Connecting..."}
        </div>
      </div>
    </header>
  );
}
