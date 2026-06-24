/**
 * The sponsor's phone — the second screen. Calm and silent by default; it only
 * ever lights up when Maya's *own* pre-written plan fires. When it does, it
 * shows the message she wrote herself — nothing else ever leaves her device.
 */
export default function SponsorPhone({ event, contact = "+15555550123", userName = "Maya" }) {
  if (!event) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 px-6 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-slate-100">
          <span className="h-3 w-3 rounded-full bg-emerald-500" />
        </div>
        <p className="text-sm font-semibold text-slate-700">All quiet</p>
        <p className="text-xs leading-relaxed text-slate-500">
          You're {userName}'s person. You'll only hear from Relapse Radar if the
          plan {userName} wrote says it's time.
        </p>
      </div>
    );
  }

  const time = formatTime(event.sent_at);

  return (
    <div className="flex h-full flex-col gap-4 px-5 py-5">
      <div className="rounded-2xl bg-red-50 px-4 py-3 ring-1 ring-red-200">
        <p className="text-xs font-semibold uppercase tracking-wide text-red-600">
          Relapse Radar · {time}
        </p>
        <p className="mt-1 text-sm font-semibold text-red-900">
          {userName} asked to be checked on if things looked rough. Now's the
          time — call {userName}.
        </p>
      </div>

      <div className="rounded-2xl bg-white px-4 py-3 ring-1 ring-slate-200">
        <p className="mb-1 text-xs font-semibold text-slate-400">
          The message {userName} wrote for this moment
        </p>
        <p className="text-sm italic leading-relaxed text-slate-700">
          “{event.message}”
        </p>
      </div>

      <a
        href={`tel:${contact}`}
        className="mt-auto flex items-center justify-center gap-2 rounded-full bg-emerald-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-700"
      >
        Call {userName}
      </a>
    </div>
  );
}

function formatTime(iso) {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  } catch {
    return "";
  }
}
