/** Shared visual language for the GREEN / AMBER / RED states. */
export const STATE_STYLES = {
  GREEN: {
    label: "On track",
    color: "#16a34a",
    soft: "#dcfce7",
    text: "text-emerald-700",
    bg: "bg-emerald-50",
    ring: "ring-emerald-200",
    dot: "bg-emerald-500",
  },
  AMBER: {
    label: "Your line's off",
    color: "#f59e0b",
    soft: "#fef3c7",
    text: "text-amber-700",
    bg: "bg-amber-50",
    ring: "ring-amber-200",
    dot: "bg-amber-500",
  },
  RED: {
    label: "Reach out",
    color: "#dc2626",
    soft: "#fee2e2",
    text: "text-red-700",
    bg: "bg-red-50",
    ring: "ring-red-200",
    dot: "bg-red-500",
  },
};

export const styleFor = (state) => STATE_STYLES[state] ?? STATE_STYLES.GREEN;
