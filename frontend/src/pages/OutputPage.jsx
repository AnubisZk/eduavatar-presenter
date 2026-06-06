// Output page for viewing and downloading the rendered MP4.
import { Download, Video } from "lucide-react";

import StatusMessage from "../components/StatusMessage.jsx";
import { toAbsoluteUrl } from "../services/api.js";

export default function OutputPage({ studio, setActivePage }) {
  const output = studio.outputResult?.output_path;
  const url = toAbsoluteUrl(output?.url);

  return (
    <section className="space-y-6">
      <div>
        <p className="text-sm font-semibold text-blue-700">Output video</p>
        <h2 className="mt-1 text-3xl font-bold text-slate-950">Final MP4 export</h2>
      </div>
      <StatusMessage type={studio.statusType} message={studio.status} />
      <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        {url ? (
          <div className="space-y-4">
            <video className="aspect-video w-full rounded-md bg-slate-900" controls src={url} />
            <a
              className="inline-flex items-center gap-2 rounded-md bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800"
              href={url}
              download
            >
              <Download size={18} />
              Download final MP4
            </a>
          </div>
        ) : (
          <div className="grid min-h-80 place-items-center rounded-md border border-dashed border-slate-300 bg-slate-50 text-center">
            <div>
              <Video className="mx-auto text-slate-400" size={44} />
              <p className="mt-3 font-semibold text-slate-900">No exported video yet</p>
              <button
                onClick={() => setActivePage("preview")}
                className="mt-4 rounded-md bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800"
                type="button"
              >
                Open preview
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
