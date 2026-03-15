"""Сервис парсинга для API worker."""

import tempfile
from pathlib import Path

from parser_manager.core import ParserFactory


def parse_file_sync(file_path: str) -> dict:
    import parser_manager.parsers  # noqa: F401

    parser = ParserFactory.create_parser(file_path)
    result = parser.parse()
    return result.to_dict()


def save_upload_to_temp(content: bytes, suffix: str) -> Path:
    temp_dir = Path(tempfile.gettempdir()) / "parser_manager_uploads"
    temp_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix or ".bin",
        dir=temp_dir,
    ) as fh:
        fh.write(content)
        return Path(fh.name)
