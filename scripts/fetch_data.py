"""Fetch every public dataset listed in docs/DATA.md.

Usage:
    python scripts/fetch_data.py akb      # GDV AKB 2015 PDF -> data/processed/akb_2015.txt
    python scripts/fetch_data.py openml   # freMTPL2freq / freMTPL2sev -> parquet
    python scripts/fetch_data.py kaggle   # vehicle-insurance-fraud CSV (needs Kaggle token)
    python scripts/fetch_data.py all

Nothing under data/raw or data/processed is committed. A manifest with checksums,
row counts and fetch dates is written to data/processed/manifest.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MANIFEST_PATH = PROCESSED_DIR / "manifest.json"

GDV_MUSTERBEDINGUNGEN_URL = "https://www.gdv.de/gdv/service/musterbedingungen"
AKB_PDF_URL = (
    "https://www.gdv.de/resource/blob/6178/dd2bfe79d9d75902e4cc24b5560af6ed/"
    "01-allgemeine-bedingungen-fuer-die-kfz-versicherung-akb-2015--data.pdf"
)
AKB_PDF_NAME = "akb_2015.pdf"
AKB_TXT_NAME = "akb_2015.txt"

OPENML_DATASETS = {"freMTPL2freq": 41214, "freMTPL2sev": 41215}

KAGGLE_DATASET = "khusheekapoor/vehicle-insurance-fraud-detection"
KAGGLE_FILE = "fraud_oracle.csv"

HTTP_TIMEOUT = 60


class FetchError(RuntimeError):
    """Raised when a source cannot be fetched; the message is meant for the user."""


@dataclass
class ManifestEntry:
    source: str
    url: str
    path: str
    sha256: str
    bytes: int
    fetched_at: str
    rows: int | None = None
    columns: int | None = None
    pages: int | None = None
    words: int | None = None


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, dict]:
    if path.exists():
        return json.loads(path.read_text())
    return {}


def update_manifest(entry: ManifestEntry, path: Path = MANIFEST_PATH) -> None:
    manifest = load_manifest(path)
    manifest[entry.source] = asdict(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


# --------------------------------------------------------------------------- AKB


def download_file(url: str, dest: Path, *, session: requests.Session | None = None) -> Path:
    """Stream *url* to *dest*; raises FetchError on non-200."""
    http = session or requests.Session()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with http.get(url, stream=True, timeout=HTTP_TIMEOUT) as response:
        if response.status_code != 200:
            raise FetchError(f"GET {url} returned HTTP {response.status_code}")
        tmp = dest.with_suffix(dest.suffix + ".part")
        with tmp.open("wb") as fh:
            for chunk in response.iter_content(chunk_size=1 << 16):
                fh.write(chunk)
        tmp.replace(dest)
    return dest


def discover_akb_url(session: requests.Session | None = None) -> str:
    """Fallback: find the current AKB 2015 link on the GDV Musterbedingungen page."""
    http = session or requests.Session()
    response = http.get(GDV_MUSTERBEDINGUNGEN_URL, timeout=HTTP_TIMEOUT)
    if response.status_code != 200:
        raise FetchError(
            f"GDV Musterbedingungen page returned HTTP {response.status_code}; "
            f"open {GDV_MUSTERBEDINGUNGEN_URL} in a browser and update AKB_PDF_URL."
        )
    match = re.search(r'href="(/resource/blob/[^"]*akb-2015[^"]*\.pdf)"', response.text)
    if not match:
        raise FetchError(
            "Could not find an 'akb-2015' PDF link on the GDV Musterbedingungen page; "
            f"open {GDV_MUSTERBEDINGUNGEN_URL} and update AKB_PDF_URL."
        )
    return "https://www.gdv.de" + match.group(1)


def extract_pdf_text(pdf_path: Path) -> tuple[str, int]:
    """Return (text, page_count). Pages are separated by form-feed characters."""
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    return "\f".join(pages) + "\n", len(pages)


def fetch_akb(
    raw_dir: Path = RAW_DIR,
    processed_dir: Path = PROCESSED_DIR,
    *,
    url: str = AKB_PDF_URL,
    session: requests.Session | None = None,
    manifest_path: Path = MANIFEST_PATH,
    min_pages: int = 10,
    min_words: int = 5000,
) -> ManifestEntry:
    pdf_path = raw_dir / "gdv" / AKB_PDF_NAME
    try:
        download_file(url, pdf_path, session=session)
    except FetchError as exc:
        print(f"[akb] {exc}; trying to discover the link on the GDV page", file=sys.stderr)
        url = discover_akb_url(session)
        download_file(url, pdf_path, session=session)

    text, pages = extract_pdf_text(pdf_path)
    words = len(text.split())
    if pages < min_pages or words < min_words:
        raise FetchError(
            f"AKB PDF looks wrong ({pages} pages, {words} words); expected ~55 pages / ~21k words."
        )
    processed_dir.mkdir(parents=True, exist_ok=True)
    (processed_dir / AKB_TXT_NAME).write_text(text, encoding="utf-8")

    entry = ManifestEntry(
        source="gdv_akb_2015",
        url=url,
        path=str(pdf_path.relative_to(REPO_ROOT))
        if pdf_path.is_relative_to(REPO_ROOT)
        else str(pdf_path),
        sha256=sha256_of(pdf_path),
        bytes=pdf_path.stat().st_size,
        fetched_at=_now(),
        pages=pages,
        words=words,
    )
    update_manifest(entry, manifest_path)
    print(f"[akb] {pages} pages, {words} words -> {processed_dir / AKB_TXT_NAME}")
    return entry


# ------------------------------------------------------------------------ OpenML


def fetch_openml(
    raw_dir: Path = RAW_DIR,
    processed_dir: Path = PROCESSED_DIR,
    *,
    datasets: dict[str, int] = OPENML_DATASETS,
    manifest_path: Path = MANIFEST_PATH,
) -> list[ManifestEntry]:
    try:
        import openml
    except ImportError as exc:
        raise FetchError("Install the data extra: uv sync --extra data") from exc

    openml.config.set_root_cache_directory(str(raw_dir / "openml"))
    processed_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for name, dataset_id in datasets.items():
        dataset = openml.datasets.get_dataset(
            dataset_id,
            download_data=True,
            download_qualities=False,
            download_features_meta_data=False,
        )
        frame, _, _, _ = dataset.get_data(dataset_format="dataframe")
        out = processed_dir / f"{name}.parquet"
        frame.to_parquet(out, index=False)
        entry = ManifestEntry(
            source=f"openml_{name}",
            url=f"https://www.openml.org/d/{dataset_id}",
            path=str(out.relative_to(REPO_ROOT)) if out.is_relative_to(REPO_ROOT) else str(out),
            sha256=sha256_of(out),
            bytes=out.stat().st_size,
            fetched_at=_now(),
            rows=int(frame.shape[0]),
            columns=int(frame.shape[1]),
        )
        update_manifest(entry, manifest_path)
        print(
            f"[openml] {name} (id {dataset_id}): {entry.rows} rows x {entry.columns} cols -> {out}"
        )
        entries.append(entry)
    return entries


# ------------------------------------------------------------------------ Kaggle


def kaggle_credentials_available(
    env: dict[str, str] | None = None, home: Path | None = None
) -> bool:
    env = os.environ if env is None else env
    if env.get("KAGGLE_USERNAME") and env.get("KAGGLE_KEY"):
        return True
    if env.get("KAGGLE_API_TOKEN"):
        return True
    config_dir = Path(env.get("KAGGLE_CONFIG_DIR") or (home or Path.home()) / ".kaggle")
    return (config_dir / "kaggle.json").exists()


KAGGLE_HELP = (
    "Kaggle credentials not found. Create an API token at https://www.kaggle.com/settings "
    '("Create New Token") and either save it to ~/.kaggle/kaggle.json or export '
    "KAGGLE_USERNAME and KAGGLE_KEY. The vehicle-insurance-fraud dataset is skipped until then."
)


def fetch_kaggle(
    raw_dir: Path = RAW_DIR,
    *,
    dataset: str = KAGGLE_DATASET,
    manifest_path: Path = MANIFEST_PATH,
    runner=subprocess.run,
) -> ManifestEntry:
    if not kaggle_credentials_available():
        raise FetchError(KAGGLE_HELP)
    if shutil.which("kaggle") is None:
        raise FetchError("The `kaggle` CLI is not installed; run: uv sync --extra data")

    dest_dir = raw_dir / "kaggle"
    dest_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "kaggle",
        "datasets",
        "download",
        "-d",
        dataset,
        "-p",
        str(dest_dir),
        "--unzip",
        "--force",
    ]
    result = runner(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise FetchError(f"kaggle CLI failed ({result.returncode}): {result.stderr.strip()}")

    csv_path = dest_dir / KAGGLE_FILE
    if not csv_path.exists():
        candidates = sorted(dest_dir.glob("*.csv"))
        if not candidates:
            raise FetchError(f"No CSV found in {dest_dir} after download")
        csv_path = candidates[0]

    rows, columns = _csv_shape(csv_path)
    entry = ManifestEntry(
        source="kaggle_vehicle_insurance_fraud",
        url=f"https://www.kaggle.com/datasets/{dataset}",
        path=str(csv_path.relative_to(REPO_ROOT))
        if csv_path.is_relative_to(REPO_ROOT)
        else str(csv_path),
        sha256=sha256_of(csv_path),
        bytes=csv_path.stat().st_size,
        fetched_at=_now(),
        rows=rows,
        columns=columns,
    )
    update_manifest(entry, manifest_path)
    print(f"[kaggle] {csv_path.name}: {rows} rows x {columns} cols")
    return entry


def _csv_shape(path: Path) -> tuple[int, int]:
    import csv

    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader, [])
        rows = sum(1 for _ in reader)
    return rows, len(header)


# --------------------------------------------------------------------------- CLI


def run_all() -> int:
    failures = 0
    fetch_akb()
    fetch_openml()
    try:
        fetch_kaggle()
    except FetchError as exc:
        print(f"[kaggle] skipped: {exc}", file=sys.stderr)
    try:
        from scripts.seed_policyholders import write_seed

        write_seed()
    except ImportError:
        from seed_policyholders import write_seed  # type: ignore[no-redef]

        write_seed()
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("source", choices=["akb", "openml", "kaggle", "all"])
    args = parser.parse_args(argv)
    try:
        if args.source == "akb":
            fetch_akb()
        elif args.source == "openml":
            fetch_openml()
        elif args.source == "kaggle":
            fetch_kaggle()
        else:
            return run_all()
    except FetchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
