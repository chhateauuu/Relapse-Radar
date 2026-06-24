import Field, { inputClass } from "../ui/Field";
import Toggle from "../ui/Toggle";
import { STATE_OPTIONS } from "../../lib/plan";

/** Step — set the threshold and consent rules that trigger the reach-out. */
export default function StepThresholds({ plan, patch, errors }) {
  const setThreshold = (updates) =>
    patch({ thresholds: { ...plan.thresholds, ...updates } });

  return (
    <div className="flex flex-col gap-5">
      <header>
        <h2 className="text-xl font-bold text-slate-900">Set your line</h2>
        <p className="mt-1 text-sm text-slate-600">
          When should Radar act? You decide how loud the signal has to be.
        </p>
      </header>

      <Field label="Reach out at" hint="how high your state has to climb">
        <div className="mt-1 grid grid-cols-2 gap-2">
          {STATE_OPTIONS.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => setThreshold({ state: opt.value })}
              className={`rounded-xl border px-3 py-2.5 text-sm font-semibold transition ${
                plan.thresholds?.state === opt.value
                  ? "border-emerald-500 bg-emerald-50 text-emerald-700"
                  : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </Field>

      <Field
        label="Sustained for"
        hint="days in a row before it acts — avoids one bad night"
        error={errors.sustainedDays}
      >
        <input
          type="number"
          min={1}
          max={14}
          className={inputClass}
          value={plan.thresholds?.sustained_days ?? 2}
          onChange={(e) => setThreshold({ sustained_days: Number(e.target.value) })}
        />
      </Field>

      <Toggle
        label="Nudge me first"
        hint="give you a chance to self-soothe before anyone's contacted"
        checked={plan.self_nudge_first}
        onChange={(v) => patch({ self_nudge_first: v })}
      />
    </div>
  );
}
