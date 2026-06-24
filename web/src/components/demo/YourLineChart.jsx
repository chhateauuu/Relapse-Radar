import {
  CartesianGrid,
  Label,
  Line,
  LineChart,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts";
import { STATE_THRESHOLDS } from "../../lib/assess";

/**
 * "Your line" — the centerpiece. The personal normal band sits low and green;
 * the risk line climbs across the days as the spiral builds. A marker shows
 * where the sustained drift began (the changepoint), proving it's not reacting
 * to one bad night.
 */
export default function YourLineChart({ series, current, domainDays, startedDay }) {
  // Reveal the line only up to the current day for the "climbing" effect.
  const data = series
    .filter((a) => a.day <= current.day)
    .map((a) => ({ day: a.day, risk: a.risk }));

  const [minDay, maxDay] = domainDays;

  return (
    <div className="rounded-2xl bg-white px-2 pb-2 pt-3 ring-1 ring-slate-100">
      <div className="px-2 pb-1 text-xs font-semibold text-slate-500">
        Your line over the last {maxDay - minDay + 1} days
      </div>
      <div className="h-44 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 6, right: 10, bottom: 4, left: -18 }}>
            <CartesianGrid stroke="#eef2f7" vertical={false} />
            {/* The normal band (green) + the warning zones. */}
            <ReferenceArea y1={0} y2={STATE_THRESHOLDS.amber} fill="#16a34a" fillOpacity={0.08} />
            <ReferenceArea
              y1={STATE_THRESHOLDS.amber}
              y2={STATE_THRESHOLDS.red}
              fill="#f59e0b"
              fillOpacity={0.08}
            />
            <ReferenceArea y1={STATE_THRESHOLDS.red} y2={1} fill="#dc2626" fillOpacity={0.08} />

            <XAxis
              type="number"
              dataKey="day"
              domain={[minDay, maxDay]}
              allowDecimals={false}
              tick={{ fontSize: 11, fill: "#94a3b8" }}
              tickLine={false}
              axisLine={{ stroke: "#e2e8f0" }}
            />
            <YAxis
              domain={[0, 1]}
              ticks={[0, STATE_THRESHOLDS.amber, STATE_THRESHOLDS.red, 1]}
              tickFormatter={(v) => Math.round(v * 100)}
              tick={{ fontSize: 11, fill: "#94a3b8" }}
              tickLine={false}
              axisLine={false}
              width={32}
            />

            {startedDay != null && startedDay <= current.day && (
              <ReferenceLine x={startedDay} stroke="#94a3b8" strokeDasharray="3 3">
                <Label
                  value="drift began"
                  position="insideTopLeft"
                  fontSize={10}
                  fill="#64748b"
                />
              </ReferenceLine>
            )}

            <Line
              type="monotone"
              dataKey="risk"
              stroke="#0f766e"
              strokeWidth={3}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
