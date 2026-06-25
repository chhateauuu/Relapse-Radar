/**
 * CatchPlan model helpers — honors shared/contracts.md exactly.
 *
 * The CatchPlan is the user-authored "Ulysses contract": written while well, it
 * says exactly what happens when their line goes off. P3's deterministic rules
 * engine reads this shape; we only ever write it.
 */

export const STATE_OPTIONS = [
  { value: "AMBER", label: "Amber — your line's off" },
  { value: "RED", label: "Red — reach out" },
];

/** A blank, schema-valid CatchPlan for a fresh onboarding. */
export function emptyPlan(userId = "maya") {
  return {
    user_id: userId,
    thresholds: { state: "RED", sustained_days: 2 },
    require_geofence: true,
    geofences: [],
    self_nudge_first: true,
    circle: [],
    message_template: "",
  };
}

/**
 * A paused plan: same schema, but with no recipient and no message, so P3's
 * rules engine has nothing to send. This is how "revoke in one tap" stays
 * within the frozen contract — we neutralize the plan rather than add a flag.
 */
export function neutralizePlan(plan, userId = "maya") {
  return { ...normalizePlan(plan, userId), circle: [], message_template: "" };
}

/**
 * Coerce any partial plan into the full, schema-valid shape so the editor and
 * the API never see a missing field.
 */
export function normalizePlan(plan, userId = "maya") {
  const base = emptyPlan(userId);
  return {
    ...base,
    ...plan,
    user_id: plan?.user_id ?? userId,
    thresholds: { ...base.thresholds, ...(plan?.thresholds ?? {}) },
    geofences: Array.isArray(plan?.geofences) ? plan.geofences : [],
    circle: Array.isArray(plan?.circle) ? plan.circle : [],
  };
}

/**
 * Validate a plan for the demo's purposes. Returns a map of {field: message}
 * for anything the user still needs to fill in.
 */
export function validatePlan(plan) {
  const issues = {};
  const sponsor = (plan.circle ?? [])[0];
  if (!sponsor?.name?.trim()) issues.sponsorName = "Choose who Radar reaches.";
  if (!sponsor?.contact?.trim()) issues.sponsorContact = "Add a phone number.";
  if (!plan.message_template?.trim())
    issues.message = "Write the message you'd want sent.";
  if (plan.require_geofence && !(plan.geofences ?? []).some((g) => g.label?.trim()))
    issues.geofence = "Mark at least one place, or turn off the requirement.";
  const days = Number(plan.thresholds?.sustained_days);
  if (!Number.isInteger(days) || days < 1)
    issues.sustainedDays = "Use a whole number of days (1 or more).";
  return issues;
}

export const isValidPlan = (plan) => Object.keys(validatePlan(plan)).length === 0;
