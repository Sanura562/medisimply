import ResultCard from "./ResultCard";

// Three-way, calm/tonal treatment for where the grounding data came from.
// Gold (tertiary_fixed) is reserved for the one genuinely "not verified"
// state, per the design system's guidance to use gold sparingly for
// warnings/critical notes - the other two stay in the primary (green) family
// since they're both real, verified data, just from different places.
const DATA_SOURCE_BADGES = {
  local_verified: {
    label: "✓ Verified Source",
    className: "bg-primary/10 text-primary",
  },
  live_mcp_lookup: {
    label: "✓ Live Verified Lookup",
    className: "bg-primary-fixed/50 text-primary",
  },
  ai_knowledge_only: {
    label: "⚠ AI Knowledge Only",
    className: "bg-tertiary-fixed/50 text-on-surface",
  },
};

export default function Results({ data, onReset }) {
  const fallbackImg =
    "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect fill='%23f5f3ee' width='100' height='100' rx='16'/><text x='50' y='60' text-anchor='middle' font-size='40'>💊</text></svg>";

  const badge =
    DATA_SOURCE_BADGES[data.data_source] ||
    (data.found_in_database
      ? DATA_SOURCE_BADGES.local_verified
      : DATA_SOURCE_BADGES.ai_knowledge_only);

  return (
    <div className="animate-fadeUp">
      {/* Drug header with image */}
      <div className="bg-surface-container-lowest rounded-card p-6 mb-5 flex items-center gap-6">
        <img
          src={data.image_url || fallbackImg}
          alt={data.medicine_name}
          className="w-24 h-24 rounded-xl object-cover bg-surface-container-low flex-shrink-0"
          onError={(e) => {
            e.target.src = fallbackImg;
          }}
        />
        <div>
          <h2 className="font-display text-2xl font-bold text-primary">
            {data.medicine_name}
          </h2>
          {data.composition && (
            <p className="text-[15px] text-on-surface/50">
              💉 {data.composition}
            </p>
          )}
          {data.manufacturer && (
            <p className="text-sm text-on-surface/50">
              🏭 {data.manufacturer}
            </p>
          )}
          <span
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold mt-2 ${badge.className}`}
          >
            {badge.label}
          </span>
        </div>
      </div>

      {/* Four section cards */}
      <ResultCard
        icon="💊"
        tone="calm"
        title="What This Medicine Does"
        titleSi="මෙම බෙහෙත කරන දේ"
        data={data.what_it_does}
      />
      <ResultCard
        icon="⏰"
        tone="calm"
        title="How To Take This Medicine"
        titleSi="මෙම බෙහෙත ගන්නේ කෙසේද"
        data={data.how_to_take}
      />
      <ResultCard
        icon="⚡"
        tone="warning"
        title="Warnings & Side Effects"
        titleSi="අනතුරු ඇඟවීම් සහ අතුරු ආබාධ"
        data={data.warnings_and_side_effects}
      />
      <ResultCard
        icon="🚫"
        tone="warning"
        title="Who Should NOT Take This"
        titleSi="මෙම බෙහෙත නොගත යුත්තේ කාටද"
        data={data.who_should_not_take}
      />

      {/* Key Points */}
      {data.key_points?.length > 0 && (
        <div className="bg-surface-container-lowest rounded-card p-6 mb-5">
          <div className="font-display font-bold text-on-surface mb-4">
            📌 Key Points to Remember
          </div>
          {data.key_points.map((point, i) => (
            <div key={i} className="flex items-start gap-3 mb-2.5">
              <div className="w-6 h-6 rounded-full bg-primary text-white text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                {i + 1}
              </div>
              <span className="text-on-surface/80">{point}</span>
            </div>
          ))}
        </div>
      )}

      {/* RAG Sources - shows WHERE the information came from */}
      {data.rag_sources?.length > 0 && (
        <div className="bg-surface-container-lowest rounded-card p-6 mb-5">
          <div className="font-display font-bold text-on-surface mb-1">
            📚 Information Sources
          </div>
          <p className="text-sm text-on-surface/50 mb-4">
            The AI used these verified passages to generate the simplified
            information above.
          </p>
          {data.rag_sources.map((src, i) => (
            <div key={i} className="mb-3 p-3 bg-surface-container-low rounded-lg">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-bold text-primary bg-primary/10 px-2 py-0.5 rounded-full">
                  {src.drug_name}
                </span>
                <span className="text-xs text-on-surface/50">
                  {src.section.replace("_", " ")}
                </span>
                <span className="text-xs text-on-surface/30">•</span>
                <span className="text-xs text-on-surface/50">
                  {src.source}
                </span>
              </div>
              <p className="text-sm text-on-surface/70 leading-relaxed">
                {src.text}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Source + Reset */}
      <p className="text-center text-sm text-on-surface/50 mb-4">
        🔍 Source: {data.source}
      </p>
      <div className="text-center mb-5">
        <button
          onClick={onReset}
          className="px-7 py-3 bg-surface-container-lowest text-primary border-2 border-primary/40 rounded-xl font-semibold hover:bg-primary hover:text-white hover:border-primary transition-all"
        >
          🔍 Search Another Medicine
        </button>
      </div>
    </div>
  );
}
