"""Сервис парсинга для фонового обработчика API."""

import tempfile
from pathlib import Path

from parser_manager.core import ParserFactory


def parse_file_sync(file_path: str) -> dict:
    import parser_manager.parsers  # noqa: F401

    parser = ParserFactory.create_parser(file_path)
    result = parser.parse()
    # Метод to_dict() автоматически включает doc_stats, ast, semantic_blocks и quality
    return result.to_dict()


def export_file_sync(result_dict: dict, fmt: str) -> str:
    """
    Экспортировать словарь результата парсинга в нужный формат.

    Args:
        result_dict: словарь из result.to_dict()
        fmt: 'json', 'md' или 'report'
    """
    import json

    from parser_manager.models.parsed_content import ParsedContent
    from parser_manager.utils.exporters import export_content

    if fmt == "json":
        return json.dumps(result_dict, ensure_ascii=False, indent=2)

    # Для экспорта в текстовые форматы восстанавливаем ParsedContent из словаря
    fmt_name = result_dict.get("format", "html")
    pc = ParsedContent(
        file_path=str(result_dict.get("file_path", "")),
        format=fmt_name,
        text="",  # текст не храним повторно
        semantic_blocks=result_dict.get("semantic_blocks") or [],
        doc_stats=result_dict.get("doc_stats") or {},
        ast=result_dict.get("ast") or {},
        metadata=result_dict.get("metadata") or {},
        quality=result_dict.get("quality") or {},
        file_metrics=result_dict.get("file_metrics") or {},
        success=bool(result_dict.get("success", True)),
        error=result_dict.get("error"),
    )
    return export_content(pc, fmt)


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
