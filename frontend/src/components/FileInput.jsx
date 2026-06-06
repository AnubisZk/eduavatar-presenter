// Reusable file input with concise accepted-format messaging.
import { UploadCloud } from "lucide-react";

export default function FileInput({ label, accept, value, onChange, helper }) {
  return (
    <label className="block rounded-lg border border-dashed border-slate-300 bg-white p-5 transition hover:border-blue-400">
      <div className="flex items-start gap-4">
        <span className="grid h-11 w-11 place-items-center rounded-lg bg-slate-100 text-blue-700">
          <UploadCloud size={22} />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block text-sm font-semibold text-slate-900">{label}</span>
          <span className="mt-1 block text-sm text-slate-500">{value?.name || helper}</span>
          <input
            className="sr-only"
            type="file"
            accept={accept}
            onChange={(event) => onChange(event.target.files?.[0] || null)}
          />
        </span>
      </div>
    </label>
  );
}
