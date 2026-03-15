"""
Parser Manager - синтаксический анализатор для HTML и документов
"""

import logging
import argparse
from pathlib import Path
from parser_manager.core import BaseParser, ParserFactory
from parser_manager.models import (
    ParsedContent,
    DocumentMetadata,
    TextElement,
    ParserError,
    DocumentNotFoundError,
    UnsupportedFormatError,
    ParsingFailedError,
    CorruptedFileError,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="parser-manager",
        description="Унифицированный парсинг HTML/PDF/DOCX/DOC/DJVU в единый JSON-формат.",
    )
    parser.add_argument("-f", "--file", help="Путь к входному файлу")
    parser.add_argument(
        "-o",
        "--output",
        help="Путь к JSON-файлу результата (если не указан — вывод в консоль)",
    )
    parser.add_argument(
        "--list-formats",
        action="store_true",
        help="Показать поддерживаемые форматы и завершить работу",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Красивый (pretty) JSON вывод",
    )
    parser.add_argument(
        "--export-format",
        choices=["json", "md"],
        default="json",
        dest="export_format",
        help="Формат экспорта: json (по умолчанию) или md (Markdown)",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Показать версию и завершить работу",
    )
    return parser


def main(argv=None) -> int:
    """Точка входа CLI приложения."""
    parser = _build_cli_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"Parser Manager v{__version__}")
        return 0

    import parser_manager.parsers  # noqa: F401

    if args.list_formats:
        formats = ParserFactory.get_available_formats()
        print(
            "Поддерживаемые форматы:",
            ", ".join(formats) if formats else "(не зарегистрированы)",
        )
        return 0

    if not args.file:
        parser.print_help()
        return 2

    try:
        parser_instance = ParserFactory.create_parser(args.file)
        result = parser_instance.parse()

        if args.export_format == "md":
            from parser_manager.utils.exporters import to_markdown

            output_text = to_markdown(result)
        else:
            output_text = result.export("json", pretty=args.pretty)

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output_text + "\n", encoding="utf-8")
            print(f"OK: результат сохранён в {output_path}")
        else:
            print(output_text)

        stats = result.doc_stats
        print(
            f"Готово: {Path(args.file).name} | format={result.format} | "
            f"words={stats.get('word_count', 0)} | "
            f"read={stats.get('reading_time_min', 0)} min | "
            f"text_length={result.text_length}"
        )
        return 0

    except (
        DocumentNotFoundError,
        UnsupportedFormatError,
        ParsingFailedError,
        CorruptedFileError,
    ) as exc:
        print(f"Ошибка: {exc}")
        return 1
    except ParserError as exc:
        print(f"Ошибка парсера: {exc}")
        return 1
    except Exception as exc:
        logger.exception("Необработанная ошибка CLI")
        print(f"Непредвиденная ошибка: {exc}")
        return 1


__version__ = "0.0.0"
__all__ = [
    "BaseParser",
    "ParserFactory",
    "ParsedContent",
    "DocumentMetadata",
    "TextElement",
    "ParserError",
    "DocumentNotFoundError",
    "UnsupportedFormatError",
    "ParsingFailedError",
    "CorruptedFileError",
    "main",
]
