import { motion } from "framer-motion";
import { api } from "../api/client";
import type { Job } from "../types";

interface Props {
  job: Job;
  onReset: () => void;
}

export function DownloadView({ job, onReset }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="mx-auto w-full max-w-lg text-center"
    >
      <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-good/10 ring-1 ring-good/30">
        <svg viewBox="0 0 24 24" className="h-8 w-8 text-good" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M5 13l4 4L19 7" />
        </svg>
      </div>
      <p className="font-mono text-xs uppercase tracking-[0.4em] text-good">paso 04 — listo</p>
      <h2 className="mt-3 font-display text-4xl font-extrabold tracking-tight text-mist">
        Tu vídeo está subtitulado.
      </h2>
      <p className="mt-3 text-mist-dim">{job.original_filename}</p>

      <a
        href={api.downloadUrl(job.id)}
        className="mt-8 flex w-full items-center justify-center gap-2 rounded-xl bg-signal px-6 py-4 font-display text-base font-bold text-ink transition-colors duration-200 hover:bg-signal-bright"
        download
      >
        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M12 4v12m0 0l-4-4m4 4l4-4M4 20h16" />
        </svg>
        Descargar vídeo
      </a>

      <div className="mt-3 flex justify-center gap-4">
        {(["srt", "vtt"] as const).map((formato) => (
          <a key={formato} href={api.subtitlesUrl(job.id, formato)} download
             className="text-sm font-semibold text-signal underline">
            Subtítulos {formato.toUpperCase()}
          </a>
        ))}
      </div>

      <button
        type="button"
        onClick={onReset}
        className="mt-4 w-full cursor-pointer rounded-xl border border-ink-line px-6 py-3 text-sm text-mist-dim transition-colors duration-200 hover:border-mist-dim hover:text-mist"
      >
        Subtitular otro vídeo
      </button>
    </motion.div>
  );
}
