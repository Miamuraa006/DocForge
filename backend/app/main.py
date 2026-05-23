from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from html import escape
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field
from reportlab.graphics import renderPDF
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from svglib.svglib import svg2rlg


MAX_FILE_SIZE = 10 * 1024 * 1024
WORD_EXTENSIONS = {".doc", ".docx"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
SVG_EXTENSIONS = {".svg"}
VECTOR_EXTENSIONS = SVG_EXTENSIONS
DXF_EXTENSIONS = {".dxf"}


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


def file_response(file_bytes: bytes, filename: str, media_type: str) -> Response:
    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def pdf_response(pdf_bytes: bytes, filename: str = "converted.pdf") -> Response:
    return file_response(pdf_bytes, filename, "application/pdf")


def dxf_response(dxf_bytes: bytes, filename: str = "converted.dxf") -> Response:
    return file_response(dxf_bytes, filename, "application/dxf")


def svg_response(svg_bytes: bytes, filename: str = "converted.svg") -> Response:
    return file_response(svg_bytes, filename, "image/svg+xml")


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


async def convert_with_libreoffice(
    file: UploadFile,
    allowed_extensions: set[str],
    prefix: str,
    label: str,
) -> Response:
    extension = get_extension(file.filename)
    if extension not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        raise HTTPException(status_code=400, detail=f"Only {allowed} files are allowed.")

    with tempfile.TemporaryDirectory(prefix=f"docforge-{prefix}-") as temp_dir:
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
            raise HTTPException(status_code=504, detail=f"{label} conversion timed out.") from exc

        output_path = input_path.with_suffix(".pdf")
        if result.returncode != 0 or not output_path.exists():
            raise HTTPException(
                status_code=500,
                detail=f"{label} conversion failed.",
            )

        return pdf_response(output_path.read_bytes())


@app.post("/api/word-to-pdf")
async def word_to_pdf(file: UploadFile = File(...)) -> Response:
    return await convert_with_libreoffice(file, WORD_EXTENSIONS, "word", "Word to PDF")


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


def image_to_svg_bytes(input_path: Path) -> bytes:
    with Image.open(input_path) as image:
        raster = image.convert("RGBA")
        raster.thumbnail((220, 220), Image.Resampling.LANCZOS)
        width, height = raster.size
        pixels = raster.load()

        rects = []
        for y in range(height):
            run_start: int | None = None
            for x in range(width + 1):
                is_marked = False
                if x < width:
                    red, green, blue, alpha = pixels[x, y]
                    luminance = (0.299 * red) + (0.587 * green) + (0.114 * blue)
                    is_marked = alpha > 20 and luminance < 245

                if is_marked and run_start is None:
                    run_start = x
                elif not is_marked and run_start is not None:
                    rects.append(
                        f'<rect x="{run_start}" y="{y}" width="{x - run_start}" height="1" fill="#111111" />'
                    )
                    run_start = None

    svg = "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            '<g id="IMAGE_TRACE">',
            *rects,
            "</g>",
            "</svg>",
        ]
    )
    return svg.encode("utf-8")


def parse_svg_number(value: str | None, default: float = 0.0) -> float:
    if value is None:
        return default
    cleaned = value.strip().replace("px", "").replace("mm", "").replace("pt", "")
    try:
        return float(cleaned)
    except ValueError:
        return default


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def svg_to_dxf_bytes(svg_bytes: bytes) -> bytes:
    import ezdxf

    root = ET.fromstring(svg_bytes)
    view_box = root.attrib.get("viewBox", "").replace(",", " ").split()
    if len(view_box) == 4:
        svg_height = parse_svg_number(view_box[3], 100.0)
    else:
        svg_height = parse_svg_number(root.attrib.get("height"), 100.0)

    document = ezdxf.new("R2010")
    document.units = ezdxf.units.MM
    modelspace = document.modelspace()
    entity_count = 0

    def invert_y(y: float) -> float:
        return svg_height - y

    for element in root.iter():
        tag = local_name(element.tag)

        if tag == "rect":
            x = parse_svg_number(element.attrib.get("x"))
            y = parse_svg_number(element.attrib.get("y"))
            width = parse_svg_number(element.attrib.get("width"))
            height = parse_svg_number(element.attrib.get("height"))
            if width <= 0 or height <= 0:
                continue
            modelspace.add_lwpolyline(
                [
                    (x, invert_y(y)),
                    (x + width, invert_y(y)),
                    (x + width, invert_y(y + height)),
                    (x, invert_y(y + height)),
                ],
                close=True,
                dxfattribs={"layer": "SVG_TRACE"},
            )
            entity_count += 1

        elif tag == "line":
            x1 = parse_svg_number(element.attrib.get("x1"))
            y1 = parse_svg_number(element.attrib.get("y1"))
            x2 = parse_svg_number(element.attrib.get("x2"))
            y2 = parse_svg_number(element.attrib.get("y2"))
            modelspace.add_line((x1, invert_y(y1)), (x2, invert_y(y2)), dxfattribs={"layer": "SVG_TRACE"})
            entity_count += 1

        elif tag in {"polyline", "polygon"}:
            raw_points = element.attrib.get("points", "").replace(",", " ").split()
            values = [parse_svg_number(point) for point in raw_points]
            points = [
                (values[index], invert_y(values[index + 1]))
                for index in range(0, len(values) - 1, 2)
            ]
            if len(points) >= 2:
                modelspace.add_lwpolyline(
                    points,
                    close=tag == "polygon",
                    dxfattribs={"layer": "SVG_TRACE"},
                )
                entity_count += 1

        elif tag == "circle":
            cx = parse_svg_number(element.attrib.get("cx"))
            cy = parse_svg_number(element.attrib.get("cy"))
            radius = parse_svg_number(element.attrib.get("r"))
            if radius > 0:
                modelspace.add_circle((cx, invert_y(cy)), radius, dxfattribs={"layer": "SVG_TRACE"})
                entity_count += 1

    if entity_count == 0:
        raise ValueError("SVG does not contain supported vector geometry.")

    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as output:
        output_path = Path(output.name)
    try:
        document.saveas(output_path)
        return output_path.read_bytes()
    finally:
        output_path.unlink(missing_ok=True)


