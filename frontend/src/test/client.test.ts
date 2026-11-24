import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "../api/client";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("api.createJob", () => {
  it("envía FormData con vídeo, idioma y modelo", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ id: "abc", status: "pending" }), { status: 200 })
    );
    vi.stubGlobal("fetch", fetchMock);

    const file = new File(["x"], "video.mp4", { type: "video/mp4" });
    const job = await api.createJob({ video: file, language: "es", model: "small" });

    expect(job.id).toBe("abc");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain("/jobs");
    expect(init.method).toBe("POST");
    const body = init.body as FormData;
    expect(body.get("language")).toBe("es");
    expect(body.get("model")).toBe("small");
    expect(body.get("video")).toBeInstanceOf(File);
  });

  it("omite el idioma cuando es 'auto'", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ id: "abc" }), { status: 200 })
    );
    vi.stubGlobal("fetch", fetchMock);

    const file = new File(["x"], "v.mp4", { type: "video/mp4" });
    await api.createJob({ video: file, language: "auto", model: "small" });

    const body = fetchMock.mock.calls[0][1].body as FormData;
    expect(body.get("language")).toBeNull();
  });
});

describe("manejo de errores", () => {
  it("lanza el detalle del backend", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Formato no soportado" }), { status: 400 })
      )
    );
    await expect(api.listJobs()).rejects.toThrow("Formato no soportado");
  });
});

describe("downloadUrl", () => {
  it("construye la URL de descarga", () => {
    expect(api.downloadUrl("xyz")).toBe(`${api.baseUrl}/jobs/xyz/download`);
  });
});

it("enlaza la descarga de subtítulos en ambos formatos", () => {
  expect(api.subtitlesUrl("abc", "srt")).toContain("/jobs/abc/subtitles?format=srt");
  expect(api.subtitlesUrl("abc", "vtt")).toContain("/jobs/abc/subtitles?format=vtt");
});
