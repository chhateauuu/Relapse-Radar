/**
 * Demo controls — the levers the presenter drives:
 *  • advance-day slider (scrub the spiral)
 *  • play / pause auto-advance
 *  • on-device toggle (privacy proof)
 *  • personal vs population toggle (the AI proof)
 */
export default function DemoControls({
  dayIndex,
  maxIndex,
  currentDay,
  onIndexChange,
  playing,
  onTogglePlay,
  onDevice,
  onToggleOnDevice,
  mode,
  onModeChange,
}) {
  return (
    <div className="flex w-full max-w-xl flex-col gap-5 rounded-2xl bg-slate-900/70 p-5 ring-1 ring-white/10 backdrop-blur">
      {/* Advance-day slider */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between text-xs font-medium text-slate-300">
          <span>Advance days</span>
          <span className="tabular-nums text-slate-400">Day {currentDay}</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onTogglePlay}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-emerald-600 text-white transition hover:bg-emerald-700"
            aria-label={playing ? "Pause" : "Play"}
          >
            {playing ? "❚❚" : "▶"}
          </button>
          <input
            type="range"
            min={0}
            max={maxIndex}
            step={1}
            value={dayIndex}
            onChange={(e) => onIndexChange(Number(e.target.value))}
            className="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-slate-600 accent-emerald-500"
          />
        </div>
      </div>

      {/* Toggles */}
      <div className="grid grid-cols-2 gap-3">
        <TogglePill
          label="On-device"
          hint={onDevice ? "raw data stays on phone" : "off"}
          active={onDevice}
          onClick={() => onToggleOnDevice(!onDevice)}
        />
        <TogglePill
          label={mode === "personal" ? "Personal model" : "Population model"}
          hint={mode === "personal" ? "learns Maya's normal" : "generic averages"}
          active={mode === "personal"}
          onClick={() => onModeChange(mode === "personal" ? "population" : "personal")}
        />
      </div>
    </div>
  );
}

function TogglePill({ label, hint, active, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex flex-col items-start rounded-xl px-4 py-2.5 text-left ring-1 transition ${
        active
          ? "bg-emerald-500/15 text-emerald-200 ring-emerald-400/40"
          : "bg-white/5 text-slate-300 ring-white/10 hover:bg-white/10"
      }`}
    >
      <span className="text-sm font-semibold">{label}</span>
      <span className="text-[11px] text-slate-400">{hint}</span>
    </button>
  );
}
