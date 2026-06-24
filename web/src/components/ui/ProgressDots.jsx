/** Step progress dots for the onboarding wizard. */
export default function ProgressDots({ count, current }) {
  return (
    <div className="flex items-center gap-1.5">
      {Array.from({ length: count }).map((_, i) => (
        <span
          key={i}
          className={`h-1.5 rounded-full transition-all ${
            i === current ? "w-6 bg-emerald-600" : "w-1.5 bg-slate-300"
          }`}
        />
      ))}
    </div>
  );
}
