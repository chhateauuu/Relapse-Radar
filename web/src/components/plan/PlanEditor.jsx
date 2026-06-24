import { useState } from "react";
import Field, { inputClass } from "../ui/Field";
import Toggle from "../ui/Toggle";
import Button from "../ui/Button";
import { STATE_OPTIONS } from "../../lib/plan";

/** A titled group of controls. */
function Section({ title, children }) {
  return (
    <section className="flex flex-col gap-3">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
        {title}
      </h3>
      {children}
    </section>
  );
}

/**
 * The full catch-plan editor — everything on one scroll for someone revisiting
 * a plan they already authored. Same patch helpers as onboarding.
 */
export default function PlanEditor({
  plan,
  patch,
  saving,
  savedAt,
  paused,
  onSave,
  onTogglePause,
  onDelete,
  onRestart,
}) {
  const [confirmingDelete, setConfirmingDelete] = useState(false);
  const sponsor = (plan.circle ?? [])[0] ?? {};
  const place = (plan.geofences ?? [])[0] ?? {};

  const patchSponsor = (updates) =>
    patch({
      circle: [
        { name: "", role: "sponsor", contact: "", ...sponsor, ...updates },
        ...(plan.circle ?? []).slice(1),
      ],
    });
  const patchPlace = (updates) =>
    patch({
      geofences: [
        { label: "", lat: 0, lng: 0, radius_m: 200, ...place, ...updates },
        ...(plan.geofences ?? []).slice(1),
      ],
    });
  const setThreshold = (updates) =>
    patch({ thresholds: { ...plan.thresholds, ...updates } });

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto px-6 py-5">
        <header className="mb-5">
          <h2 className="text-xl font-bold text-slate-900">Your catch-plan</h2>
          <p className="mt-1 text-sm text-slate-600">
            {paused
              ? "Paused — Radar won't reach out to anyone."
              : "Active and yours. Change anything, any time."}
          </p>
        </header>

        {paused && (
          <div className="mb-5 flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3">
            <span className="text-lg leading-none">⏸️</span>
            <p className="text-xs leading-relaxed text-amber-800">
              Your plan is paused. Nothing is sent to anyone while it's off — turn
              it back on whenever you're ready.
            </p>
          </div>
        )}

        <div className="flex flex-col gap-6">
          <Section title="Your person">
            <Field label="Name">
              <input
                className={inputClass}
                value={sponsor.name ?? ""}
                onChange={(e) => patchSponsor({ name: e.target.value })}
              />
            </Field>
            <Field label="Number">
              <input
                type="tel"
                className={inputClass}
                value={sponsor.contact ?? ""}
                onChange={(e) => patchSponsor({ contact: e.target.value })}
              />
            </Field>
          </Section>

          <Section title="Message">
            <textarea
              rows={4}
              className={`${inputClass} resize-none`}
              value={plan.message_template ?? ""}
              onChange={(e) => patch({ message_template: e.target.value })}
            />
          </Section>

          <Section title="Risky place">
            <Field label="Label">
              <input
                className={inputClass}
                value={place.label ?? ""}
                onChange={(e) => patchPlace({ label: e.target.value })}
              />
            </Field>
            <Field label="Radius (m)">
              <input
                type="number"
                min={50}
                max={2000}
                step={50}
                className={inputClass}
                value={place.radius_m ?? 200}
                onChange={(e) => patchPlace({ radius_m: Number(e.target.value) })}
              />
            </Field>
          </Section>

          <Section title="When to act">
            <div className="grid grid-cols-2 gap-2">
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
            <Field label="Sustained days">
              <input
                type="number"
                min={1}
                max={14}
                className={inputClass}
                value={plan.thresholds?.sustained_days ?? 2}
                onChange={(e) =>
                  setThreshold({ sustained_days: Number(e.target.value) })
                }
              />
            </Field>
            <Toggle
              label="Nudge me first"
              checked={plan.self_nudge_first}
              onChange={(v) => patch({ self_nudge_first: v })}
            />
            <Toggle
              label="Require I'm at a risky place"
              checked={plan.require_geofence}
              onChange={(v) => patch({ require_geofence: v })}
            />
          </Section>

          <div className="mt-2 flex flex-col gap-3 border-t border-slate-100 pt-5">
            <button
              type="button"
              onClick={onTogglePause}
              disabled={saving}
              className={`flex w-full items-center justify-between gap-3 rounded-xl border px-4 py-3 text-left transition disabled:opacity-60 ${
                paused
                  ? "border-emerald-200 bg-emerald-50 hover:bg-emerald-100"
                  : "border-amber-200 bg-amber-50 hover:bg-amber-100"
              }`}
            >
              <span>
                <span className="block text-sm font-semibold text-slate-800">
                  {paused ? "Resume plan" : "Pause plan"}
                </span>
                <span className="block text-xs text-slate-500">
                  {paused
                    ? "Turn Radar back on — your plan is restored exactly as you left it."
                    : "Turn it off in one tap. Nothing is sent while paused."}
                </span>
              </span>
              <span className="text-xl leading-none">{paused ? "▶️" : "⏸️"}</span>
            </button>

            {confirmingDelete ? (
              <div className="flex flex-col gap-2 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3">
                <p className="text-xs leading-relaxed text-rose-700">
                  Delete your whole plan? This clears it from this device and tells
                  Radar to stop. You can always write a new one.
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={() => setConfirmingDelete(false)}
                    disabled={saving}
                    className="flex-1"
                  >
                    Keep it
                  </Button>
                  <button
                    type="button"
                    onClick={onDelete}
                    disabled={saving}
                    className="flex-1 rounded-full bg-rose-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-rose-700 disabled:opacity-60"
                  >
                    Delete plan
                  </button>
                </div>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setConfirmingDelete(true)}
                disabled={saving}
                className="self-start text-xs font-semibold text-rose-400 underline-offset-2 hover:text-rose-600 hover:underline disabled:opacity-60"
              >
                Delete my plan
              </button>
            )}

            <button
              type="button"
              onClick={onRestart}
              className="self-start text-xs font-semibold text-slate-400 underline-offset-2 hover:text-slate-600 hover:underline"
            >
              Start over with the guided setup
            </button>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between gap-3 border-t border-slate-100 px-6 py-4">
        <span className="text-xs text-slate-400">
          {saving
            ? "Saving…"
            : paused
              ? "Paused"
              : savedAt
                ? "Saved"
                : "Unsaved changes"}
        </span>
        <Button onClick={onSave} disabled={saving} className="min-w-28">
          Save changes
        </Button>
      </div>
    </div>
  );
}
