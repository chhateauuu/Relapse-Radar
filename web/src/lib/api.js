/**
 * CatchPlan API client — GET/PUT /plan/{user_id} (shared/contracts.md).
 *
 * P3's API is the source of truth at integration. Until it's reachable (or for
 * offline demos) this falls back to localStorage seeded from the fixture, so the
 * onboarding always loads and saves something. The shapes are identical, so the
 * fallback is invisible to the rest of the app.
 */
import { SAMPLE_PLAN } from "./fixtures";
import { neutralizePlan, normalizePlan } from "./plan";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";
const storageKey = (userId) => `relapse-radar:plan:v2:${userId}`;
const pausedKey = (userId) => `relapse-radar:paused:v2:${userId}`;

function readPaused(userId) {
  try {
    return localStorage.getItem(pausedKey(userId)) === "1";
  } catch {
    return false;
  }
}

function writePaused(userId, paused) {
  try {
    if (paused) localStorage.setItem(pausedKey(userId), "1");
    else localStorage.removeItem(pausedKey(userId));
  } catch {
    /* storage may be unavailable; not fatal for the demo */
  }
}

function readLocal(userId) {
  try {
    const raw = localStorage.getItem(storageKey(userId));
    if (raw) return normalizePlan(JSON.parse(raw), userId);
  } catch {
    /* ignore unparseable/blocked storage */
  }
  return normalizePlan({ ...SAMPLE_PLAN, user_id: userId }, userId);
}

function writeLocal(userId, plan) {
  try {
    localStorage.setItem(storageKey(userId), JSON.stringify(plan));
  } catch {
    /* storage may be unavailable; not fatal for the demo */
  }
}

/** Load the plan: live API first, local fallback if it's unreachable. */
export async function getPlan(userId = "maya") {
  const paused = readPaused(userId);
  try {
    const res = await fetch(`${API_BASE}/plan/${userId}`);
    if (res.ok)
      return { plan: normalizePlan(await res.json(), userId), paused, source: "api" };
  } catch {
    /* fall through to local */
  }
  return { plan: readLocal(userId), paused, source: "local" };
}

/** Save the plan: write through to the API when reachable, always cache local. */
export async function putPlan(userId = "maya", plan) {
  const normalized = normalizePlan(plan, userId);
  writeLocal(userId, normalized);
  const paused = readPaused(userId);
  const effective = paused ? neutralizePlan(normalized, userId) : normalized;
  try {
    const res = await fetch(`${API_BASE}/plan/${userId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(effective),
    });
    if (res.ok) {
      await res.json();
      return { plan: normalized, paused, source: "api" };
    }
  } catch {
    /* fall through to local */
  }
  return { plan: normalized, paused, source: "local" };
}

/**
 * Pause or resume in one tap. The authored plan stays cached locally; while
 * paused, P3 receives a neutralized plan it can't act on. Reversible — resuming
 * pushes the authored plan back.
 */
export async function setPaused(userId = "maya", paused, plan) {
  writePaused(userId, paused);
  return putPlan(userId, plan);
}

/** Delete the plan: clear local data and push a neutralized plan to the API. */
export async function clearPlan(userId = "maya") {
  writePaused(userId, false);
  try {
    localStorage.removeItem(storageKey(userId));
  } catch {
    /* storage may be unavailable */
  }
  try {
    await fetch(`${API_BASE}/plan/${userId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(neutralizePlan({ user_id: userId }, userId)),
    });
  } catch {
    /* offline is fine; local is already cleared */
  }
}
