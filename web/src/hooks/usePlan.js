import { useCallback, useEffect, useState } from "react";
import { clearPlan, getPlan, putPlan, setPaused as setPausedApi } from "../lib/api";
import { emptyPlan, normalizePlan } from "../lib/plan";
import { SAMPLE_PLAN } from "../lib/fixtures";

/**
 * Owns the editable CatchPlan: loads it (API or local fallback), exposes a
 * field patcher, and saves it back. `source` tells the UI whether it's talking
 * to the live API or the offline fallback; `paused` reflects the one-tap revoke.
 *
 * Seeds with the hardcoded sample plan so both the demo and the plan page show
 * fully-filled, matching info with no data entry required.
 */
export function usePlan(userId = "maya") {
  const [plan, setPlan] = useState(() => normalizePlan(SAMPLE_PLAN, userId));
  const [source, setSource] = useState("loading");
  const [paused, setPaused] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState(null);

  useEffect(() => {
    let active = true;
    getPlan(userId).then(({ plan: loaded, paused: isPaused, source: src }) => {
      if (!active) return;
      setPlan(loaded);
      setPaused(isPaused);
      setSource(src);
    });
    return () => {
      active = false;
    };
  }, [userId]);

  const patch = useCallback((updates) => {
    setPlan((prev) => ({ ...prev, ...updates }));
    setSavedAt(null);
  }, []);

  const save = useCallback(async () => {
    setSaving(true);
    const { plan: saved, source: src } = await putPlan(userId, plan);
    setPlan(saved);
    setSource(src);
    setSaving(false);
    setSavedAt(Date.now());
    return saved;
  }, [userId, plan]);

  const togglePause = useCallback(async () => {
    const next = !paused;
    setPaused(next);
    setSaving(true);
    const { source: src } = await setPausedApi(userId, next, plan);
    setSource(src);
    setSaving(false);
    setSavedAt(Date.now());
    return next;
  }, [userId, plan, paused]);

  const deletePlan = useCallback(async () => {
    setSaving(true);
    await clearPlan(userId);
    const fresh = emptyPlan(userId);
    setPlan(fresh);
    setPaused(false);
    setSavedAt(null);
    setSaving(false);
    return fresh;
  }, [userId]);

  return {
    plan,
    setPlan,
    patch,
    source,
    paused,
    saving,
    savedAt,
    save,
    togglePause,
    deletePlan,
  };
}
