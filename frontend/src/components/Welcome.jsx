export default function Welcome() {
  return (
    <div className="bg-surface-container-lowest rounded-card p-7 mb-7 flex items-center gap-5">
      <div className="text-5xl flex-shrink-0">👴🏽</div>
      <div>
        <h2 className="font-display text-xl font-bold text-primary mb-1">
          Understand Your Medicine
        </h2>
        <p className="text-base text-on-surface/60">
          Type the name of any medicine. We'll explain it simply in English and
          Sinhala.
        </p>
        <p className="font-sinhala leading-sinhala text-[15px] text-primary-container mt-1">
          ඕනෑම බෙහෙතක නම ටයිප් කරන්න. අපි එය ඉංග්‍රීසි සහ සිංහලෙන් සරලව පැහැදිලි
          කරමු.
        </p>
      </div>
    </div>
  );
}
