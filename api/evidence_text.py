"""Read bounded PDF text in a worker, retaining exact page boundaries."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

MAX_TEXT = 40_000


class EvidenceTextError(Exception):
    pass


def read_pages(path: Path) -> list[dict]:
    from pypdf import PdfReader

    try:
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise EvidenceTextError("encrypted_pdf")
        if not 0 < len(reader.pages) <= 300:
            raise EvidenceTextError("unsupported_page_count")
        pages, total, unreadable = [], 0, False
        for number, page in enumerate(reader.pages, 1):
            text = " ".join((page.extract_text() or "").replace("\x00", "").split())
            total += len(text)
            if total > MAX_TEXT:
                raise EvidenceTextError("document_text_too_long")
            if not text:
                if page.get_contents() is not None:
                    unreadable = True
            elif sum(c.isalpha() for c in text) < 3 or "\ufffd" in text:
                unreadable = True
            pages.append({"page": number, "text": text})
        if unreadable:
            raise EvidenceTextError(
                "unreadable_pages" if any(p["text"] for p in pages) else "no_selectable_text"
            )
        if not any(p["text"] for p in pages):
            raise EvidenceTextError("empty_pdf")
        return pages
    except EvidenceTextError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise EvidenceTextError("damaged_pdf") from exc


def prepare_evidence_pdf(path: Path) -> list[dict]:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "api.evidence_text", str(path.resolve())],
            capture_output=True,
            timeout=30,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise EvidenceTextError("processing_timeout") from exc
    if result.returncode or len(result.stdout) > 1_000_000:
        raise EvidenceTextError("processing_failed")
    try:
        payload = json.loads(result.stdout)
        if "error" in payload:
            raise EvidenceTextError(payload["error"])
        return payload["pages"]
    except (ValueError, KeyError, TypeError) as exc:
        raise EvidenceTextError("processing_failed") from exc


def _main():
    try:
        import resource

        resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
        try:
            resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        except (ValueError, OSError):
            pass
        print(json.dumps({"pages": read_pages(Path(sys.argv[1]))}))
    except EvidenceTextError as exc:
        print(json.dumps({"error": str(exc)}))


if __name__ == "__main__":
    _main()
