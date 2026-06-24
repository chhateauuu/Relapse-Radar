import { useState } from "react";
import PhoneFrame from "./components/ui/PhoneFrame";
import OnboardingFlow from "./components/onboarding/OnboardingFlow";
import PlanEditor from "./components/plan/PlanEditor";
import DemoView from "./components/demo/DemoView";
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

/** Top-level switch between the live demo (P4) and the catch-plan flow (P5). */
function ViewTabs({ view, onChange }) {
  const tabs = [
    { id: "demo", label: "Live demo" },
    { id: "plan", label: "My plan" },
  ];
  return (
    <div className="inline-flex rounded-full bg-white/5 p-1 ring-1 ring-white/10">
      {tabs.map((t) => (
        <button
          key={t.id}
          type="button"
          onClick={() => onChange(t.id)}
          className={`rounded-full px-4 py-1.5 text-sm font-semibold transition ${
            view === t.id
              ? "bg-emerald-600 text-white"
              : "text-slate-300 hover:text-white"
          }`}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

export default function App() {
  const { plan, patch, source, paused, saving, savedAt, save, togglePause, deletePlan } =
    usePlan(USER_ID);
  const [view, setView] = useState("demo");
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
    <div className="flex min-h-screen flex-col items-center gap-6 px-4 py-10">
      <header className="flex flex-col items-center gap-3 text-center">
        <h1 className="text-2xl font-bold tracking-tight text-white">Relapse Radar</h1>
        <p className="max-w-md text-sm text-slate-400">
          Catches you in your worst moment — through the person you trust, using
          a plan you wrote in your best moment.
        </p>
        <ViewTabs view={view} onChange={setView} />
      </header>

      {view === "demo" ? (
        <DemoView userId={USER_ID} plan={plan} />
      ) : (
        <div className="flex flex-col items-center gap-4">
          <SourceBadge source={source} />
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
      )}
    </div>
  );
}
