"""
Parser Manager - синтаксический анализатор для HTML и документов
"""

import argparse
import json
import logging
from pathlib import Path

from parser_manager.core import BaseParser, ParserFactory
from parser_manager.models import (
    CorruptedFileError,
    DocumentMetadata,
    DocumentNotFoundError,
    ParsedContent,
    ParserError,
    ParsingFailedError,
    TextElement,
    UnsupportedFormatError,
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
        payload = result.to_dict()

        json_text = json.dumps(
            payload,
            ensure_ascii=False,
            indent=2 if args.pretty else None,
        )

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json_text + "\n", encoding="utf-8")
            print(f"OK: результат сохранён в {output_path}")
        else:
            print(json_text)

        print(
            f"Готово: {Path(args.file).name} | format={result.format} | "
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
