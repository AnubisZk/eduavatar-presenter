// Home page that presents the studio purpose and guides users into the workflow.
import { ArrowRight, BadgeCheck, Languages, ShieldCheck } from "lucide-react";

export default function HomePage({ setActivePage }) {
  return (
    <section className="grid gap-8 lg:grid-cols-[1fr_420px] lg:items-center">
      <div className="py-8">
        <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Erasmus+ / VET ready</p>
        <h1 className="mt-4 max-w-3xl text-4xl font-bold text-slate-950 sm:text-5xl">
          EduAvatar Presenter Studio
        </h1>
        <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-600">
          Create consent-based avatar presentations from a photo or short video, a voice sample, a script, and PDF or PPTX slides.
        </p>
        <button
          onClick={() => setActivePage("create")}
          className="mt-7 inline-flex items-center gap-2 rounded-md bg-blue-700 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-800"
          type="button"
        >
          Start project
          <ArrowRight size={18} />
        </button>
      </div>
      <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="aspect-video rounded-md bg-[linear-gradient(135deg,#dbeafe,#f8fafc_55%,#dcfce7)] p-5">
          <div className="flex h-full flex-col justify-between">
            <div className="rounded-md bg-white/85 p-4 shadow-sm">
              <div className="h-4 w-48 rounded bg-blue-700" />
              <div className="mt-4 grid gap-2">
                <div className="h-3 w-full rounded bg-slate-200" />
                <div className="h-3 w-2/3 rounded bg-slate-200" />
              </div>
            </div>
            <div className="ml-auto h-24 w-24 rounded-lg border-4 border-white bg-slate-900 shadow-lg" />
          </div>
        </div>
        <div className="mt-5 grid gap-3">
          {[
            [ShieldCheck, "Consent is required before uploads."],
            [Languages, "Scripts can be organized by slide and language."],
            [BadgeCheck, "CPU-friendly lip sync works locally; SadTalker and Wav2Lip can be connected for higher realism."],
          ].map(([Icon, text]) => (
            <div className="flex items-center gap-3 text-sm text-slate-700" key={text}>
              <Icon className="text-blue-700" size={18} />
              {text}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
