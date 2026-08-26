// Only two tonal families in this system: calm (primary) for everyday
// informational sections, and warning (tertiary/gold, used sparingly) for
// the sections that are genuinely about risk - warnings and contraindications.
const toneMap = {
  calm: { chip: "bg-primary/10 text-primary", sinhala: "bg-primary/8 text-primary" },
  warning: {
    chip: "bg-tertiary-fixed/50 text-on-surface",
    sinhala: "bg-tertiary-fixed/25 text-on-surface",
  },
};

export default function ResultCard({ icon, tone, title, titleSi, data }) {
  const { chip, sinhala } = toneMap[tone] || toneMap.calm;

  return (
    <div className="bg-surface-container-lowest rounded-card mb-5 overflow-hidden px-6 py-5">
      {/* Header - no divider line beneath it; the gap to the body below is
          pure vertical whitespace, per the No-Line Rule. */}
      <div className="flex items-center gap-3 mb-4">
        <div
          className={`w-10 h-10 rounded-xl ${chip} flex items-center justify-center text-xl flex-shrink-0`}
        >
          {icon}
        </div>
        <div>
          <div className="font-display font-bold text-on-surface">{title}</div>
          <div className="font-sinhala leading-sinhala text-sm text-on-surface/50">
            {titleSi}
          </div>
        </div>
      </div>

      {/* Body */}
      <p className="text-lg leading-relaxed text-on-surface mb-4">
        {data.english}
      </p>
      <div
        className={`font-sinhala leading-sinhala text-lg p-4 rounded-lg ${sinhala}`}
      >
        {data.sinhala}
      </div>
    </div>
  );
}
