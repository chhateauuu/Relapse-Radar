import Field, { inputClass } from "../ui/Field";

/** Step — choose the person Radar reaches (circle[0], the sponsor). */
export default function StepPerson({ plan, patch, errors }) {
  const sponsor = (plan.circle ?? [])[0] ?? {};

  const patchSponsor = (updates) => {
    const next = { name: "", role: "sponsor", contact: "", ...sponsor, ...updates };
    patch({ circle: [next, ...(plan.circle ?? []).slice(1)] });
  };

  return (
    <div className="flex flex-col gap-5">
      <header>
        <h2 className="text-xl font-bold text-slate-900">Choose your person</h2>
        <p className="mt-1 text-sm text-slate-600">
          The one person you trust to catch you — a sponsor, a friend, family.
        </p>
      </header>

      <Field label="Their name" error={errors.sponsorName}>
        <input
          className={inputClass}
          value={sponsor.name ?? ""}
          placeholder="Dana"
          onChange={(e) => patchSponsor({ name: e.target.value })}
        />
      </Field>

      <Field label="Their role">
        <input
          className={inputClass}
          value={sponsor.role ?? ""}
          placeholder="sponsor"
          onChange={(e) => patchSponsor({ role: e.target.value })}
        />
      </Field>

      <Field label="Their number" hint="where the text would go" error={errors.sponsorContact}>
        <input
          type="tel"
          className={inputClass}
          value={sponsor.contact ?? ""}
          placeholder="+1 555 555 0123"
          onChange={(e) => patchSponsor({ contact: e.target.value })}
        />
      </Field>
    </div>
  );
}
