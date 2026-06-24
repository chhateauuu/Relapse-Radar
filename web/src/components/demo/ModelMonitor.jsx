import { useMemo } from "react";

/**
 * "Backend AI Model" — a monitor screen beside the phones that visualizes the
 * model processing each day's FeatureRecord: the assess pipeline, the z-scores
 * vs the personal baseline, the fused risk, the change-point, and the rules.
 *
 * The z-score baseline mirrors the backend's population baseline (brain/scorer.py)
 * so the numbers shown match what the model actually computed.
 */
const MODEL_BASELINE = {
  sleep_hours: [7.2, 0.5],
  late_night_min: [8.0, 8.0],
  screen_time_min: [210.0, 30.0],
  unlocks: [78.0, 12.0],
  outgoing_msgs: [18.0, 4.0],
  unique_contacts: [6.0, 1.5],
  location_entropy: [1.45, 0.2],
  time_at_home_pct: [0.55, 0.08],
  dwell_flagged_min: [0.0, 4.0],
  steps: [5200.0, 700.0],
};

const RISK_UP = {
  sleep_hours: false,
  late_night_min: true,
  screen_time_min: true,
  unlocks: true,
  outgoing_msgs: false,
  unique_contacts: false,
  location_entropy: false,
  time_at_home_pct: true,
  dwell_flagged_min: true,
  steps: false,
};

const STAGES = ["ingest", "z-score", "fusion", "change-point", "state"];

const STATE_COLOR = { GREEN: "#34d399", AMBER: "#fbbf24", RED: "#fb7185" };

const TONE_CLASS = {
  dim: "text-emerald-300/50",
  base: "text-emerald-200/80",
  label: "text-emerald-300/70",
  warn: "text-amber-300",
  cyan: "text-cyan-300",
  green: "text-emerald-400",
  amber: "text-amber-300",
  red: "text-rose-400",
};

const z = (value, [mean, spread]) => (spread ? (value - mean) / spread : 0);
const fix = (n, d = 1) => Number(n).toFixed(d);

function stateTone(state) {
  return state === "RED" ? "red" : state === "AMBER" ? "amber" : "green";
}

function buildLog(record, assessment, timeline) {
  const f = record.features ?? {};
  const lines = [];
  lines.push({ tone: "dim", text: `$ POST /assess  user=${record.user_id} day=${record.day}` });
  lines.push({ tone: "dim", text: "  ├─ ingest: 10 passive signals" });

  const zs = Object.entries(MODEL_BASELINE)
    .map(([k, base]) => ({ k, z: z(f[k], base) }))
    .sort((a, b) => Math.abs(b.z) - Math.abs(a.z));

  lines.push({ tone: "label", text: "  ├─ z-score vs personal baseline:" });
  zs.slice(0, 5).forEach(({ k, z: zv }) => {
    const directional = RISK_UP[k] ? zv : -zv; // how far the risky way
    const arrow = zv >= 0 ? "▲" : "▼";
    const sign = zv >= 0 ? "+" : "";
    lines.push({
      tone: directional >= 1.5 ? "warn" : "base",
      text: `  │   ${k.padEnd(16)} ${sign}${fix(zv, 1)}σ ${arrow}`,
    });
  });

  lines.push({ tone: "cyan", text: `  ├─ fusion model → risk = ${fix(assessment.risk, 3)}` });

  if (assessment.changepoint?.active && assessment.changepoint.started_day != null) {
    lines.push({
      tone: "dim",
      text: `  ├─ change-point: drift since day ${assessment.changepoint.started_day}`,
    });
  }

  lines.push({ tone: stateTone(assessment.state), text: `  └─ state = ${assessment.state}` });

  (timeline ?? [])
    .filter((e) => e.day === record.day)
    .forEach((e) => {
      if (e.type === "self_nudge") {
        lines.push({ tone: "amber", text: "  ! rules: self-nudge → check-in sent to user" });
      }
      if (e.type === "notify_circle") {
        lines.push({ tone: "red", text: `  ! rules: ${assessment.state} sustained → notify_circle` });
        lines.push({ tone: "red", text: `  → SMS dispatched to ${e.recipient} via ${e.channel}` });
      }
    });

  return lines;
}

export default function ModelMonitor({ record, assessment, timeline, source }) {
  const lines = useMemo(
    () => buildLog(record, assessment, timeline),
    [record, assessment, timeline]
  );
  const risk = assessment.risk ?? 0;
  const color = STATE_COLOR[assessment.state] ?? STATE_COLOR.GREEN;

  // Which pipeline stage "lands" the current state, for the final accent.
  return (
    <div className="flex flex-col items-center">
      <div className="monitor-screen flex w-[460px] max-w-[88vw] flex-col">
        {/* title bar */}
        <div className="flex items-center gap-2 border-b border-emerald-900/40 bg-black/40 px-4 py-2.5">
          <span className="flex gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-rose-500/80" />
            <span className="h-2.5 w-2.5 rounded-full bg-amber-400/80" />
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/80" />
          </span>
          <span className="ml-2 font-mono text-xs text-emerald-300">relapse-radar · brain.assess</span>
          <span className="ml-auto flex items-center gap-1.5 font-mono text-[11px] text-emerald-400">
            <span className={`h-1.5 w-1.5 rounded-full ${source === "api" ? "bg-emerald-400 monitor-pulse" : "bg-slate-500"}`} />
            {source === "api" ? "POST /assess · live" : "offline"}
          </span>
        </div>

        {/* risk gauge + state */}
        <div className="flex items-center gap-3 border-b border-emerald-900/30 px-4 py-3">
          <div className="flex-1">
            <div className="flex justify-between font-mono text-[10px] text-emerald-300/70">
              <span>risk</span>
              <span>{Math.round(risk * 100)}%</span>
            </div>
            <div className="mt-1 h-2 overflow-hidden rounded-full bg-emerald-950">
              <div
                className="h-2 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, risk * 100)}%`, background: color }}
              />
            </div>
          </div>
          <span
            className="rounded px-2 py-1 font-mono text-[11px] font-bold"
            style={{ color, background: `${color}22` }}
          >
            {assessment.state}
          </span>
        </div>

        {/* pipeline */}
        <div className="flex flex-wrap items-center gap-1 px-4 py-3 font-mono text-[10px]">
          {STAGES.map((s, i) => (
            <span key={s} className="flex items-center gap-1">
              <span
                className="rounded px-1.5 py-0.5"
                style={
                  i === STAGES.length - 1
                    ? { color, background: `${color}22` }
                    : { color: "#67e8f9", background: "rgba(34,211,238,0.1)" }
                }
              >
                {s}
              </span>
              {i < STAGES.length - 1 && <span className="text-emerald-700">›</span>}
            </span>
          ))}
        </div>

        {/* console — remounts per day so the log re-streams */}
        <div
          key={record.day}
          className="flex-1 overflow-y-auto px-4 py-3 font-mono text-[12px] leading-relaxed"
        >
          {lines.map((ln, i) => (
            <div
              key={i}
              className={`monitor-line whitespace-pre ${TONE_CLASS[ln.tone] ?? TONE_CLASS.base}`}
              style={{ animationDelay: `${i * 45}ms` }}
            >
              {ln.text}
            </div>
          ))}
          <span className="monitor-cursor text-emerald-400">▌</span>
        </div>
      </div>
      <div className="mt-0 h-3 w-24 bg-[#2b3a35]" />
      <div className="h-1.5 w-48 rounded-b-md bg-[#2b3a35]" />
    </div>
  );
}
