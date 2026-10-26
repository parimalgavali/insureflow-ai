from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest

from scripts import fetch_data
from scripts.fetch_data import (
    AKB_PDF_URL,
    GDV_MUSTERBEDINGUNGEN_URL,
    FetchError,
    discover_akb_url,
    download_file,
    extract_pdf_text,
    fetch_akb,
    fetch_kaggle,
    fetch_openml,
    kaggle_credentials_available,
)
from tests.conftest import FakeResponse, FakeSession


def test_extract_pdf_text_from_fixture(akb_fixture_pdf: Path):
    text, pages = extract_pdf_text(akb_fixture_pdf)
    assert pages == 2
    assert "Allgemeine Bedingungen für die Kfz-Versicherung" in text
    assert text.count("\f") == 1  # pages separated by form feed


def test_download_file_raises_on_http_error(tmp_path: Path):
    session = FakeSession({"https://x/404.pdf": FakeResponse(404)})
    with pytest.raises(FetchError, match="HTTP 404"):
        download_file("https://x/404.pdf", tmp_path / "out.pdf", session=session)
    assert not (tmp_path / "out.pdf").exists()


def test_fetch_akb_with_mocked_http(tmp_path: Path, akb_fixture_pdf: Path):
    session = FakeSession({AKB_PDF_URL: FakeResponse(200, akb_fixture_pdf.read_bytes())})
    manifest = tmp_path / "manifest.json"

    entry = fetch_akb(
        tmp_path / "raw",
        tmp_path / "processed",
        session=session,
        manifest_path=manifest,
        min_pages=2,
        min_words=50,
    )

    assert session.calls == [AKB_PDF_URL]
    assert entry.pages == 2 and entry.words > 50
    assert (tmp_path / "raw" / "gdv" / "akb_2015.pdf").read_bytes() == akb_fixture_pdf.read_bytes()
    txt = (tmp_path / "processed" / "akb_2015.txt").read_text(encoding="utf-8")
    assert "AKB 2015" in txt
    saved = json.loads(manifest.read_text())["gdv_akb_2015"]
    assert saved["sha256"] == entry.sha256 and len(saved["sha256"]) == 64


def test_fetch_akb_falls_back_to_discovery(tmp_path: Path, akb_fixture_pdf: Path):
    new_path = "/resource/blob/999/abc/01-allgemeine-bedingungen-akb-2015--data.pdf"
    html = f'<a href="{new_path}">AKB</a>'
    session = FakeSession(
        {
            AKB_PDF_URL: FakeResponse(404),
            GDV_MUSTERBEDINGUNGEN_URL: FakeResponse(200, text=html),
            "https://www.gdv.de" + new_path: FakeResponse(200, akb_fixture_pdf.read_bytes()),
        }
    )
    entry = fetch_akb(
        tmp_path / "raw",
        tmp_path / "processed",
        session=session,
        manifest_path=tmp_path / "m.json",
        min_pages=2,
        min_words=50,
    )
    assert entry.url.endswith(new_path)
    assert session.calls[1] == GDV_MUSTERBEDINGUNGEN_URL


def test_discover_akb_url_fails_loudly_when_link_missing():
    session = FakeSession(
        {GDV_MUSTERBEDINGUNGEN_URL: FakeResponse(200, text="<html>nothing</html>")}
    )
    with pytest.raises(FetchError, match="update AKB_PDF_URL"):
        discover_akb_url(session)


def test_fetch_akb_rejects_truncated_pdf(tmp_path: Path, akb_fixture_pdf: Path):
    session = FakeSession({AKB_PDF_URL: FakeResponse(200, akb_fixture_pdf.read_bytes())})
    with pytest.raises(FetchError, match="looks wrong"):
        fetch_akb(
            tmp_path / "raw",
            tmp_path / "processed",
            session=session,
            manifest_path=tmp_path / "m.json",
        )


# ------------------------------------------------------------------------ Kaggle


def test_kaggle_credentials_detection(tmp_path: Path):
    assert kaggle_credentials_available(env={}, home=tmp_path) is False
    assert kaggle_credentials_available(
        env={"KAGGLE_USERNAME": "u", "KAGGLE_KEY": "k"}, home=tmp_path
    )
    (tmp_path / ".kaggle").mkdir()
    (tmp_path / ".kaggle" / "kaggle.json").write_text("{}")
    assert kaggle_credentials_available(env={}, home=tmp_path) is True


def test_fetch_kaggle_without_credentials_gives_help(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(fetch_data, "kaggle_credentials_available", lambda: False)
    with pytest.raises(FetchError, match="kaggle.com/settings"):
        fetch_kaggle(tmp_path, manifest_path=tmp_path / "m.json")


def test_fetch_kaggle_with_mocked_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(fetch_data, "kaggle_credentials_available", lambda: True)
    monkeypatch.setattr(fetch_data.shutil, "which", lambda _: "/usr/bin/kaggle")

    def fake_run(cmd, **_):
        dest = Path(cmd[cmd.index("-p") + 1])
        (dest / "fraud_oracle.csv").write_text("Month,Age,FraudFound_P\nJan,30,0\nFeb,41,1\n")
        return types.SimpleNamespace(returncode=0, stderr="")

    entry = fetch_kaggle(tmp_path, manifest_path=tmp_path / "m.json", runner=fake_run)
    assert (entry.rows, entry.columns) == (2, 3)
    assert entry.url.endswith("khusheekapoor/vehicle-insurance-fraud-detection")


def test_fetch_kaggle_reports_cli_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(fetch_data, "kaggle_credentials_available", lambda: True)
    monkeypatch.setattr(fetch_data.shutil, "which", lambda _: "/usr/bin/kaggle")
    fake_run = lambda cmd, **_: types.SimpleNamespace(returncode=1, stderr="403 Forbidden")  # noqa: E731
    with pytest.raises(FetchError, match="403 Forbidden"):
        fetch_kaggle(tmp_path, manifest_path=tmp_path / "m.json", runner=fake_run)


# ------------------------------------------------------------------------ OpenML


def test_fetch_openml_with_mocked_package(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    pd = pytest.importorskip("pandas")
    frame = pd.DataFrame({"IDpol": [1, 2, 3], "DrivAge": [30, 40, 50]})

    class FakeDataset:
        def get_data(self, dataset_format="dataframe"):
            return frame, None, None, None

    fake_openml = types.SimpleNamespace(
        config=types.SimpleNamespace(set_root_cache_directory=lambda path: None),
        datasets=types.SimpleNamespace(get_dataset=lambda dataset_id, **_: FakeDataset()),
    )
    monkeypatch.setitem(sys.modules, "openml", fake_openml)

    entries = fetch_openml(
        tmp_path / "raw",
        tmp_path / "processed",
        datasets={"tiny": 1},
        manifest_path=tmp_path / "m.json",
    )
    assert len(entries) == 1 and entries[0].rows == 3 and entries[0].columns == 2
    assert pd.read_parquet(tmp_path / "processed" / "tiny.parquet").equals(frame)


def test_cli_returns_1_on_fetch_error(monkeypatch: pytest.MonkeyPatch, capsys):
    def boom():
        raise FetchError("nope")

    monkeypatch.setattr(fetch_data, "fetch_kaggle", boom)
    assert fetch_data.main(["kaggle"]) == 1
    assert "error: nope" in capsys.readouterr().err
