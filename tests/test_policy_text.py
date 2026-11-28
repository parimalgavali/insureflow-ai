import subprocess
from pathlib import Path

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, NameObject

from api.policy_text import PolicyTextError, prepare_pdf


def test_protected_pdf_fails_preparation_without_becoming_readable(tmp_path):
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("sample-password")
    path = tmp_path / "protected.pdf"
    writer.write(path)
    with pytest.raises(PolicyTextError, match="encrypted_pdf"):
        prepare_pdf(path)


def test_page_with_content_but_no_readable_text_is_not_silently_skipped(tmp_path):
    writer = PdfWriter()
    page = writer.add_blank_page(width=100, height=100)
    stream = DecodedStreamObject()
    stream.set_data(b"0 0 100 100 re S")
    page[NameObject("/Contents")] = writer._add_object(stream)
    path = tmp_path / "unreadable.pdf"
    writer.write(path)
    with pytest.raises(PolicyTextError, match="unreadable_page"):
        prepare_pdf(path)


def test_stuck_worker_returns_a_retryable_processing_timeout(monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 30)

    monkeypatch.setattr(subprocess, "run", timeout)
    with pytest.raises(PolicyTextError, match="processing_timeout"):
        prepare_pdf(Path("not-read.pdf"))
