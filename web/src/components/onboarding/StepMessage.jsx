import Field, { inputClass } from "../ui/Field";

const STARTERS = [
  "If you get this, I'm having a hard night near somewhere risky — please call me.",
  "This is my pre-written SOS. I'm not okay right now. Reach out, don't wait for me to.",
  "Red flag from me to you. Can you check in tonight? It would help to hear your voice.",
];

/** Step — write the message that gets sent. The user's own words. */
export default function StepMessage({ plan, patch, errors }) {
  return (
    <div className="flex flex-col gap-5">
      <header>
        <h2 className="text-xl font-bold text-slate-900">Write your message</h2>
        <p className="mt-1 text-sm text-slate-600">
          This is exactly what your person receives. No edits, no AI — your voice
          to your future self's rescuer.
        </p>
      </header>

      <Field error={errors.message}>
        <textarea
          rows={5}
          className={`${inputClass} resize-none`}
          value={plan.message_template ?? ""}
          placeholder="If you get this, I'm having a hard night…"
          onChange={(e) => patch({ message_template: e.target.value })}
        />
      </Field>

      <div>
        <p className="mb-2 text-xs font-semibold text-slate-500">Need a starting point?</p>
        <div className="flex flex-col gap-2">
          {STARTERS.map((text) => (
            <button
              key={text}
              type="button"
              onClick={() => patch({ message_template: text })}
              className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-left text-xs leading-relaxed text-slate-600 transition hover:border-emerald-300 hover:bg-emerald-50"
            >
              {text}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
