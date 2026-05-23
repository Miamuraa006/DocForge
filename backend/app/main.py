from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from html import escape
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


MAX_FILE_SIZE = 10 * 1024 * 1024
WORD_EXTENSIONS = {".doc", ".docx"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


app = FastAPI(title="DocForge API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip().rstrip("/")
        for origin in os.getenv(
            "FRONTEND_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    ],
    allow_origin_regex=os.getenv("FRONTEND_ORIGIN_REGEX") or None,
    allow_credentials=False,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)


class TextPayload(BaseModel):
    text: str = Field(..., min_length=1, max_length=MAX_FILE_SIZE)


def get_extension(filename: str) -> str:
    return Path(filename or "").suffix.lower()


async def save_upload(upload: UploadFile, destination: Path) -> None:
    total = 0
    with destination.open("wb") as output:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_FILE_SIZE:
                raise HTTPException(status_code=413, detail="File size exceeds 10MB.")
            output.write(chunk)


def pdf_response(pdf_bytes: bytes, filename: str) -> Response:
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def find_libreoffice() -> str:
    configured_path = os.getenv("LIBREOFFICE_PATH")
    if configured_path:
        if Path(configured_path).exists() or shutil.which(configured_path):
            return configured_path
        raise HTTPException(
            status_code=500,
            detail="LIBREOFFICE_PATH is set but the executable was not found.",
        )

    executable = shutil.which("soffice") or shutil.which("libreoffice")
    if not executable:
        raise HTTPException(
            status_code=500,
            detail="LibreOffice is not installed or not available on PATH.",
        )
    return executable


@app.post("/api/word-to-pdf")
async def word_to_pdf(file: UploadFile = File(...)) -> Response:
    extension = get_extension(file.filename)
    if extension not in WORD_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only .doc and .docx files are allowed.")

    with tempfile.TemporaryDirectory(prefix="docforge-word-") as temp_dir:
        temp_path = Path(temp_dir)
        input_path = temp_path / f"upload{extension}"
        await save_upload(file, input_path)

        libreoffice = find_libreoffice()
        try:
            result = subprocess.run(
                [
                    libreoffice,
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    str(temp_path),
                    str(input_path),
                ],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise HTTPException(status_code=504, detail="Word to PDF conversion timed out.") from exc

        output_path = input_path.with_suffix(".pdf")
        if result.returncode != 0 or not output_path.exists():
            raise HTTPException(
                status_code=500,
                detail="Word to PDF conversion failed.",
            )

        return pdf_response(output_path.read_bytes(), "converted.pdf")


@app.post("/api/image-to-pdf")
async def image_to_pdf(file: UploadFile = File(...)) -> Response:
    extension = get_extension(file.filename)
    if extension not in IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only .jpg, .jpeg, and .png files are allowed.")

    with tempfile.TemporaryDirectory(prefix="docforge-image-") as temp_dir:
        temp_path = Path(temp_dir)
        input_path = temp_path / f"upload{extension}"
        output_path = temp_path / "converted.pdf"
        await save_upload(file, input_path)

        try:
            with Image.open(input_path) as image:
                rgb_image = image.convert("RGB")
                rgb_image.save(output_path, "PDF", resolution=100.0)
        except UnidentifiedImageError as exc:
            raise HTTPException(status_code=400, detail="Invalid image file.") from exc

        return pdf_response(output_path.read_bytes(), "converted.pdf")


@app.post("/api/text-to-pdf")
async def text_to_pdf(payload: TextPayload) -> Response:
    if len(payload.text.encode("utf-8")) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="Text size exceeds 10MB.")

    with tempfile.TemporaryDirectory(prefix="docforge-text-") as temp_dir:
        output_path = Path(temp_dir) / "converted.pdf"
        document = SimpleDocTemplate(str(output_path), pagesize=A4)
        styles = getSampleStyleSheet()
        body_style = styles["BodyText"]

        story = []
        for line in payload.text.splitlines() or [payload.text]:
            safe_line = escape(line).replace(" ", "&nbsp;") or "&nbsp;"
            story.append(Paragraph(safe_line, body_style))
            story.append(Spacer(1, 8))

        document.build(story)
        return pdf_response(output_path.read_bytes(), "converted.pdf")
