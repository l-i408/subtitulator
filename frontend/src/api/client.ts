import type { Job, SubtitleStyle, TranscriptResponse, TranscriptSegment } from "../types";

const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://localhost:8000";

async function handle<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `Error ${response.status}`;
    try {
      const data = await response.json();
      if (data?.detail) detail = data.detail;
    } catch {
      /* respuesta sin cuerpo JSON */
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export interface CreateJobInput {
  video: File;
  language: string;
  model: string;
}

export const api = {
  baseUrl: BASE_URL,

  async createJob({ video, language, model }: CreateJobInput): Promise<Job> {
    const form = new FormData();
    form.append("video", video);
    if (language && language !== "auto") form.append("language", language);
    if (model) form.append("model", model);
    const res = await fetch(`${BASE_URL}/jobs`, { method: "POST", body: form });
    return handle<Job>(res);
  },

  async listJobs(): Promise<Job[]> {
    return handle<Job[]>(await fetch(`${BASE_URL}/jobs`));
  },

  async getJob(id: string): Promise<Job> {
    return handle<Job>(await fetch(`${BASE_URL}/jobs/${id}`));
  },

  async getTranscript(id: string): Promise<TranscriptResponse> {
    return handle<TranscriptResponse>(await fetch(`${BASE_URL}/jobs/${id}/transcript`));
  },

  async saveTranscript(id: string, segmentos: TranscriptSegment[]): Promise<TranscriptResponse> {
    const res = await fetch(`${BASE_URL}/jobs/${id}/transcript`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ segmentos }),
    });
    return handle<TranscriptResponse>(res);
  },

  async render(id: string, style: SubtitleStyle): Promise<Job> {
    const res = await fetch(`${BASE_URL}/jobs/${id}/render`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(style),
    });
    return handle<Job>(res);
  },

  subtitlesUrl(id: string, format: "srt" | "vtt"): string {
    return `${BASE_URL}/jobs/${id}/subtitles?format=${format}`;
  },

  downloadUrl(id: string): string {
    return `${BASE_URL}/jobs/${id}/download`;
  },
};
