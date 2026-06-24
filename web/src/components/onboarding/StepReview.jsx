/** A plain-language summary row. */
function Row({ label, value }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-slate-100 py-2.5 last:border-0">
      <span className="text-xs font-semibold uppercase tracking-wide text-slate-400">
        {label}
      </span>
      <span className="max-w-[60%] text-right text-sm text-slate-800">{value}</span>
    </div>
  );
}

/** Step — read the plan back in plain language before committing. */
export default function StepReview({ plan }) {
  const sponsor = (plan.circle ?? [])[0] ?? {};
  const places = (plan.geofences ?? []).filter((p) => p.label?.trim());
  const placeText = places.length
    ? places.map((p) => p.label).join(", ")
    : "None selected";

  return (
    <div className="flex flex-col gap-5">
      <header>
        <h2 className="text-xl font-bold text-slate-900">Read it back</h2>
        <p className="mt-1 text-sm text-slate-600">
          This is your contract. It only runs the way you just described.
        </p>
      </header>

      <div className="rounded-2xl border border-slate-200 bg-white px-4 py-1">
        <Row label="Person" value={`${sponsor.name || "—"}${sponsor.role ? ` · ${sponsor.role}` : ""}`} />
        <Row label="Number" value={sponsor.contact || "—"} />
        <Row label="Places" value={placeText} />
        <Row label="Reach out at" value={plan.thresholds?.state || "—"} />
        <Row label="Sustained" value={`${plan.thresholds?.sustained_days ?? "—"} day(s)`} />
        <Row label="Nudge me first" value={plan.self_nudge_first ? "Yes" : "No"} />
        <Row label="Need risky place" value={plan.require_geofence ? "Yes" : "No"} />
      </div>

      <div>
        <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400">
          They'll receive
        </p>
        <p className="rounded-2xl bg-emerald-50 px-4 py-3 text-sm italic leading-relaxed text-emerald-900">
          “{plan.message_template || "—"}”
        </p>
      </div>

      <p className="rounded-xl bg-slate-50 px-4 py-3 text-xs leading-relaxed text-slate-500">
        In a crisis right now, call or text <strong>988</strong> (Suicide &amp;
        Crisis Lifeline) or <strong>1-800-662-HELP</strong> (SAMHSA). Radar is a
        safety net, not an emergency service.
      </p>
    </div>
  );
}
