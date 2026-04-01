const colorMap = {
  blue: "bg-blue-50",
  green: "bg-emerald-50",
  orange: "bg-orange-50",
  red: "bg-red-50",
};

export default function ResultCard({ icon, color, title, titleSi, data }) {
  return (
    <div className="bg-white rounded-2xl mb-5 shadow-sm border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 flex items-center gap-3 border-b border-gray-100">
        <div
          className={`w-10 h-10 rounded-xl ${colorMap[color]} flex items-center justify-center text-xl`}
        >
          {icon}
        </div>
        <div>
          <div className="font-bold text-gray-800">{title}</div>
          <div className="font-['Noto_Sans_Sinhala'] text-sm text-gray-400">
            {titleSi}
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="px-6 py-5">
        <p className="text-lg leading-relaxed text-gray-800 mb-4">
          {data.english}
        </p>
        <div className="font-['Noto_Sans_Sinhala'] text-lg leading-loose text-[#0D4A35] bg-[#E8F5EE] p-4 rounded-xl border-l-4 border-[#1A6B4F]">
          {data.sinhala}
        </div>
      </div>
    </div>
  );
}
