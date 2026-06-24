/**
 * Offline assessment engine for the demo.
 *
 * At integration the brain (P1/P2) and API (P3) produce the RiskAssessment and
 * EscalationEvent series. Until that's wired — and so the demo always runs even
 * with no backend — this computes the same shapes locally from the fixtures:
 * a personalized z-score baseline → fused risk → state → drivers → changepoint,
 * plus the deterministic catch-plan escalation. Output shapes match
 * shared/contracts.md exactly.
 *
 * The "personal vs population" toggle is a real, visible demonstration: the
 * personal model learns Maya's own normal and catches the spiral; the population
 * model uses generic averages and under-reacts — it misses her.
 */
import { DEMO_STREAM, FEATURES, HEALTHY_RECORDS } from "./demoData";
import { SAMPLE_PLAN } from "./fixtures";

export const STATE_THRESHOLDS = { amber: 0.3, red: 0.6 };

/** Risk (0–1) → GREEN | AMBER | RED. */
export function stateFor(risk) {
  if (risk >= STATE_THRESHOLDS.red) return "RED";
  if (risk >= STATE_THRESHOLDS.amber) return "AMBER";
  return "GREEN";
}

const Z_CLAMP = 4; // keep z-scores in a realistic, readable range
const RISK_GAIN = 0.18; // tuned so healthy ≈ 0.07 and the spiral peak ≈ 0.8
const RISK_BIAS = -2.7;

/** Generic population baseline — deliberately lenient, so it misses Maya. */
const POPULATION_BASELINE = {
  sleep_hours: { mean: 6.3, std: 1.4 },
  late_night_min: { mean: 35, std: 30 },
  outgoing_msgs: { mean: 12, std: 8 },
  unique_contacts: { mean: 4, std: 3 },
  location_entropy: { mean: 1.0, std: 0.5 },
  time_at_home_pct: { mean: 0.65, std: 0.2 },
  dwell_flagged_min: { mean: 5, std: 12 },
  screen_time_min: { mean: 300, std: 90 },
  unlocks: { mean: 120, std: 50 },
  steps: { mean: 4500, std: 2500 },
};

const sigmoid = (x) => 1 / (1 + Math.exp(-x));
const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));

/** Mean + standard deviation of one feature across the healthy records. */
function meanStd(records, key) {
  const xs = records.map((r) => r.features[key]);
  const mean = xs.reduce((a, b) => a + b, 0) / xs.length;
  const variance =
    xs.reduce((a, b) => a + (b - mean) ** 2, 0) / Math.max(1, xs.length - 1);
  return { mean, std: Math.sqrt(variance) };
}

/** Learn each person's normal from their healthy days (per-feature mean/std). */
function personalBaseline(records) {
  const base = {};
  for (const f of FEATURES) base[f.key] = meanStd(records, f.key);
  return base;
}

const PERSONAL_BASELINE = personalBaseline(HEALTHY_RECORDS);

/** Signed z-score with a per-feature spread floor and a clamp. */
function zScore(value, key, baseline) {
  const meta = FEATURES.find((f) => f.key === key);
  const { mean, std } = baseline[key];
  const spread = Math.max(std, meta.minStd);
  return clamp((value - mean) / spread, -Z_CLAMP, Z_CLAMP);
}

/** One FeatureRecord → its per-feature z-scores + fused risk + drivers. */
function scoreRecord(record, baseline) {
  let sumContribution = 0;
  const perFeature = FEATURES.map((f) => {
    const z = zScore(record.features[f.key], f.key, baseline);
    // "badness" = how far in the relapse-warning direction this signal drifted.
    const badness = f.higherIsWorse ? z : -z;
    const contribution = Math.max(0, badness) * f.weight;
    sumContribution += contribution;
    return { feature: f.key, z, direction: z >= 0 ? "up" : "down", contribution };
  });

  const risk = sigmoid(RISK_GAIN * sumContribution + RISK_BIAS);

  const drivers = perFeature
    .filter((d) => d.contribution > 0.2)
    .sort((a, b) => b.contribution - a.contribution)
    .slice(0, 3)
    .map(({ feature, z, direction }) => ({
      feature,
      z: Math.round(z * 10) / 10,
      direction,
    }));

  return { risk, drivers, perFeature };
}

const PHRASES = {
  sleep_hours: { down: "you've been sleeping less" },
  late_night_min: { up: "you're up late more often" },
  outgoing_msgs: { down: "you've gone quieter with people" },
  unique_contacts: { down: "you've been reaching out to fewer people" },
  location_entropy: { down: "you've been getting out less" },
  time_at_home_pct: { up: "you've been staying in more" },
  dwell_flagged_min: { up: "you're spending time somewhere you flagged" },
  screen_time_min: { up: "you're on your phone more" },
  unlocks: { up: "you're checking your phone more" },
  steps: { down: "you've been moving less" },
};

