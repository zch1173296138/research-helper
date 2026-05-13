import json
import shutil
import subprocess
import time
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import requests

from backend.app.core.config import Settings


class MinerUError(RuntimeError):
    pass


class MinerUClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def should_use_api(self) -> bool:
        return self.settings.mineru_mode in {"auto", "api"} and bool(self.settings.mineru_api_token)

    def should_use_local(self) -> bool:
        return self.settings.mineru_mode in {"auto", "local"} and self.settings.mineru_use_local

    def process(
        self,
        pdf_path: Path,
        output_dir: Path,
        paper_id: str,
        original_filename: str,
        is_ocr: bool = True,
        enable_formula: bool = True,
        enable_table: bool = True,
        language: str = "ch",
        layout_model: str = "doclayout_yolo",
    ) -> tuple[Path, str]:
        output_dir.mkdir(parents=True, exist_ok=True)
        self._write_filename_info(output_dir, paper_id, original_filename)

        errors: list[str] = []

        if self.should_use_api():
            try:
                self._process_api(pdf_path, output_dir, paper_id, is_ocr, enable_formula, enable_table, language)
                md_path = self._find_full_markdown(output_dir)
                if md_path:
                    return md_path, "mineru_api"
                raise MinerUError("MinerU API did not produce Markdown output")
            except Exception as exc:
                (output_dir / "mineru_api_error.txt").write_text(str(exc), encoding="utf-8")
                errors.append(f"MinerU API failed: {exc}")

        if self.should_use_local():
            try:
                self._process_local(pdf_path, output_dir)
                md_path = self._find_full_markdown(output_dir)
                if md_path:
                    return md_path, "mineru_local"
                raise MinerUError("Local MinerU did not produce Markdown output")
            except Exception as exc:
                (output_dir / "mineru_local_error.txt").write_text(str(exc), encoding="utf-8")
                errors.append(f"Local MinerU failed: {exc}")

        if errors:
            raise MinerUError("; ".join(errors))
        raise MinerUError(
            "MinerU is not configured. Set MINERU_API_TOKEN for API mode or enable "
            "MINERU_USE_LOCAL=true with a local MinerU service."
        )

    def _write_filename_info(self, output_dir: Path, paper_id: str, original_filename: str) -> None:
        payload = {
            "file_id": paper_id,
            "original_filename": original_filename,
            "processed_at": time.time(),
        }
        (output_dir / "filename_info.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _process_local(self, pdf_path: Path, output_dir: Path) -> None:
        cmd = [
            "mineru",
            "-p",
            str(pdf_path),
            "-o",
            str(output_dir),
            "-b",
            "vlm-http-client",
            "-u",
            self.settings.mineru_local_url,
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=self.settings.mineru_timeout_seconds,
        )
        if result.returncode != 0:
            raise MinerUError(result.stderr or result.stdout or "MinerU local command failed")
        self._flatten_mineru_output(output_dir)

    def _process_api(
        self,
        pdf_path: Path,
        output_dir: Path,
        paper_id: str,
        is_ocr: bool,
        enable_formula: bool,
        enable_table: bool,
        language: str,
    ) -> None:
        session = requests.Session()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.settings.mineru_api_token}",
        }
        payload = {
            "files": [
                {
                    "name": pdf_path.name,
                    "is_ocr": is_ocr,
                    "data_id": f"{paper_id}_b1",
                }
            ],
            "model_version": "vlm",
            "enable_formula": enable_formula,
            "enable_table": enable_table,
            "language": language,
        }
        response = session.post(
            f"{self.settings.mineru_api_base_url}/file-urls/batch",
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        result = response.json()
        if result.get("code") != 0:
            raise MinerUError(result.get("msg", "MinerU file URL request failed"))

        batch_id = result["data"]["batch_id"]
        upload_url = result["data"]["file_urls"][0]
        with pdf_path.open("rb") as file_obj:
            upload_response = session.put(upload_url, data=file_obj, timeout=120)
            upload_response.raise_for_status()

        start = time.time()
        while time.time() - start < self.settings.mineru_timeout_seconds:
            status_response = session.get(
                f"{self.settings.mineru_api_base_url}/extract-results/batch/{batch_id}",
                headers=headers,
                timeout=30,
            )
            status_response.raise_for_status()
            status = status_response.json()
            if status.get("code") != 0:
                raise MinerUError(status.get("msg", "MinerU status request failed"))

            extract_result = status.get("data", {}).get("extract_result", [])
            if extract_result and all(item.get("state") in {"done", "failed"} for item in extract_result):
                done = [item for item in extract_result if item.get("state") == "done"]
                if not done:
                    raise MinerUError("MinerU API finished without successful files")
                self._download_zip(session, done[0]["full_zip_url"], output_dir)
                self._flatten_mineru_output(output_dir)
                return
            time.sleep(5)

        raise MinerUError("MinerU API processing timed out")

    def _download_zip(self, session: requests.Session, zip_url: str, output_dir: Path) -> None:
        temp_dir = output_dir / "_mineru_tmp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        zip_name = Path(urlparse(zip_url).path).name or "mineru_result.zip"
        zip_path = temp_dir / zip_name
        response = session.get(zip_url, stream=True, timeout=120)
        response.raise_for_status()
        with zip_path.open("wb") as file_obj:
            for chunk in response.iter_content(1024 * 1024):
                file_obj.write(chunk)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(output_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    def _flatten_mineru_output(self, output_dir: Path) -> None:
        # MinerU commonly emits nested directories such as <paper>/vlm/*. Move useful files up.
        md_files = list(output_dir.rglob("full.md"))
        if not md_files:
            md_files = list(output_dir.rglob("*.md"))
        if not md_files:
            return
        source_md = md_files[0]
        target_md = output_dir / "full.md"
        if source_md != target_md:
            target_md.write_text(source_md.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")

        for image_dir_name in ("images", "image"):
            for image_dir in output_dir.rglob(image_dir_name):
                if image_dir.is_dir() and image_dir != output_dir / "images":
                    target_dir = output_dir / "images"
                    target_dir.mkdir(exist_ok=True)
                    for item in image_dir.iterdir():
                        if item.is_file():
                            shutil.copy2(item, target_dir / item.name)

    def _find_full_markdown(self, output_dir: Path) -> Path | None:
        candidates = [output_dir / "full.md", *output_dir.rglob("full.md")]
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate
        md_files = list(output_dir.rglob("*.md"))
        return md_files[0] if md_files else None
