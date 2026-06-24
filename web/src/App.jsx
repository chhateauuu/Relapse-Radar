import { useState } from "react";
import PhoneFrame from "./components/ui/PhoneFrame";
import OnboardingFlow from "./components/onboarding/OnboardingFlow";
import PlanEditor from "./components/plan/PlanEditor";
import { usePlan } from "./hooks/usePlan";

const USER_ID = "maya";

/** A small badge showing whether we're wired to the live API or local fallback. */
function SourceBadge({ source }) {
  const live = source === "api";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${
        live ? "bg-emerald-500/15 text-emerald-300" : "bg-slate-500/15 text-slate-300"
      }`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${live ? "bg-emerald-400" : "bg-slate-400"}`}
      />
      {source === "loading" ? "connecting…" : live ? "live API" : "offline demo"}
    </span>
  );
}

export default function App() {
  const { plan, patch, source, paused, saving, savedAt, save, togglePause, deletePlan } =
    usePlan(USER_ID);
  const [mode, setMode] = useState("onboarding");

  const handleComplete = async () => {
    await save();
    setMode("editor");
  };

  const handleDelete = async () => {
    await deletePlan();
    setMode("onboarding");
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-6 px-4 py-10">
      <header className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold tracking-tight text-white">
          Relapse Radar
        </h1>
        <p className="max-w-md text-sm text-slate-400">
          Your catch-plan — a contract you write while you're well, so the right
          help finds you when it's hard.
        </p>
        <SourceBadge source={source} />
      </header>

      <PhoneFrame title={mode === "onboarding" ? "Setup" : "Catch-plan"}>
        {mode === "onboarding" ? (
          <OnboardingFlow
            plan={plan}
            patch={patch}
            saving={saving}
            onComplete={handleComplete}
          />
        ) : (
          <PlanEditor
            plan={plan}
            patch={patch}
            saving={saving}
            savedAt={savedAt}
            paused={paused}
            onSave={save}
            onTogglePause={togglePause}
            onDelete={handleDelete}
            onRestart={() => setMode("onboarding")}
          />
        )}
      </PhoneFrame>
    </div>
  );
}