/** Warm, non-clinical sentence from the drivers (the LLM replaces this later). */
function explain(state, drivers) {
  if (state === "GREEN" || drivers.length === 0) {
    return "Your line's steady — you're on track.";
  }
  const parts = drivers
    .map((d) => PHRASES[d.feature]?.[d.direction])
    .filter(Boolean);
  const seen = [];
  for (const p of parts) if (!seen.includes(p)) seen.push(p);
  const list =
    seen.length <= 1
      ? seen[0]
      : `${seen.slice(0, -1).join(", ")} and ${seen[seen.length - 1]}`;
  return `Your line's been off — ${list}. That pattern's been hard for you before.`;
}

/**
 * Build the full demo for one model: the FeatureRecord stream, a RiskAssessment
 * per day, and the EscalationEvent timeline the catch-plan would produce.
 *
 * @param {"personal"|"population"} mode
 * @param {object} plan CatchPlan (thresholds, geofence, message, circle)
 */
/**
 * Fill each assessment's changepoint from the risk series: the first day of the
 * sustained climb that led into the current elevated state. Works on any
 * RiskAssessment[] (local or model), assuming ascending day order.
 */
export function annotateChangepoints(assessments) {
  if (assessments.length === 0) return assessments;
  const baselineRisk = Math.min(...assessments.map((a) => a.risk));
  const driftFloor = baselineRisk + 0.05;
  return assessments.map((a, i) => {
    const active = a.state !== "GREEN";
    let startedDay = null;
    if (active) {
      let j = i;
      while (j > 0 && assessments[j].risk > driftFloor) j -= 1;
      startedDay = assessments[Math.min(j + 1, i)].day;
    }
    return { ...a, changepoint: { active, started_day: startedDay } };
  });
}

export function buildDemo(mode = "personal", plan = SAMPLE_PLAN) {
  const baseline = mode === "population" ? POPULATION_BASELINE : PERSONAL_BASELINE;
  const stream = DEMO_STREAM;

  // First pass: risk + drivers per day.
  const scored = stream.map((rec) => scoreRecord(rec, baseline));

  const base = stream.map((rec, i) => {
    const { risk, drivers } = scored[i];
    const state = stateFor(risk);
    return {
      user_id: rec.user_id,
      day: rec.day,
      risk: Math.round(risk * 100) / 100,
      state,
      drivers,
      changepoint: { active: false, started_day: null },
      explanation: explain(state, drivers),
    };
  });

  const assessments = annotateChangepoints(base);
  const timeline = buildTimeline(stream, assessments, plan);
  return { stream, assessments, timeline };
}

/** Deterministic catch-plan engine → the escalation events over the run. */
export function buildTimeline(stream, assessments, plan) {
  const events = [];
  const sustainedNeeded = plan?.thresholds?.sustained_days ?? 2;
  const requireGeofence = plan?.require_geofence ?? true;
  const selfNudgeFirst = plan?.self_nudge_first ?? true;
  const recipient = plan?.circle?.[0]?.name?.trim() || "your person";
  const message =
    plan?.message_template?.trim() ||
    "If you get this, I'm having a hard night near somewhere risky — please call me.";

  let redRun = 0;
  let nudged = false;
  let notified = false;

  assessments.forEach((a, i) => {
    const rec = stream[i];
    const nearFlagged = (rec.features.dwell_flagged_min ?? 0) > 0;

    // Self-nudge once, the first time the line drifts into AMBER+.
    if (selfNudgeFirst && !nudged && a.state !== "GREEN") {
      nudged = true;
      events.push({
        user_id: a.user_id,
        day: a.day,
        type: "self_nudge",
        recipient: a.user_id,
        channel: "app",
        message: "Noticing your line's off. HALT check — how are you doing?",
        sent_at: `${rec.date}T21:30:00Z`,
      });
    }

    redRun = a.state === "RED" ? redRun + 1 : 0;

    // Notify the chosen person once: sustained RED + (optionally) near a flagged
    // place — exactly the user-authored rule, nothing more.
    const geofenceOk = !requireGeofence || nearFlagged;
    if (!notified && redRun >= sustainedNeeded && geofenceOk) {
      notified = true;
      events.push({
        user_id: a.user_id,
        day: a.day,
        type: "notify_circle",
        recipient,
        channel: "sms",
        message,
        sent_at: `${rec.date}T22:14:00Z`,
      });
    }
  });

  return events;
}
