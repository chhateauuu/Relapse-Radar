/** Phone shell with a status bar so the flow reads as a real app. */
export default function PhoneFrame({ title = "Catch-plan", children }) {
  return (
    <div className="phone-frame">
      <div className="phone-notch" />
      <div className="flex items-center justify-between px-6 pt-2.5 pb-1 text-[11px] font-semibold text-slate-500">
        <span>9:41</span>
        <span className="tracking-wide">{title}</span>
        <span className="flex items-center gap-1">
          <span>5G</span>
          <span>100%</span>
        </span>
      </div>
      <div className="flex-1 overflow-y-auto">{children}</div>
    </div>
  );
}
