import PlacesEditor from "../plan/PlacesEditor";

/** Step — mark risky places by address, shown on a map. */
export default function StepPlaces({ plan, patch, errors }) {
  return (
    <div className="flex flex-col gap-5">
      <header>
        <h2 className="text-xl font-bold text-slate-900">Mark your risky places</h2>
        <p className="mt-1 text-sm text-slate-600">
          Addresses where being there, for a while, is a warning sign for you.
        </p>
      </header>

      <PlacesEditor
        places={plan.geofences}
        onChange={(geofences) => patch({ geofences })}
        error={errors.geofence}
      />

      <p className="rounded-xl bg-slate-50 px-4 py-3 text-xs leading-relaxed text-slate-500">
        Location is checked on your phone. Radar never sees where you are — only
        whether your own rule was met.
      </p>
    </div>
  );
}
