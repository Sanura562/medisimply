export default function Disclaimer() {
  return (
    <div className="bg-tertiary-fixed/35 rounded-card p-4 flex items-start gap-3 mb-7">
      <span className="text-xl flex-shrink-0">⚠️</span>
      <p className="text-sm text-on-surface/80 leading-relaxed">
        <strong className="text-on-surface">Important:</strong> This tool
        explains medicine information in simple words. It is{" "}
        <strong className="text-on-surface">not medical advice</strong>. Always
        follow your doctor's instructions. |{" "}
        <span className="font-sinhala leading-sinhala">
          <strong className="text-on-surface">වැදගත්:</strong> මෙය වෛද්‍ය
          උපදෙස් නොවේ.
        </span>
      </p>
    </div>
  );
}
