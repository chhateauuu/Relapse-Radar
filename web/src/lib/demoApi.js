/**
 * Demo data client — the live-demo screen's source of truth.
 *
 * Offline-first: it always builds a complete, valid demo from the frozen
 * fixtures so the screen runs with no backend. When P3's API is reachable it
 * uses the **real model's** risk + drivers (`POST /assess/batch`) and re-derives
 * the traffic-light state, drift changepoint, and deterministic escalation on
 * top — so the line, the bands, and the sponsor moment stay coherent with what
 * the model decided. The population run is always a local demonstration.
 */
import { annotateChangepoints, buildDemo, buildTimeline, stateFor } from "./assess";
import { SAMPLE_PLAN } from "./fixtures";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

/**
 * @param {string} userId
 * @param {{mode?: "personal"|"population", plan?: object}} opts
 * @returns {Promise<{stream, assessments, timeline, source: "api"|"local"}>}
 */
export async function loadDemo(userId = "maya", opts = {}) {
  const { mode = "personal", plan = SAMPLE_PLAN } = opts;
  const local = buildDemo(mode, plan);

  // The population run is purely a local proof; never call the API for it.
  if (mode === "population") return { ...local, source: "local" };

  try {
    const res = await fetch(`${API_BASE}/assess/batch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(local.stream),
    });
    if (res.ok) {
      const apiAssessments = await res.json();
      if (Array.isArray(apiAssessments) && apiAssessments.length === local.stream.length) {
        // Use the model's risk + drivers; derive state (matching the chart
        // bands), changepoint, and the escalation timeline on top of it.
        const base = apiAssessments.map((a, i) => {
          const fallback = local.assessments[i];
          const risk = typeof a.risk === "number" ? a.risk : fallback.risk;
          const drivers =
            Array.isArray(a.drivers) && a.drivers.length ? a.drivers : fallback.drivers;
          const explanation =
            a.explanation && a.explanation.trim() ? a.explanation : fallback.explanation;
          return {
            user_id: a.user_id ?? local.stream[i].user_id,
            day: a.day ?? local.stream[i].day,
            risk,
            state: stateFor(risk),
            drivers,
            changepoint: { active: false, started_day: null },
            explanation,
          };
        });
        const assessments = annotateChangepoints(base);
        const timeline = buildTimeline(local.stream, assessments, plan);
        return { stream: local.stream, assessments, timeline, source: "api" };
      }
    }
  } catch {
    /* API unreachable — fall through to the local demo */
  }

  return { ...local, source: "local" };
}
