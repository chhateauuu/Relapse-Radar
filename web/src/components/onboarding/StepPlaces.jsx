import Field, { inputClass } from "../ui/Field";

/** Step — mark a risky place (geofence). Lat/lng stay 0 for the demo. */
export default function StepPlaces({ plan, patch, errors }) {
  const geofence = (plan.geofences ?? [])[0] ?? {};

  const patchGeofence = (updates) => {
    const next = { label: "", lat: 0, lng: 0, radius_m: 200, ...geofence, ...updates };
    patch({ geofences: [next, ...(plan.geofences ?? []).slice(1)] });
  };

  return (
    <div className="flex flex-col gap-5">
      <header>
        <h2 className="text-xl font-bold text-slate-900">Mark your risky places</h2>
        <p className="mt-1 text-sm text-slate-600">
          A place where being there, for a while, is a warning sign for you.
        </p>
      </header>

      <Field label="Place name" hint="just a label only you understand" error={errors.geofence}>
        <input
          className={inputClass}
          value={geofence.label ?? ""}
          placeholder="old neighborhood"
          onChange={(e) => patchGeofence({ label: e.target.value })}
        />
      </Field>

      <Field label="How close counts" hint="radius in meters">
        <input
          type="number"
          min={50}
          max={2000}
          step={50}
          className={inputClass}
          value={geofence.radius_m ?? 200}
          onChange={(e) => patchGeofence({ radius_m: Number(e.target.value) })}
        />
      </Field>

      <p className="rounded-xl bg-slate-50 px-4 py-3 text-xs leading-relaxed text-slate-500">
        Location is checked on your phone. Radar never sees where you are — only
        whether your own rule was met.
      </p>
    </div>
  );
}
