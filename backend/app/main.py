from contextlib import asynccontextmanager
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, File, Form, Query, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from app.config import settings
from app.database import init_db
from app.logger import get_logger
from app.schemas import JobResponse, SubtitleStyle, TranscriptPayload, TranscriptResponse
from app.services import job_service
from app.services.subtitle_service import exportar_subtitulos


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = get_logger("api")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Error inesperado en %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
    )


@app.get("/health")
async def healthcheck():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.post("/jobs", response_model=JobResponse)
async def create_job(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    language: str | None = Form(default=None),
    model: str | None = Form(default=None),
):
    job = await job_service.create_job(video, language, model)
    background_tasks.add_task(job_service.process_transcription, job["id"])
    return job


@app.get("/jobs", response_model=list[JobResponse])
async def list_jobs():
    return job_service.list_jobs()


@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str):
    return job_service.get_job(job_id)


@app.get("/jobs/{job_id}/transcript", response_model=TranscriptResponse)
async def get_transcript(job_id: str):
    return job_service.get_transcript(job_id)


@app.put("/jobs/{job_id}/transcript", response_model=TranscriptResponse)
async def update_transcript(job_id: str, transcript: TranscriptPayload):
    return job_service.save_transcript(job_id, transcript)


@app.post("/jobs/{job_id}/render", response_model=JobResponse)
async def render_job(job_id: str, style: SubtitleStyle, background_tasks: BackgroundTasks):
    job = job_service.start_render(job_id)
    background_tasks.add_task(job_service.render_job, job_id, style)
    return job


@app.get("/jobs/{job_id}/subtitles")
async def descargar_subtitulos(job_id: str, formato: Literal["srt", "vtt"] = Query("srt", alias="format")):
    segmentos = job_service.get_transcript(job_id)["segmentos"]
    return Response(
        content=exportar_subtitulos(segmentos, formato),
        media_type="text/vtt" if formato == "vtt" else "application/x-subrip",
        headers={"Content-Disposition": f'attachment; filename="subtitulos.{formato}"'},
    )


@app.get("/jobs/{job_id}/download")
async def download_job(job_id: str):
    output_path = job_service.get_download_path(job_id)
    return FileResponse(
        output_path,
        media_type="video/mp4",
        filename=f"{job_id}_subtitulado.mp4",
    )
