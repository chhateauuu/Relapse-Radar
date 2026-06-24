/**
 * Demo data for the P4 live-demo screen.
 *
 * The demo stream is the two frozen fixtures concatenated: the healthy days
 * first, then the relapse spiral (days 60 → 70). There is intentionally no
 * single combined fixture — we build it here, sorted by day, so the slider can
 * scrub a clean healthy → spiral arc.
 *
 * Honors shared/contracts.md exactly: each item is a FeatureRecord.
 */
import healthy from "@shared/fixtures/maya_healthy.json";
import spiral from "@shared/fixtures/maya_spiral.json";

/** FeatureRecord[] for the whole demo, healthy first, ascending by day. */
export const DEMO_STREAM = [...healthy, ...spiral].sort((a, b) => a.day - b.day);

/** The healthy slice only — used to learn the personal baseline. */
export const HEALTHY_RECORDS = [...healthy].sort((a, b) => a.day - b.day);

/**
 * Per-feature display + modelling metadata. `higherIsWorse` encodes which
 * direction of drift is a relapse warning sign; `minStd` is a realistic spread
 * floor so a tiny 4-day baseline sample can't make z-scores explode.
 */
export const FEATURES = [
  { key: "sleep_hours", label: "Sleep", unit: "h", higherIsWorse: false, weight: 0.9, minStd: 1.0, decimals: 1 },
  { key: "late_night_min", label: "Late-night use", unit: "m", higherIsWorse: true, weight: 0.7, minStd: 15, decimals: 0 },
  { key: "outgoing_msgs", label: "Messages out", unit: "", higherIsWorse: false, weight: 0.8, minStd: 4, decimals: 0 },
  { key: "unique_contacts", label: "People reached", unit: "", higherIsWorse: false, weight: 0.5, minStd: 2, decimals: 0 },
  { key: "location_entropy", label: "Places visited", unit: "", higherIsWorse: false, weight: 0.7, minStd: 0.3, decimals: 1 },
  { key: "time_at_home_pct", label: "Time at home", unit: "%", higherIsWorse: true, weight: 0.5, minStd: 0.12, decimals: 0, scale: 100 },
  { key: "dwell_flagged_min", label: "Near a flagged place", unit: "m", higherIsWorse: true, weight: 1.1, minStd: 5, decimals: 0 },
  { key: "screen_time_min", label: "Screen time", unit: "m", higherIsWorse: true, weight: 0.4, minStd: 40, decimals: 0 },
  { key: "unlocks", label: "Phone unlocks", unit: "", higherIsWorse: true, weight: 0.4, minStd: 20, decimals: 0 },
  { key: "steps", label: "Steps", unit: "", higherIsWorse: false, weight: 0.4, minStd: 1200, decimals: 0 },
];

/** Quick lookup by feature key. */
export const FEATURE_BY_KEY = Object.fromEntries(FEATURES.map((f) => [f.key, f]));

/** Friendly label for a feature key (falls back to the key). */
export function featureLabel(key) {
  return FEATURE_BY_KEY[key]?.label ?? key;
}

/** Format a raw feature value for display, honoring scale/decimals/unit. */
export function formatFeature(key, value) {
  const meta = FEATURE_BY_KEY[key];
  if (!meta || value == null) return String(value ?? "—");
  const scaled = meta.scale ? value * meta.scale : value;
  const text = scaled.toFixed(meta.decimals ?? 0);
  return meta.unit ? `${text}${meta.unit}` : text;
}
