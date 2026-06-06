// Small status surface for errors, loading updates, and successful workflow messages.
import { AlertCircle, CheckCircle2, Loader2 } from "lucide-react";

export default function StatusMessage({ type = "info", message }) {
  if (!message) return null;
  const iconMap = {
    error: AlertCircle,
    success: CheckCircle2,
    loading: Loader2,
  };
  const Icon = iconMap[type] || CheckCircle2;
  const colorClass =
    type === "error"
      ? "border-red-200 bg-red-50 text-red-800"
      : type === "loading"
        ? "border-blue-200 bg-blue-50 text-blue-800"
        : "border-emerald-200 bg-emerald-50 text-emerald-800";
  return (
    <div className={`flex items-center gap-2 rounded-lg border px-4 py-3 text-sm ${colorClass}`}>
      <Icon className={type === "loading" ? "animate-spin" : ""} size={18} />
      <span>{message}</span>
    </div>
  );
}
