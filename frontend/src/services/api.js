// Centralized API helper so model integrations can evolve without touching UI components.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const toAbsoluteUrl = (url) => {
  if (!url) return "";
  return url.startsWith("http") ? url : `${API_BASE_URL}${url}`;
};

async function parseResponse(response) {
  // FastAPI returns useful JSON errors; surface them as readable UI messages.
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "The server could not complete this request.");
  }
  return data;
}

export async function uploadProject({ consent, files }) {
  // Consent and files are sent together because uploads are blocked until all confirmations are true.
  const formData = new FormData();
  formData.append("user_name", consent.userName);
  formData.append("image_permission", consent.imagePermission);
  formData.append("voice_permission", consent.voicePermission);
  formData.append("purpose_acknowledgement", consent.purposeAcknowledgement);
  formData.append("misuse_acknowledgement", consent.misuseAcknowledgement);
  formData.append("avatar_file", files.avatar);
  formData.append("voice_file", files.voice);
  formData.append("presentation_file", files.presentation);

  return parseResponse(
    await fetch(`${API_BASE_URL}/upload`, {
      method: "POST",
      body: formData,
    })
  );
}

export async function createScriptSections(payload) {
  // This endpoint divides a manual script into slide-level narration chunks.
  return parseResponse(
    await fetch(`${API_BASE_URL}/presentation/script`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}

export async function generateVoice(payload) {
  // Placeholder TTS returns one silent WAV per slide.
  return parseResponse(
    await fetch(`${API_BASE_URL}/voice/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}

export async function generateAvatar(payload) {
  // Placeholder avatar generation returns one short clip or image preview per slide.
  return parseResponse(
    await fetch(`${API_BASE_URL}/avatar/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}

export async function renderFinal(payload) {
  // Final render composes slides, avatar clips, narration audio, and optional subtitles.
  return parseResponse(
    await fetch(`${API_BASE_URL}/render/final`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}

export { API_BASE_URL, toAbsoluteUrl };
