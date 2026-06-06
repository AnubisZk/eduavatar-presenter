// Visual progress tracker for the eight-step creation wizard.
import { Check } from "lucide-react";

export default function StepIndicator({ steps, currentStep }) {
  return (
    <div className="grid gap-2 md:grid-cols-4 xl:grid-cols-8">
      {steps.map((step, index) => {
        const stepNumber = index + 1;
        const complete = stepNumber < currentStep;
        const active = stepNumber === currentStep;
        return (
          <div
            key={step}
            className={`rounded-lg border px-3 py-3 ${
              active
                ? "border-blue-600 bg-blue-50"
                : complete
                  ? "border-emerald-300 bg-emerald-50"
                  : "border-slate-200 bg-white"
            }`}
          >
            <div className="flex items-center gap-2">
              <span
                className={`grid h-6 w-6 place-items-center rounded-full text-xs font-semibold ${
                  complete ? "bg-emerald-600 text-white" : active ? "bg-blue-700 text-white" : "bg-slate-200 text-slate-600"
                }`}
              >
                {complete ? <Check size={14} /> : stepNumber}
              </span>
              <span className="text-sm font-medium text-slate-800">{step}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
