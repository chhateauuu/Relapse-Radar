/** A labelled form field with an optional hint and inline error. */
export default function Field({ label, hint, error, children }) {
  return (
    <label className="block">
      {label && (
        <span className="block text-sm font-semibold text-slate-800">{label}</span>
      )}
      {hint && <span className="mb-1.5 block text-xs text-slate-500">{hint}</span>}
      {children}
      {error && <span className="mt-1 block text-xs text-rose-500">{error}</span>}
    </label>
  );
}

export const inputClass =
  "mt-1 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-100";
