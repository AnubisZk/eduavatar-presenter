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

async function apiFetch(path, options) {
  try {
    return await fetch(`${API_BASE_URL}${path}`, options);
  } catch {
    throw new Error(
      `The presentation backend could not be reached at ${API_BASE_URL}. Check the deployment and try again.`
    );
  }
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
    await apiFetch("/upload", {
      method: "POST",
      body: formData,
    })
  );
}

export async function createScriptSections(payload) {
  // This endpoint divides a manual script into slide-level narration chunks.
  return parseResponse(
    await apiFetch("/presentation/script", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}

export async function generateVoice(payload) {
  // The selected voice provider returns one narration file per slide.
  return parseResponse(
    await apiFetch("/voice/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}

export async function generateAvatar(payload) {
  // The selected avatar provider returns one synchronized clip per slide.
  return parseResponse(
    await apiFetch("/avatar/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}

export async function renderFinal(payload) {
  // Final render composes slides, avatar clips, narration audio, and optional subtitles.
  return parseResponse(
    await apiFetch("/render/final", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}

export { API_BASE_URL, toAbsoluteUrl };
