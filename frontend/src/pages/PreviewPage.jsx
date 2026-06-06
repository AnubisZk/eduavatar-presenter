// Preview page showing slides, avatar clip, narration, language, and render actions.
import { Download, Film, Play } from "lucide-react";

import StatusMessage from "../components/StatusMessage.jsx";
import { renderFinal, toAbsoluteUrl } from "../services/api.js";

export default function PreviewPage({ studio, setStudio, setActivePage }) {
  const currentSlide = studio.uploadResult?.slides?.[0];
  const firstAvatar = studio.avatarResult?.avatar_videos?.[0];
  const firstSection = studio.scriptResult?.sections?.[0];

  const handleExport = async () => {
    try {
      if (!studio.uploadResult || !studio.voiceResult || !studio.avatarResult || !studio.scriptResult) {
        throw new Error("Generate preview assets before exporting.");
      }
      setStudio((previous) => ({ ...previous, status: "Rendering final MP4 with FFmpeg...", statusType: "loading" }));
      const rendered = await renderFinal({
        project_id: studio.uploadResult.project_id,
        slide_paths: studio.uploadResult.slides.map((item) => item.path),
        audio_files: studio.voiceResult.audio_files.map((item) => item.path),
        avatar_videos: studio.avatarResult.avatar_videos.map((item) => item.path),
        narration_sections: studio.scriptResult.sections.map((item) => item.text),
        include_subtitles: true,
      });
      setStudio((previous) => ({ ...previous, outputResult: rendered, status: "Final MP4 rendered.", statusType: "success" }));
      setActivePage("output");
    } catch (error) {
      setStudio((previous) => ({ ...previous, status: error.message, statusType: "error" }));
    }
  };

  return (
    <section className="space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <p className="text-sm font-semibold text-blue-700">Preview</p>
          <h2 className="mt-1 text-3xl font-bold text-slate-950">Presentation playback workspace</h2>
        </div>
        <button
          onClick={handleExport}
          className="inline-flex items-center gap-2 rounded-md bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-800"
          type="button"
        >
          <Download size={18} />
          Generate video
        </button>
      </div>
      <StatusMessage type={studio.statusType} message={studio.status} />
      <div className="grid gap-5 lg:grid-cols-[1fr_340px]">
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <div className="relative overflow-hidden rounded-md bg-slate-900">
            {currentSlide ? (
              <img className="aspect-video w-full object-contain" src={toAbsoluteUrl(currentSlide.url)} alt="Current slide" />
            ) : (
              <div className="grid aspect-video place-items-center text-slate-300">No slide preview yet</div>
            )}
            <div className="absolute bottom-5 right-5 h-32 w-32 overflow-hidden rounded-lg border-4 border-white bg-slate-800 shadow-lg">
              {firstAvatar?.url?.endsWith(".mp4") ? (
                <video className="h-full w-full object-cover" src={toAbsoluteUrl(firstAvatar.url)} muted autoPlay loop playsInline />
              ) : firstAvatar?.url ? (
                <img className="h-full w-full object-cover" src={toAbsoluteUrl(firstAvatar.url)} alt="Avatar preview" />
              ) : (
                <div className="grid h-full place-items-center text-xs text-slate-300">Avatar</div>
              )}
            </div>
          </div>
        </div>
        <aside className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
            <Film size={18} className="text-blue-700" />
            Slide 1 narration
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-600">{firstSection?.text || "Generate a preview to see narration."}</p>
          <dl className="mt-6 grid gap-3 text-sm">
            <div className="flex justify-between gap-3">
              <dt className="text-slate-500">Language</dt>
              <dd className="font-medium text-slate-900">{studio.targetLanguage}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-slate-500">Slides</dt>
              <dd className="font-medium text-slate-900">{studio.uploadResult?.slides?.length || 0}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-slate-500">Preview clips</dt>
              <dd className="font-medium text-slate-900">{studio.avatarResult?.avatar_videos?.length || 0}</dd>
            </div>
          </dl>
          <button
            onClick={() => setActivePage("create")}
            className="mt-6 inline-flex w-full items-center justify-center gap-2 rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            type="button"
          >
            <Play size={18} />
            Back to wizard
          </button>
        </aside>
      </div>
    </section>
  );
}
