import StateIndicator from "./StateIndicator";
import YourLineChart from "./YourLineChart";
import SignalReadout from "./SignalReadout";
import CheckInChat from "./CheckInChat";
import IOSNotification from "./IOSNotification";

/** Maya's phone — the radar. State, "your line," what's driving it, the check-in. */
export default function MayaPhone({ record, assessment, series, domainDays, onDevice }) {
  const elevated = assessment.state !== "GREEN";

  return (
    <div className="flex flex-col gap-3 px-4 py-3">
      {assessment.state === "AMBER" && (
        <IOSNotification
          title="Your line's off"
          body="You've slept less and gone quiet a few days running. Tap to check in."
        />
      )}

      {onDevice && (
        <div className="flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1.5 text-[11px] font-medium text-slate-500">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          On-device · raw data never leaves your phone
        </div>
      )}

      <StateIndicator
        state={assessment.state}
        risk={assessment.risk}
        day={record.day}
        soberDays={record.day}
      />

      <YourLineChart
        series={series}
        current={assessment}
        domainDays={domainDays}
        startedDay={assessment.changepoint?.active ? assessment.changepoint.started_day : null}
      />

      {elevated && assessment.explanation && (
        <div className="rounded-2xl bg-emerald-600 px-4 py-3 text-sm font-medium text-white shadow-sm">
          {assessment.explanation}
        </div>
      )}

      {elevated && <SignalReadout drivers={assessment.drivers} record={record} />}

      {elevated && <CheckInChat awaitingReply />}
    </div>
  );
}
