import ResultCard from "./ResultCard";

export default function Results({ data, onReset }) {
  const fallbackImg =
    "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect fill='%23E8F5EE' width='100' height='100' rx='16'/><text x='50' y='60' text-anchor='middle' font-size='40'>💊</text></svg>";

  return (
    <div className="animate-fadeUp">
      {/* Drug header with image */}
      <div className="bg-white rounded-2xl p-6 mb-5 shadow-sm border border-gray-100 flex items-center gap-6">
        <img
          src={data.image_url || fallbackImg}
          alt={data.medicine_name}
          className="w-24 h-24 rounded-xl object-cover bg-gray-100 flex-shrink-0 border border-gray-200"
          onError={(e) => {
            e.target.src = fallbackImg;
          }}
        />
        <div>
          <h2 className="text-2xl font-bold text-[#0D4A35]">
            {data.medicine_name}
          </h2>
          {data.composition && (
            <p className="text-[15px] text-gray-400">💉 {data.composition}</p>
          )}
          {data.manufacturer && (
            <p className="text-sm text-gray-400">🏭 {data.manufacturer}</p>
          )}
          <span
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold mt-2 ${
              data.found_in_database
                ? "bg-[#E8F5EE] text-[#0D4A35]"
                : "bg-[#FFF3CD] text-[#664D03]"
            }`}
          >
            {data.found_in_database
              ? "✅ Verified Source"
              : "⚠️ AI Knowledge Only"}
          </span>
        </div>
      </div>

      {/* Four section cards */}
      <ResultCard
        icon="💊"
        color="blue"
        title="What This Medicine Does"
        titleSi="මෙම බෙහෙත කරන දේ"
        data={data.what_it_does}
      />
      <ResultCard
        icon="⏰"
        color="green"
        title="How To Take This Medicine"
        titleSi="මෙම බෙහෙත ගන්නේ කෙසේද"
        data={data.how_to_take}
      />
      <ResultCard
        icon="⚡"
        color="orange"
        title="Warnings & Side Effects"
        titleSi="අනතුරු ඇඟවීම් සහ අතුරු ආබාධ"
        data={data.warnings_and_side_effects}
      />
      <ResultCard
        icon="🚫"
        color="red"
        title="Who Should NOT Take This"
        titleSi="මෙම බෙහෙත නොගත යුත්තේ කාටද"
        data={data.who_should_not_take}
      />

      {/* Key Points */}
      {data.key_points?.length > 0 && (
        <div className="bg-white rounded-2xl p-6 mb-5 shadow-sm border border-gray-100">
          <div className="font-bold text-gray-800 mb-4">
            📌 Key Points to Remember
          </div>
          {data.key_points.map((point, i) => (
            <div key={i} className="flex items-start gap-3 mb-2.5">
              <div className="w-6 h-6 rounded-full bg-[#1A6B4F] text-white text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                {i + 1}
              </div>
              <span className="text-gray-700">{point}</span>
            </div>
          ))}
        </div>
      )}

      {/* RAG Sources - shows WHERE the information came from */}
      {data.rag_sources?.length > 0 && (
        <div className="bg-white rounded-2xl p-6 mb-5 shadow-sm border border-gray-100">
          <div className="font-bold text-gray-800 mb-1">
            📚 Information Sources
          </div>
          <p className="text-sm text-gray-400 mb-4">
            The AI used these verified passages to generate the simplified
            information above.
          </p>
          {data.rag_sources.map((src, i) => (
            <div
              key={i}
              className="mb-3 p-3 bg-gray-50 rounded-lg border border-gray-100"
            >
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-bold text-[#1A6B4F] bg-[#E8F5EE] px-2 py-0.5 rounded-full">
                  {src.drug_name}
                </span>
                <span className="text-xs text-gray-400">
                  {src.section.replace("_", " ")}
                </span>
                <span className="text-xs text-gray-300">•</span>
                <span className="text-xs text-gray-400">{src.source}</span>
              </div>
              <p className="text-sm text-gray-600 leading-relaxed">
                {src.text}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Source + Reset */}
      <p className="text-center text-sm text-gray-400 mb-4">
        🔍 Source: {data.source}
      </p>
      <div className="text-center mb-5">
        <button
          onClick={onReset}
          className="px-7 py-3 bg-white text-[#1A6B4F] border-2 border-[#1A6B4F] rounded-xl font-semibold hover:bg-[#1A6B4F] hover:text-white transition-all"
        >
          🔍 Search Another Medicine
        </button>
      </div>
    </div>
  );
}
