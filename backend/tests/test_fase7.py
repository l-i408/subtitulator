"""Fase 7 — Integración end-to-end del flujo completo vía HTTP.

Se simulan Whisper (transcribir) y FFmpeg (extraer_audio, quemar_subtitulos,
obtener_duracion) para validar el contrato completo sin dependencias pesadas.
Las BackgroundTasks de FastAPI se ejecutan de forma síncrona con TestClient.
"""
from fastapi.testclient import TestClient

from app.database import get_connection, init_db
from app.main import app
from app.schemas import JobStatus
from app.services import job_service


client = TestClient(app)


def _limpiar():
    init_db()
    with get_connection() as connection:
        connection.execute("DELETE FROM jobs WHERE original_filename = 'e2e.mp4'")


def _mock_pipeline(monkeypatch, tmp_path):
    audio = tmp_path / "audio.wav"
    audio.write_bytes(b"RIFF")

    monkeypatch.setattr(job_service, "obtener_duracion", lambda path: 12.0)
    monkeypatch.setattr(job_service, "extraer_audio", lambda path: str(audio))
    monkeypatch.setattr(
        job_service,
        "transcribir",
        lambda path, language: [
            {"inicio": 0.0, "fin": 2.0, "texto": "Hola mundo"},
            {"inicio": 2.0, "fin": 4.0, "texto": "segundo segmento"},
        ],
    )

    def fake_quemar(video_path, subtitles_path, output_path):
        with open(output_path, "wb") as file:
            file.write(b"VIDEO-RENDERIZADO")
        return output_path

    monkeypatch.setattr(job_service, "quemar_subtitulos", fake_quemar)


class TestFlujoCompleto:
    def test_pipeline_e2e_completo(self, monkeypatch, tmp_path):
        _limpiar()
        _mock_pipeline(monkeypatch, tmp_path)

        # 1. Subir vídeo → transcripción en background
        create = client.post(
            "/jobs",
            data={"language": "es", "model": "small"},
            files={"video": ("e2e.mp4", b"contenido-de-video", "video/mp4")},
        )
        assert create.status_code == 200
        job_id = create.json()["id"]

        # 2. Tras el background, el job está transcrito
        status = client.get(f"/jobs/{job_id}").json()
        assert status["status"] == JobStatus.transcribed.value
        assert status["progress"] == 100

        # 3. Obtener la transcripción
        transcript = client.get(f"/jobs/{job_id}/transcript").json()
        assert len(transcript["segmentos"]) == 2
        assert transcript["segmentos"][0]["texto"] == "Hola mundo"

        # 4. Editar y guardar la transcripción
        editado = {
            "segmentos": [
                {"inicio": 0.0, "fin": 2.0, "texto": "Hola mundo corregido"},
                {"inicio": 2.0, "fin": 4.0, "texto": "segundo segmento"},
            ]
        }
        put = client.put(f"/jobs/{job_id}/transcript", json=editado)
        assert put.status_code == 200
        assert put.json()["segmentos"][0]["texto"] == "Hola mundo corregido"

        # Las dos descargas usan la transcripción editada.
        for formato, separador in [("srt", ","), ("vtt", ".")]:
            respuesta = client.get(f"/jobs/{job_id}/subtitles", params={"format": formato})
            assert respuesta.status_code == 200
            assert respuesta.headers["content-disposition"] == f'attachment; filename="subtitulos.{formato}"'
            cabecera = "1\n" if formato == "srt" else "WEBVTT\n\n"
            assert respuesta.text.startswith(
                f"{cabecera}00:00:00{separador}000 --> 00:00:02{separador}000\nHola mundo corregido\n"
            )
        assert client.get(f"/jobs/{job_id}/subtitles?format=pdf").status_code == 422

        # 5. Renderizar con estilo → quemado en background
        render = client.post(
            f"/jobs/{job_id}/render",
            json={
                "font": "Arial",
                "font_size": 48,
                "color": "#FFFFFF",
                "outline_color": "#000000",
                "position": "bottom",
            },
        )
        assert render.status_code == 200

        # 6. El job queda completado
        done = client.get(f"/jobs/{job_id}").json()
        assert done["status"] == JobStatus.done.value
        assert done["progress"] == 100

        # 7. Se descarga el vídeo de salida generado (.ass real + quemado simulado)
        download = client.get(f"/jobs/{job_id}/download")
        assert download.status_code == 200
        assert download.content == b"VIDEO-RENDERIZADO"

    def test_validacion_y_transcripcion_no_interfieren_entre_jobs(self, monkeypatch, tmp_path):
        _limpiar()
        _mock_pipeline(monkeypatch, tmp_path)

        # Job válido
        ok = client.post(
            "/jobs",
            data={"language": "es"},
            files={"video": ("e2e.mp4", b"video", "video/mp4")},
        )
        assert ok.status_code == 200
        ok_id = ok.json()["id"]

        # Job inválido (formato no soportado) no afecta al anterior
        bad = client.post(
            "/jobs",
            data={"language": "es"},
            files={"video": ("documento.txt", b"x", "text/plain")},
        )
        assert bad.status_code == 400

        # El job válido sigue transcrito y operativo
        assert client.get(f"/jobs/{ok_id}").json()["status"] == JobStatus.transcribed.value

    def test_render_antes_de_transcribir_devuelve_409(self, monkeypatch):
        _limpiar()
        from app.repositories import job_repository

        job_repository.create(
            {
                "id": "fase7_pending",
                "original_filename": "e2e.mp4",
                "input_path": "data/jobs/fase7_pending/input.mp4",
                "language": "es",
                "model": "small",
            }
        )
        render = client.post(
            "/jobs/fase7_pending/render",
            json={
                "font": "Arial",
                "font_size": 48,
                "color": "#FFFFFF",
                "outline_color": "#000000",
                "position": "bottom",
            },
        )
        assert render.status_code == 409
