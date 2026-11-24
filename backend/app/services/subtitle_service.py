import os
from html import escape
from typing import Literal

from app.schemas import SubtitleStyle


class SubtitleGenerationError(Exception):
    pass


def _ass_timestamp(seconds: float) -> str:
    centiseconds = round(seconds * 100)
    hours = centiseconds // 360000
    minutes = (centiseconds % 360000) // 6000
    secs = (centiseconds % 6000) // 100
    cs = centiseconds % 100
    return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"


def _ass_color(hex_color: str) -> str:
    red = hex_color[1:3]
    green = hex_color[3:5]
    blue = hex_color[5:7]
    return f"&H00{blue}{green}{red}"


def _alignment(position: str) -> int:
    return {"top": 8, "middle": 5, "bottom": 2}[position]


def _escape_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n", "\\N")


def generar_ass(segmentos: list[dict], style: SubtitleStyle, output_path: str) -> str:
    if not segmentos:
        raise SubtitleGenerationError("No hay segmentos para generar subtítulos")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    alignment = _alignment(style.position)
    primary_color = _ass_color(style.color)
    outline_color = _ass_color(style.outline_color)

    lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1920",
        "PlayResY: 1080",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,{style.font},{style.font_size},{primary_color},&H000000FF,{outline_color},&H64000000,0,0,0,0,100,100,0,0,1,3,0,{alignment},80,80,70,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    for segment in segmentos:
        start = _ass_timestamp(float(segment["inicio"]))
        end = _ass_timestamp(float(segment["fin"]))
        text = _escape_text(str(segment["texto"]).strip())
        lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")

    with open(output_path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")

    return output_path


def _marca_de_tiempo(segundos: float, separador: str) -> str:
    horas, resto = divmod(round(segundos * 1000), 3_600_000)
    minutos, resto = divmod(resto, 60_000)
    segundos, ms = divmod(resto, 1000)
    return f"{horas:02d}:{minutos:02d}:{segundos:02d}{separador}{ms:03d}"


def exportar_subtitulos(segmentos: list[dict], formato: Literal["srt", "vtt"]) -> str:
    separador = "," if formato == "srt" else "."
    bloques = []
    for numero, segmento in enumerate(segmentos, 1):
        inicio = _marca_de_tiempo(segmento["inicio"], separador)
        fin = _marca_de_tiempo(segmento["fin"], separador)
        texto = "\n".join(linea for linea in segmento["texto"].splitlines() if linea.strip())
        bloque = f"{inicio} --> {fin}\n{escape(texto, quote=False)}"
        bloques.append(f"{numero}\n{bloque}" if formato == "srt" else bloque)
    cabecera = "WEBVTT\n\n" if formato == "vtt" else ""
    return cabecera + "\n\n".join(bloques) + ("\n" if bloques else "")
