import { useEffect, useMemo, useState } from "react";
import PhoneFrame from "../ui/PhoneFrame";
import MayaPhone from "./MayaPhone";
import SponsorPhone from "./SponsorPhone";
import ModelMonitor from "./ModelMonitor";
import DemoControls from "./DemoControls";
import { buildDemo } from "../../lib/assess";
import { loadDemo } from "../../lib/demoApi";
import { SAMPLE_PLAN } from "../../lib/fixtures";

const STEP_MS = 1100; // auto-advance cadence

/**
 * The live-demo screen (P4). Two phones side by side — Maya's radar and her
 * sponsor's — plus the presenter controls. Everything renders from the
 * RiskAssessment / EscalationEvent series; nothing about the spiral is
 * hardcoded, so it stays correct whether the data is local or from the API.
 */
export default function DemoView({ userId = "maya", plan }) {
  // Drive the demo from the user's authored plan when it's complete; otherwise
  // fall back to the sample so the escalation always has a recipient + message.
  const effectivePlan =
    plan?.message_template?.trim() && plan?.circle?.length ? plan : SAMPLE_PLAN;

  const [mode, setMode] = useState("personal");
  const [onDevice, setOnDevice] = useState(true);
  const [dayIndex, setDayIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  // Seed synchronously so the first paint is never empty; the API refines it.
  const [data, setData] = useState(() => ({ ...buildDemo("personal", effectivePlan), source: "local" }));

  // (Re)load whenever the model toggles. Instant local build, then API enrich.
  useEffect(() => {
    let alive = true;
    setData({ ...buildDemo(mode, effectivePlan), source: "local" });
    loadDemo(userId, { mode, plan: effectivePlan }).then((d) => {
      if (alive) setData(d);
    });
    return () => {
      alive = false;
    };
  }, [mode, effectivePlan, userId]);

  // Auto-advance while playing; stop at the end.
  const maxIndex = data.stream.length - 1;

  // Pause points: the line first goes off (AMBER), it hits "reach out" (RED),
  // and the sponsor's phone receives the message (notify_circle).
  const milestones = useMemo(() => {
    const set = new Set();
    const firstOff = data.assessments.findIndex((a) => a.state !== "GREEN");
    if (firstOff >= 0) set.add(firstOff);
    const reachOut = data.assessments.findIndex((a) => a.state === "RED");
    if (reachOut >= 0) set.add(reachOut);
    const notify = data.timeline.find((e) => e.type === "notify_circle");
    if (notify) {
      const ni = data.stream.findIndex((r) => r.day === notify.day);
      if (ni >= 0) set.add(ni);
    }
    return set;
  }, [data]);

  // Advance one day at a time; pause at each milestone and at the end.
  useEffect(() => {
    if (!playing) return undefined;
    if (dayIndex >= maxIndex) {
      setPlaying(false);
      return undefined;
    }
    const id = setTimeout(() => {
      const next = dayIndex + 1;
      setDayIndex(next);
      if (next >= maxIndex || milestones.has(next)) setPlaying(false);
    }, STEP_MS);
    return () => clearTimeout(id);
  }, [playing, dayIndex, maxIndex, milestones]);

  // Pressing play after the run has finished restarts it from the beginning.
  const togglePlay = () => {
    if (!playing && dayIndex >= maxIndex) {
      setDayIndex(0);
      setPlaying(true);
      return;
    }
    setPlaying((p) => !p);
  };

  const idx = Math.min(dayIndex, maxIndex);
  const record = data.stream[idx];
  const assessment = data.assessments[idx];
  const domainDays = [data.stream[0].day, data.stream[maxIndex].day];

  // The sponsor only sees the notify_circle event once its day has arrived.
  const sponsorEvent =
    [...data.timeline]
      .filter((e) => e.type === "notify_circle" && e.day <= record.day)
      .sort((a, b) => b.day - a.day)[0] ?? null;

  return (
    <div className="flex flex-col items-center gap-8">
      <span
        className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${
          data.source === "api"
            ? "bg-emerald-500/15 text-emerald-300"
            : "bg-slate-500/15 text-slate-300"
        }`}
      >
        <span
          className={`h-1.5 w-1.5 rounded-full ${
            data.source === "api" ? "bg-emerald-400" : "bg-slate-400"
          }`}
        />
        {data.source === "api" ? "live model · API" : "offline model"}
      </span>

      <div className="flex flex-wrap items-start justify-center gap-8">
        <div className="flex flex-col items-center gap-5">
          <span className="text-lg font-bold tracking-tight text-slate-100">
            Maya's phone
          </span>
          <PhoneFrame title="Your line">
            <MayaPhone
              record={record}
              assessment={assessment}
              series={data.assessments}
              domainDays={domainDays}
              onDevice={onDevice}
            />
          </PhoneFrame>
        </div>

        <div className="flex flex-col items-center gap-5">
          <span className="text-lg font-bold tracking-tight text-slate-100">
            Sponsor's phone
          </span>
          <PhoneFrame title={sponsorEvent ? sponsorEvent.recipient : effectivePlan?.circle?.[0]?.name ?? "Dana"}>
            <SponsorPhone
              event={sponsorEvent}
              contact={effectivePlan?.circle?.[0]?.contact}
              userName="Maya"
            />
          </PhoneFrame>
        </div>

        <div className="flex flex-col items-center gap-5">
          <span className="text-lg font-bold tracking-tight text-slate-100">
            Backend AI Model
          </span>
          <ModelMonitor
            record={record}
            assessment={assessment}
            timeline={data.timeline}
            source={data.source}
          />
        </div>
      </div>

      <DemoControls
        dayIndex={idx}
        maxIndex={maxIndex}
        currentDay={record.day}
        onIndexChange={setDayIndex}
        playing={playing}
        onTogglePlay={togglePlay}
        onDevice={onDevice}
        onToggleOnDevice={setOnDevice}
        mode={mode}
        onModeChange={setMode}
      />

      {mode === "population" && (
        <p className="max-w-md text-center text-xs leading-relaxed text-slate-400">
          The population model uses generic averages — it under-reacts to Maya's
          own drift and misses the spiral. Flip back to the personal model to see
          it caught.
        </p>
      )}
    </div>
  );
}
