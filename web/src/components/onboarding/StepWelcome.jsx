/** Step 1 — a warm, consent-first welcome that frames the Ulysses contract. */
export default function StepWelcome() {
  return (
    <div className="flex flex-col gap-5">
      <div className="grid h-16 w-16 place-items-center rounded-2xl bg-emerald-50 text-3xl">
        🪢
      </div>
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Write your catch-plan</h2>
        <p className="mt-2 text-sm leading-relaxed text-slate-600">
          While things are steady, decide what should happen if your line goes
          off. You choose who's reached, and the words they'll get — written by
          you, for you.
        </p>
      </div>
      <ul className="flex flex-col gap-2 text-sm text-slate-600">
        <li className="flex items-center gap-2">📍 Mark the places that feel risky</li>
        <li className="flex items-center gap-2">🤝 Choose the person who catches you</li>
        <li className="flex items-center gap-2">✍️ Write the message in your words</li>
        <li className="flex items-center gap-2">🎚️ Set when it should reach out</li>
      </ul>
      <p className="rounded-xl bg-slate-50 px-4 py-3 text-xs leading-relaxed text-slate-500">
        Nothing leaves your phone but the message you write — and only when your
        own rule says so. Revocable in one tap, any time.
      </p>
    </div>
  );
}
