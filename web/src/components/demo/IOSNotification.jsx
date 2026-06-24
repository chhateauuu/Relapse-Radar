/**
 * An iOS-style notification banner, shown at the top of Maya's phone when her
 * line first drifts (AMBER). Concise and formatted like a real push banner.
 */
export default function IOSNotification({
  appName = "Relapse Radar",
  time = "now",
  title,
  body,
}) {
  return (
    <div className="ios-notif flex items-start gap-2.5 rounded-2xl bg-white/85 px-3 py-2.5 shadow-lg ring-1 ring-black/5 backdrop-blur">
      <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-[8px] bg-emerald-500 text-white">
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden>
          <path d="M12 12 L19 7" />
          <circle cx="12" cy="12" r="1.6" fill="currentColor" stroke="none" />
          <path d="M12 5 a7 7 0 0 1 7 7" />
          <path d="M12 8.5 a3.5 3.5 0 0 1 3.5 3.5" />
        </svg>
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            {appName}
          </span>
          <span className="ml-auto shrink-0 text-[11px] text-slate-400">{time}</span>
        </div>
        <p className="mt-0.5 text-sm font-semibold leading-tight text-slate-900">{title}</p>
        <p className="text-sm leading-snug text-slate-600">{body}</p>
      </div>
    </div>
  );
}
