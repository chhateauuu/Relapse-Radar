import { styleFor } from "./stateStyles";

/**
 * The big GREEN / AMBER / RED state indicator — calm, strengths-based.
 * It's "your line," never a shaming relapse score.
 */
export default function StateIndicator({ state, risk, day, soberDays }) {
  const s = styleFor(state);
  return (
    <div
      className={`flex items-center gap-4 rounded-2xl px-4 py-3 ring-1 ${s.bg} ${s.ring}`}
    >
      <div
        className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full"
        style={{ background: s.soft }}
      >
        <span
          className="h-6 w-6 rounded-full"
          style={{ background: s.color, boxShadow: `0 0 0 5px ${s.soft}` }}
        />
      </div>
      <div className="min-w-0 flex-1">
        <p className={`text-base font-bold ${s.text}`}>{s.label}</p>
        <p className="text-xs text-slate-500">
          Day {day} · {soberDays} days sober
        </p>
      </div>
      <div className="text-right">
        <p className="text-[10px] uppercase tracking-wide text-slate-400">Your line</p>
        <p className="text-lg font-bold tabular-nums" style={{ color: s.color }}>
          {Math.round(risk * 100)}
        </p>
      </div>
    </div>
  );
}
