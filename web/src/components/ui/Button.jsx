const VARIANTS = {
  primary: "bg-emerald-600 text-white hover:bg-emerald-700 disabled:bg-slate-300",
  ghost: "text-slate-500 hover:text-slate-800 disabled:text-slate-300",
  outline:
    "border border-slate-300 text-slate-700 hover:bg-slate-50 disabled:text-slate-300",
};

/** App button with a few variants, used across the flow. */
export default function Button({ variant = "primary", className = "", ...props }) {
  return (
    <button
      type="button"
      className={`rounded-full px-5 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed ${VARIANTS[variant]} ${className}`}
      {...props}
    />
  );
}
