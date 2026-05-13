from pathlib import Path

import pytest

from backend.app.core.config import Settings
from backend.app.services.mineru import MinerUClient, MinerUError


def make_settings(tmp_path: Path, **overrides) -> Settings:
    return Settings(
        storage_dir=tmp_path / "storage",
        lancedb_path=tmp_path / "lancedb",
        **overrides,
    )


def write_pdf(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "paper.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n")
    return pdf_path


def test_mineru_process_requires_configured_parser(tmp_path):
    settings = make_settings(tmp_path, mineru_mode="auto", mineru_api_token="", mineru_use_local=False)
    output_dir = tmp_path / "output"

    with pytest.raises(MinerUError, match="MinerU is not configured"):
        MinerUClient(settings).process(write_pdf(tmp_path), output_dir, "paper-1", "paper.pdf")

    assert not (output_dir / "full.md").exists()


def test_mineru_process_returns_local_markdown(tmp_path, monkeypatch):
    settings = make_settings(tmp_path, mineru_mode="local", mineru_use_local=True)
    client = MinerUClient(settings)
    output_dir = tmp_path / "output"

    def fake_process_local(pdf_path: Path, target_dir: Path) -> None:
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "full.md").write_text("# Parsed by MinerU", encoding="utf-8")

    monkeypatch.setattr(client, "_process_local", fake_process_local)

    md_path, parser = client.process(write_pdf(tmp_path), output_dir, "paper-1", "paper.pdf")

    assert parser == "mineru_local"
    assert md_path == output_dir / "full.md"
    assert md_path.read_text(encoding="utf-8") == "# Parsed by MinerU"


def test_mineru_process_does_not_fallback_when_api_has_no_markdown(tmp_path, monkeypatch):
    settings = make_settings(tmp_path, mineru_mode="api", mineru_api_token="token")
    client = MinerUClient(settings)
    output_dir = tmp_path / "output"

    def fake_process_api(*args, **kwargs) -> None:
        return None

    monkeypatch.setattr(client, "_process_api", fake_process_api)

    with pytest.raises(MinerUError, match="MinerU API did not produce Markdown output"):
        client.process(write_pdf(tmp_path), output_dir, "paper-1", "paper.pdf")

    assert not (output_dir / "full.md").exists()
    assert "MinerU API did not produce Markdown output" in (output_dir / "mineru_api_error.txt").read_text(
        encoding="utf-8"
    )
