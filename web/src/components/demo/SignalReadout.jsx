import { featureLabel, formatFeature } from "../../lib/demoData";

/**
 * "Contributing signals" — which parts of Maya's rhythm have drifted, straight
 * from RiskAssessment.drivers. Each driver carries a signed z and a direction;
 * we render it as a plain, non-clinical readout with the live value alongside.
 */
export default function SignalReadout({ drivers, record }) {
  if (!drivers || drivers.length === 0) {
    return (
      <div className="rounded-2xl bg-white px-4 py-3 text-sm text-slate-500 ring-1 ring-slate-100">
        Every signal is inside your normal range.
      </div>
    );
  }

  return (
    <div className="rounded-2xl bg-white px-4 py-3 ring-1 ring-slate-100">
      <p className="mb-2 text-xs font-semibold text-slate-500">What's driving it</p>
      <ul className="flex flex-col gap-2">
        {drivers.map((d) => {
          const magnitude = Math.min(1, Math.abs(d.z) / 4);
          const down = d.direction === "down";
          return (
            <li key={d.feature} className="flex items-center gap-3">
              <span
                className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-sm font-bold"
                style={{
                  background: `rgba(220,38,38,${0.1 + magnitude * 0.25})`,
                  color: "#b91c1c",
                }}
                aria-hidden
              >
                {down ? "↓" : "↑"}
              </span>
              <span className="flex-1 text-sm font-medium text-slate-700">
                {featureLabel(d.feature)}
              </span>
              {record && (
                <span className="text-sm font-semibold tabular-nums text-slate-500">
                  {formatFeature(d.feature, record.features[d.feature])}
                </span>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
