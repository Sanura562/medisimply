export default function Welcome() {
  return (
    <div className="bg-white rounded-2xl p-7 mb-7 shadow-sm border border-gray-100 flex items-center gap-5">
      <div className="text-5xl flex-shrink-0">👴🏽</div>
      <div>
        <h2 className="text-xl font-bold text-[#0D4A35] mb-1">
          Understand Your Medicine
        </h2>
        <p className="text-base text-gray-500">
          Type the name of any medicine. We'll explain it simply in English and
          Sinhala.
        </p>
        <p className="font-['Noto_Sans_Sinhala'] text-[15px] text-[#1A6B4F] mt-1">
          ඕනෑම බෙහෙතක නම ටයිප් කරන්න. අපි එය ඉංග්‍රීසි සහ සිංහලෙන් සරලව පැහැදිලි
          කරමු.
        </p>
      </div>
    </div>
  );
}
