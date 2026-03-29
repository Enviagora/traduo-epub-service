import subprocess
import tempfile
import os
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import Response

app = FastAPI(title="Traduo ePUB Converter")


@app.post("/convert-to-epub")
async def convert_to_epub(
    file: UploadFile = File(...),
    book_title: str = Form(default="livro"),
    cover: UploadFile = File(default=None),
):
    with tempfile.TemporaryDirectory() as tmp_dir:
        input_path = os.path.join(tmp_dir, "input.pdf")
        output_path = os.path.join(tmp_dir, "output.epub")

        with open(input_path, "wb") as f:
            f.write(await file.read())

        cmd = [
            "ebook-convert",
            input_path,
            output_path,
            "--title", book_title,
            # Detecção e estrutura
            "--formatting-type", "auto",
            "--detect-paragraph-structure",
            # Limpeza de texto
            "--enable-heuristics",
            "--unwrap-lines",
            "--fix-indents",
            "--paragraph-type", "auto",
            # Margens e layout
            "--margin-top", "10",
            "--margin-bottom", "10",
            "--margin-left", "10",
            "--margin-right", "10",
            # Fonte legível
            "--base-font-size", "12",
            "--font-size-mapping", "10,11,12,14,16,18,20,22",
            # Preservação de imagens
            "--insert-blank-line",
            "--insert-blank-line-size", "0.5",
            "--keep-ligatures",
            "--image-resolution", "300",
            "--preserve-entity-map",
            "--pdf-image-size", "1000",
            "--pdf-add-margins",
        ]

        if cover and cover.filename:
            cover_path = os.path.join(tmp_dir, "cover.jpg")
            with open(cover_path, "wb") as f:
                f.write(await cover.read())
            cmd += ["--cover", cover_path]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            raise HTTPException(
                status_code=500,
                detail=f"Conversion failed: {result.stderr}",
            )

        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="ePUB file not generated")

        with open(output_path, "rb") as f:
            epub_bytes = f.read()

    return Response(
        content=epub_bytes,
        media_type="application/epub+zip",
        headers={"Content-Disposition": f'attachment; filename="{book_title}.epub"'},
    )


@app.post("/extract-cover")
async def extract_cover(file: UploadFile = File(...)):
    with tempfile.TemporaryDirectory() as tmp_dir:
        input_path = os.path.join(tmp_dir, "input.pdf")
        output_path = os.path.join(tmp_dir, "cover.jpg")

        with open(input_path, "wb") as f:
            f.write(await file.read())

        result = subprocess.run(
            [
                "pdftoppm",
                "-jpeg",
                "-f", "1",
                "-l", "1",
                "-r", "150",
                "-singlefile",
                input_path,
                os.path.join(tmp_dir, "cover"),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0 or not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="Cover extraction failed")

        with open(output_path, "rb") as f:
            cover_bytes = f.read()

    return Response(
        content=cover_bytes,
        media_type="image/jpeg",
        headers={"Content-Disposition": "attachment; filename=cover.jpg"},
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
