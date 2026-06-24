/**
 * The empathic check-in. When the line drifts, the app nudges Maya *first* —
 * a calm HALT-style message (filled by the LLM at integration). She doesn't
 * answer, which is exactly what later triggers the escalation.
 */
export default function CheckInChat({ explanation, awaitingReply }) {
  return (
    <div className="rounded-2xl bg-white px-4 py-3 ring-1 ring-slate-100">
      <p className="mb-2 text-xs font-semibold text-slate-500">Check-in</p>
      <div className="flex flex-col gap-2">
        {explanation && (
          <div className="max-w-[85%] self-start rounded-2xl rounded-bl-sm bg-emerald-50 px-3 py-2 text-sm text-emerald-900">
            {explanation}
          </div>
        )}
        <div className="max-w-[85%] self-start rounded-2xl rounded-bl-sm bg-slate-100 px-3 py-2 text-sm text-slate-700">
          Hey — noticing your line's off. HALT check: how are you doing right now?
        </div>
        {awaitingReply && (
          <div className="self-end pr-1 text-xs italic text-slate-400">
            no reply yet…
          </div>
        )}
      </div>
    </div>
  );
}
