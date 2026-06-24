import { useMemo, useState } from "react";
import Button from "../ui/Button";
import ProgressDots from "../ui/ProgressDots";
import { validatePlan } from "../../lib/plan";
import StepWelcome from "./StepWelcome";
import StepPerson from "./StepPerson";
import StepPlaces from "./StepPlaces";
import StepMessage from "./StepMessage";
import StepThresholds from "./StepThresholds";
import StepReview from "./StepReview";

/**
 * The onboarding wizard. Walks the user through authoring a CatchPlan, gating
 * each step on the fields that step is responsible for, then hands a valid plan
 * to `onComplete` for saving.
 */
const STEPS = [
  { Component: StepWelcome, gate: () => [] },
  { Component: StepPerson, gate: () => ["sponsorName", "sponsorContact"] },
  { Component: StepPlaces, gate: () => [] },
  { Component: StepMessage, gate: () => ["message"] },
  { Component: StepThresholds, gate: () => ["sustainedDays"] },
  { Component: StepReview, gate: () => [] },
];

export default function OnboardingFlow({ plan, patch, onComplete, saving }) {
  const [index, setIndex] = useState(0);
  const [showErrors, setShowErrors] = useState(false);

  const allIssues = useMemo(() => validatePlan(plan), [plan]);
  const { Component, gate } = STEPS[index];
  const stepIssues = gate(plan).filter((key) => allIssues[key]);
  const errors = showErrors
    ? Object.fromEntries(stepIssues.map((key) => [key, allIssues[key]]))
    : {};

  const isLast = index === STEPS.length - 1;

  const next = () => {
    if (stepIssues.length > 0) {
      setShowErrors(true);
      return;
    }
    setShowErrors(false);
    if (isLast) onComplete();
    else setIndex((i) => i + 1);
  };

  const back = () => {
    setShowErrors(false);
    setIndex((i) => Math.max(0, i - 1));
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between px-6 pt-3">
        <ProgressDots count={STEPS.length} current={index} />
        <span className="text-xs font-medium text-slate-400">
          {index + 1} / {STEPS.length}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-5">
        <Component plan={plan} patch={patch} errors={errors} />
      </div>

      <div className="flex items-center justify-between gap-3 border-t border-slate-100 px-6 py-4">
        <Button variant="ghost" onClick={back} disabled={index === 0 || saving}>
          Back
        </Button>
        <Button onClick={next} disabled={saving} className="min-w-28">
          {saving ? "Saving…" : isLast ? "Activate plan" : "Continue"}
        </Button>
      </div>
    </div>
  );
}
