from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from api.evidence_files import EvidenceFileError, validate_upload


@pytest.mark.parametrize(
    "format,mime,suffix",
    [("PNG", "image/png", ".png"), ("JPEG", "image/jpeg", ".jpg"), ("WEBP", "image/webp", ".webp")],
)
def test_supported_image_files_are_decoded(format, mime, suffix):
    buffer = BytesIO()
    Image.new("RGB", (16, 16), "gray").save(buffer, format=format)
    assert validate_upload("damage" + suffix, mime, buffer.getvalue()) == "image"


def test_real_pdf_is_not_an_image():
    data = (Path(__file__).parent / "fixtures/sample_policy.pdf").read_bytes()
    assert validate_upload("report.pdf", "application/pdf", data) == "pdf"
    with pytest.raises(EvidenceFileError, match="file_type_mismatch"):
        validate_upload("report.png", "image/png", data)


def test_spoofed_extensions_and_truncated_image_data_are_rejected():
    buffer = BytesIO()
    Image.new("RGB", (16, 16), "gray").save(buffer, format="PNG")
    data = buffer.getvalue()
    with pytest.raises(EvidenceFileError, match="file_type_mismatch"):
        validate_upload("damage.pdf", "image/png", data)
    with pytest.raises(EvidenceFileError):
        validate_upload("damage.png", "image/png", data[:24])


@pytest.mark.parametrize("data", [b"%PDF-broken", b"not a PDF"])
def test_unreadable_pdf_is_rejected(data):
    with pytest.raises(EvidenceFileError):
        validate_upload("report.pdf", "application/pdf", data)


def test_animated_image_is_rejected():
    buffer = BytesIO()
    first = Image.new("RGB", (16, 16), "gray")
    second = Image.new("RGB", (16, 16), "white")
    first.save(buffer, format="WEBP", save_all=True, append_images=[second], duration=100)
    with pytest.raises(EvidenceFileError, match="animated_image_unsupported"):
        validate_upload("animated.webp", "image/webp", buffer.getvalue())