@app.post("/api/image-to-svg")
async def image_to_svg(file: UploadFile = File(...)) -> Response:
    extension = get_extension(file.filename)
    if extension not in IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only .jpg, .jpeg, and .png files are allowed.")

    with tempfile.TemporaryDirectory(prefix="docforge-image-svg-") as temp_dir:
        temp_path = Path(temp_dir)
        input_path = temp_path / f"upload{extension}"
        await save_upload(file, input_path)

        try:
            return svg_response(image_to_svg_bytes(input_path))
        except UnidentifiedImageError as exc:
            raise HTTPException(status_code=400, detail="Invalid image file.") from exc


@app.post("/api/vector-to-pdf")
async def vector_to_pdf(file: UploadFile = File(...)) -> Response:
    extension = get_extension(file.filename)
    if extension not in SVG_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only .svg files are allowed.")

    with tempfile.TemporaryDirectory(prefix="docforge-vector-") as temp_dir:
        temp_path = Path(temp_dir)
        input_path = temp_path / f"upload{extension}"
        output_path = temp_path / "converted.pdf"
        await save_upload(file, input_path)

        try:
            drawing = svg2rlg(str(input_path))
            if drawing is None:
                raise ValueError("SVG could not be parsed.")
            renderPDF.drawToFile(drawing, str(output_path))
        except Exception as exc:
            raise HTTPException(status_code=400, detail="SVG to PDF conversion failed.") from exc

        return pdf_response(output_path.read_bytes())


@app.post("/api/svg-to-dxf")
async def svg_to_dxf(file: UploadFile = File(...)) -> Response:
    extension = get_extension(file.filename)
    if extension not in SVG_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only .svg files are allowed.")

    with tempfile.TemporaryDirectory(prefix="docforge-svg-dxf-") as temp_dir:
        temp_path = Path(temp_dir)
        input_path = temp_path / f"upload{extension}"
        await save_upload(file, input_path)

        try:
            return dxf_response(svg_to_dxf_bytes(input_path.read_bytes()))
        except ET.ParseError as exc:
            raise HTTPException(status_code=400, detail="Invalid SVG file.") from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail="SVG to DXF conversion failed.") from exc


@app.post("/api/dxf-to-pdf")
async def dxf_to_pdf(file: UploadFile = File(...)) -> Response:
    extension = get_extension(file.filename)
    if extension not in DXF_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only .dxf files are allowed.")

    with tempfile.TemporaryDirectory(prefix="docforge-dxf-") as temp_dir:
        temp_path = Path(temp_dir)
        input_path = temp_path / f"upload{extension}"
        output_path = temp_path / "converted.pdf"
        await save_upload(file, input_path)

        try:
            import ezdxf
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from ezdxf.addons.drawing import Frontend, RenderContext
            from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

            document = ezdxf.readfile(input_path)
            figure = plt.figure(figsize=(8.27, 11.69), dpi=150)
            axis = figure.add_axes((0, 0, 1, 1))
            axis.set_axis_off()
            context = RenderContext(document)
            backend = MatplotlibBackend(axis)
            Frontend(context, backend).draw_layout(document.modelspace(), finalize=True)
            figure.savefig(output_path, format="pdf", bbox_inches="tight", pad_inches=0.2)
            plt.close(figure)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="DXF to PDF conversion failed.") from exc

        return pdf_response(output_path.read_bytes())


@app.post("/api/image-to-dxf")
async def image_to_dxf(file: UploadFile = File(...)) -> Response:
    extension = get_extension(file.filename)
    if extension not in IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only .jpg, .jpeg, and .png files are allowed.")

    with tempfile.TemporaryDirectory(prefix="docforge-image-dxf-") as temp_dir:
        temp_path = Path(temp_dir)
        input_path = temp_path / f"upload{extension}"
        output_path = temp_path / "converted.dxf"
        await save_upload(file, input_path)

        try:
            svg_bytes = image_to_svg_bytes(input_path)
            output_path.write_bytes(svg_to_dxf_bytes(svg_bytes))
        except UnidentifiedImageError as exc:
            raise HTTPException(status_code=400, detail="Invalid image file.") from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Image to DXF conversion failed.") from exc

        return dxf_response(output_path.read_bytes())


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
