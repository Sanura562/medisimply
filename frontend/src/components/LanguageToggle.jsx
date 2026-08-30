import { useState } from "react";

// Visual-only toggle: the app's bilingual output already happens per-result
// (English + Sinhala shown together), so this doesn't drive a translation
// layer - it just indicates which language the user prefers to read first.
export default function LanguageToggle() {
  const [lang, setLang] = useState("en");

  return (
    <div className="flex items-center bg-white/10 rounded-full p-1 text-xs font-bold">
      <button
        type="button"
        onClick={() => setLang("en")}
        aria-pressed={lang === "en"}
        className={`px-3 py-1 rounded-full transition-colors ${
          lang === "en" ? "bg-white text-primary" : "text-white/70"
        }`}
      >
        EN
      </button>
      <button
        type="button"
        onClick={() => setLang("si")}
        aria-pressed={lang === "si"}
        className={`font-sinhala px-3 py-1 rounded-full transition-colors ${
          lang === "si" ? "bg-white text-primary" : "text-white/70"
        }`}
      >
        සිං
      </button>
    </div>
  );
}
