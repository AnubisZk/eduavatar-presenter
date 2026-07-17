// Eight-step creation wizard that collects consent, media, script, language, preview, and export intent.
import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Download, Play, Wand2 } from "lucide-react";

import FileInput from "../components/FileInput.jsx";
import StatusMessage from "../components/StatusMessage.jsx";
import StepIndicator from "../components/StepIndicator.jsx";
import {
  createScriptSections,
  generateAvatar,
  generateVoice,
  getVoiceProviders,
  renderFinal,
  uploadProject,
} from "../services/api.js";

const steps = ["Consent", "Photo/video", "Voice", "Slides", "Script", "Language", "Preview", "Export"];

const languages = ["English", "Turkish", "German", "French", "Spanish", "Italian", "Arabic"];

export default function CreatePage({ studio, setStudio, setActivePage }) {
  const [voiceProviders, setVoiceProviders] = useState(null);
  const {
    currentStep,
    consent,
    files,
    script,
    targetLanguage,
    voiceProvider,
    uploadResult,
    scriptResult,
    voiceResult,
    avatarResult,
    outputResult,
    status,
    statusType,
  } = studio;

  const updateStudio = (patch) => setStudio((previous) => ({ ...previous, ...patch }));
  const updateConsent = (patch) => updateStudio({ consent: { ...consent, ...patch } });
  const updateFiles = (patch) => updateStudio({ files: { ...files, ...patch } });
  const xttsCapability = voiceProviders?.providers?.xtts;
  const xttsUnavailable = !xttsCapability || xttsCapability.available === false;

  useEffect(() => {
    let active = true;
    getVoiceProviders()
      .then((result) => {
        if (active) setVoiceProviders(result);
      })
      .catch(() => {
        if (active) setVoiceProviders({ providers: { xtts: { available: false, reason: "Voice provider status is unavailable." } } });
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (voiceProvider === "xtts" && xttsCapability?.available === false) {
      setStudio((previous) => ({
        ...previous,
        voiceProvider: "edge",
        status: xttsCapability.reason,
        statusType: "error",
      }));
    }
  }, [setStudio, voiceProvider, xttsCapability]);

  const canContinueConsent =
    consent.userName.trim() &&
    consent.imagePermission &&
    consent.voicePermission &&
    consent.purposeAcknowledgement &&
    consent.misuseAcknowledgement;

  const uploadIfReady = async () => {
    if (uploadResult) return uploadResult;
    if (!files.avatar || !files.voice || !files.presentation) {
      throw new Error("Add avatar, voice, and presentation files before uploading.");
    }
    updateStudio({ status: "Uploading files and saving consent record...", statusType: "loading" });
    const uploaded = await uploadProject({ consent, files });
    updateStudio({ uploadResult: uploaded, status: "Upload complete. Slides are ready for narration.", statusType: "success" });
    return uploaded;
  };

  const handleNext = async () => {
    try {
      if (currentStep === 1 && !canContinueConsent) {
        throw new Error("Complete all consent confirmations before continuing.");
      }
      if (currentStep === 2 && !files.avatar) throw new Error("Upload a JPG, PNG, MP4, or MOV avatar source.");
      if (currentStep === 3 && !files.voice) throw new Error("Upload a WAV or MP3 voice sample.");
      if (currentStep === 4) await uploadIfReady();
      if (currentStep === 5 && !script.trim()) throw new Error("Enter or paste a presentation script.");
      if (currentStep === 6) await handleScript();
      updateStudio({ currentStep: Math.min(8, currentStep + 1) });
    } catch (error) {
      updateStudio({ status: error.message, statusType: "error" });
    }
  };

  const handleScript = async () => {
    const uploaded = await uploadIfReady();
    updateStudio({ status: "Dividing script into slide narration sections...", statusType: "loading" });
    const sectioned = await createScriptSections({
      project_id: uploaded.project_id,
      original_script: script,
      target_language: targetLanguage,
      slide_count: uploaded.slides.length || 1,
    });
    updateStudio({ scriptResult: sectioned, status: "Script sections created for each slide.", statusType: "success" });
    return sectioned;
  };

  const handleGeneratePreview = async () => {
    try {
      const uploaded = await uploadIfReady();
      const sectioned = scriptResult || (await handleScript());
      updateStudio({
        status: voiceProvider === "xtts" ? "Cloning the uploaded voice and generating narration..." : "Generating natural narration audio...",
        statusType: "loading",
      });
      const voice = await generateVoice({
        project_id: uploaded.project_id,
        script_sections: sectioned.sections,
        target_language: targetLanguage,
        voice_sample_path: uploaded.file_paths.voice,
        provider: voiceProvider,
      });
      updateStudio({ voiceResult: voice, status: "Generating lip-synced moving avatar clips...", statusType: "loading" });
      const avatar = await generateAvatar({
        project_id: uploaded.project_id,
        avatar_source_path: uploaded.file_paths.avatar,
        audio_files: voice.audio_files.map((item) => item.path),
        provider: "animated",
      });
      updateStudio({
        voiceResult: voice,
        avatarResult: avatar,
        status: "Preview assets generated.",
        statusType: "success",
        currentStep: 8,
      });
      setActivePage("preview");
    } catch (error) {
      updateStudio({ status: error.message, statusType: "error" });
    }
  };

  const handleExport = async () => {
    try {
      if (!uploadResult || !scriptResult || !voiceResult || !avatarResult) {
        await handleGeneratePreview();
        return;
      }
      updateStudio({ status: "Rendering final MP4 with FFmpeg...", statusType: "loading" });
      const rendered = await renderFinal({
        project_id: uploadResult.project_id,
        slide_paths: uploadResult.slides.map((item) => item.path),
        audio_files: voiceResult.audio_files.map((item) => item.path),
        avatar_videos: avatarResult.avatar_videos.map((item) => item.path),
        narration_sections: scriptResult.sections.map((item) => item.text),
        include_subtitles: true,
      });
      updateStudio({ outputResult: rendered, status: "Final MP4 rendered.", statusType: "success" });
      setActivePage("output");
    } catch (error) {
      updateStudio({ status: error.message, statusType: "error" });
    }
  };

  return (
    <section className="space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div>
          <p className="text-sm font-semibold text-blue-700">Create Avatar Presentation</p>
          <h2 className="mt-1 text-3xl font-bold text-slate-950">Step-by-step production wizard</h2>
        </div>
        <div className="text-sm text-slate-500">Project ID: {uploadResult?.project_id || "created after upload"}</div>
      </div>
      <StepIndicator steps={steps} currentStep={currentStep} />
      <StatusMessage type={statusType} message={status} />
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        {currentStep === 1 && (
          <div className="space-y-5">
            <label className="block">
              <span className="text-sm font-medium text-slate-800">User name</span>
              <input
                className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-blue-600"
                value={consent.userName}
                onChange={(event) => updateConsent({ userName: event.target.value })}
                placeholder="Enter the responsible user's name"
              />
            </label>
            {[
              ["imagePermission", "I have permission to use this person's image/video."],
              ["voicePermission", "I have permission to use this person's voice."],
              ["purposeAcknowledgement", "I understand that this avatar will be generated only for educational, presentation, or promotional purposes."],
              ["misuseAcknowledgement", "I will not use this system for impersonation, fraud, political manipulation, or harmful content."],
            ].map(([key, label]) => (
              <label key={key} className="flex gap-3 rounded-md border border-slate-200 p-4 text-sm text-slate-700">
                <input
                  type="checkbox"
                  className="mt-1 h-4 w-4"
                  checked={consent[key]}
                  onChange={(event) => updateConsent({ [key]: event.target.checked })}
                />
                <span>{label}</span>
              </label>
            ))}
          </div>
        )}
        {currentStep === 2 && (
          <FileInput
            label="Upload person's photo or short video"
            accept=".jpg,.jpeg,.png,.mp4,.mov"
            value={files.avatar}
            onChange={(file) => updateFiles({ avatar: file })}
            helper="Accepted formats: JPG, PNG, MP4, MOV"
          />
        )}
        {currentStep === 3 && (
          <div className="space-y-5">
            <FileInput
              label="Upload voice sample with consent (reference)"
              accept=".wav,.mp3"
              value={files.voice}
              onChange={(file) => updateFiles({ voice: file })}
              helper="Use 6-30 seconds of clear speech with little background noise. Accepted formats: WAV, MP3."
            />
            <label className="block max-w-xl">
              <span className="text-sm font-medium text-slate-800">Narration voice</span>
              <select
                className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-blue-600"
                value={voiceProvider}
                onChange={(event) => updateStudio({
                  voiceProvider: event.target.value,
                  voiceResult: null,
                  avatarResult: null,
                  outputResult: null,
                })}
              >
                <option value="edge">Standard neural voice (fast)</option>
                <option value="xtts" disabled={xttsUnavailable}>
                  Clone the uploaded voice with XTTS{xttsUnavailable ? " (not enabled)" : ""}
                </option>
              </select>
              <span className="mt-2 block text-xs leading-5 text-slate-500">
                {xttsUnavailable
                  ? xttsCapability?.reason || "Checking whether voice cloning is available..."
                  : "Voice cloning uses the uploaded reference and requires permission from the speaker."}
              </span>
            </label>
          </div>
        )}
        {currentStep === 4 && (
          <FileInput
            label="Upload presentation file"
            accept=".pdf,.pptx"
            value={files.presentation}
            onChange={(file) => updateFiles({ presentation: file })}
            helper="Accepted formats: PDF, PPTX"
          />
        )}
        {currentStep === 5 && (
          <textarea
            className="min-h-72 w-full rounded-md border border-slate-300 p-4 outline-none focus:border-blue-600"
            value={script}
            onChange={(event) => updateStudio({ script: event.target.value })}
            placeholder="Write the full presentation script or paste a product/project description."
          />
        )}
        {currentStep === 6 && (
          <label className="block max-w-md">
            <span className="text-sm font-medium text-slate-800">Target language</span>
            <select
              className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 outline-none focus:border-blue-600"
              value={targetLanguage}
              onChange={(event) => updateStudio({ targetLanguage: event.target.value })}
            >
              {languages.map((language) => (
                <option key={language}>{language}</option>
              ))}
            </select>
          </label>
        )}
        {currentStep === 7 && (
          <div className="space-y-4">
            <p className="text-slate-600">
              Generate {voiceProvider === "xtts" ? "narration in the uploaded voice" : "natural narration"} and a moving, lip-synced avatar preview.
            </p>
            <button
              onClick={handleGeneratePreview}
              className="inline-flex items-center gap-2 rounded-md bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800"
              type="button"
            >
              <Play size={18} />
              Generate preview
            </button>
          </div>
        )}
        {currentStep === 8 && (
          <div className="space-y-4">
            <p className="text-slate-600">Export the final MP4 with slides, avatar, narration audio, and subtitles.</p>
            <button
              onClick={handleExport}
              className="inline-flex items-center gap-2 rounded-md bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-800"
              type="button"
            >
              <Download size={18} />
              Export MP4
            </button>
          </div>
        )}
      </div>
      <div className="flex items-center justify-between">
        <button
          onClick={() => updateStudio({ currentStep: Math.max(1, currentStep - 1) })}
          className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-40"
          disabled={currentStep === 1}
          type="button"
        >
          <ArrowLeft size={18} />
          Back
        </button>
        {currentStep < 7 && (
          <button
            onClick={handleNext}
            className="inline-flex items-center gap-2 rounded-md bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800"
            type="button"
          >
            Continue
            <ArrowRight size={18} />
          </button>
        )}
        {currentStep === 7 && (
          <button
            onClick={handleGeneratePreview}
            className="inline-flex items-center gap-2 rounded-md bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-800"
            type="button"
          >
            <Wand2 size={18} />
            Build preview
          </button>
        )}
      </div>
    </section>
  );
}
