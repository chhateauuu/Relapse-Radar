import { inputClass } from "../ui/Field";
import MiniMap from "../ui/MiniMap";

/** A sensible default center (downtown Portland) for the first added pin. */
const DEFAULT_CENTER = { lat: 45.523, lng: -122.659 };

/**
 * Edit the list of flagged places: addresses on a map, each with a radius, with
 * add/remove. New pins are offset so they land distinctly on the map (we can't
 * geocode a typed address offline, so the marker is illustrative).
 */
export default function PlacesEditor({ places, onChange, error }) {
  const list = places ?? [];

  const update = (i, updates) =>
    onChange(list.map((p, idx) => (idx === i ? { ...p, ...updates } : p)));

  const remove = (i) => onChange(list.filter((_, idx) => idx !== i));

  const add = () => {
    const base = list[list.length - 1] ?? DEFAULT_CENTER;
    const n = list.length;
    onChange([
      ...list,
      {
        label: "",
        lat: base.lat + 0.004 * ((n % 3) - 1),
        lng: base.lng + 0.004 * (n % 2 ? 1 : -1),
        radius_m: 200,
      },
    ]);
  };

  return (
    <div className="flex flex-col gap-3">
      <MiniMap places={list} />

      <ul className="flex flex-col gap-3">
        {list.map((p, i) => (
          <li key={i} className="rounded-2xl border border-slate-200 bg-white p-3">
            <div className="mb-2 flex items-center justify-between">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-red-600 text-xs font-bold text-white">
                {i + 1}
              </span>
              <button
                type="button"
                onClick={() => remove(i)}
                className="text-xs font-semibold text-slate-400 transition hover:text-rose-500"
              >
                Remove
              </button>
            </div>
            <input
              className={inputClass}
              value={p.label ?? ""}
              placeholder="123 SE Main St, Portland, OR"
              onChange={(e) => update(i, { label: e.target.value })}
            />
            <div className="mt-2 flex items-center gap-2">
              <span className="text-xs text-slate-500">Within</span>
              <input
                type="number"
                min={50}
                max={2000}
                step={50}
                className={`${inputClass} w-24`}
                value={p.radius_m ?? 200}
                onChange={(e) => update(i, { radius_m: Number(e.target.value) })}
              />
              <span className="text-xs text-slate-500">meters</span>
            </div>
          </li>
        ))}
      </ul>

      {error && <p className="text-xs text-rose-500">{error}</p>}

      <button
        type="button"
        onClick={add}
        className="rounded-xl border border-dashed border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-600 transition hover:bg-slate-50"
      >
        + Add a place
      </button>
    </div>
  );
}
