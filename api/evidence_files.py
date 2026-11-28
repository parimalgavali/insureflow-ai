"""Verify supported file contents in a bounded worker before storing evidence."""

from __future__ import annotations

import json
import subprocess
import sys
import warnings
from io import BytesIO
from pathlib import Path
from typing import Literal

DocumentType = Literal["damage_photo", "repair_estimate", "police_report", "other_document"]
EXTENSIONS = {
    "image/jpeg": {".jpg", ".jpeg"},
    "image/png": {".png"},
    "image/webp": {".webp"},
    "application/pdf": {".pdf"},
}


class EvidenceFileError(Exception):
    def __init__(self, code: str, status: int = 422):
        self.code, self.status = code, status
        super().__init__(code)


def validate_upload(filename: str, content_type: str, data: bytes) -> str:
    if content_type not in EXTENSIONS:
        raise EvidenceFileError("unsupported_file_type", 415)
    if Path(filename).suffix.lower() not in EXTENSIONS[content_type]:
        raise EvidenceFileError("file_type_mismatch")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "api.evidence_files", content_type],
            input=data,
            capture_output=True,
            timeout=15,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise EvidenceFileError("file_validation_timeout") from exc
    if result.returncode:
        raise EvidenceFileError("invalid_or_too_complex_file")
    try:
        response = json.loads(result.stdout)
        if response.get("error"):
            raise EvidenceFileError(response["error"])
        return response["media_type"]
    except (ValueError, KeyError, TypeError) as exc:
        raise EvidenceFileError("invalid_file") from exc


def _inspect(data: bytes, content_type: str) -> str:
    if content_type == "application/pdf":
        from pypdf import PdfReader

        if not data.startswith(b"%PDF-"):
            raise EvidenceFileError("file_type_mismatch")
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted:
            raise EvidenceFileError("encrypted_pdf")
        if not 0 < len(reader.pages) <= 300:
            raise EvidenceFileError("unsupported_page_count")
        return "pdf"
    from PIL import Image

    Image.MAX_IMAGE_PIXELS = 20_000_000
    formats = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}
    signatures = {
        "image/jpeg": data.startswith(b"\xff\xd8\xff"),
        "image/png": data.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/webp": data[:4] == b"RIFF" and data[8:12] == b"WEBP",
    }
    if not signatures.get(content_type, False):
        raise EvidenceFileError("file_type_mismatch")
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(BytesIO(data), formats=[formats[content_type]]) as image:
            if image.width * image.height > 20_000_000 or max(image.size) > 20_000:
                raise EvidenceFileError("image_dimensions_too_large")
            if getattr(image, "n_frames", 1) != 1:
                raise EvidenceFileError("animated_image_unsupported")
            image.verify()
        with Image.open(BytesIO(data), formats=[formats[content_type]]) as image:
            image.load()
    return "image"


def _main():
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
        try:
            resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        except (ValueError, OSError):
            pass
        media_type = _inspect(sys.stdin.buffer.read(), sys.argv[1])
        print(json.dumps({"media_type": media_type}))
    except EvidenceFileError as exc:
        print(json.dumps({"error": exc.code}))
    except Exception:  # noqa: BLE001
        print(json.dumps({"error": "invalid_file"}))


if __name__ == "__main__":
    _main()
