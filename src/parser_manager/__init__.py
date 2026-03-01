"""
Parser Manager - синтаксический анализатор для HTML и документов
"""

import logging
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


def main():
    """Точка входа CLI приложения"""
    print("Parser Manager v0.0.0")
    print("Поддерживаемые форматы:", ", ".join(ParserFactory.get_available_formats()))


__version__ = "0.0.0"
__all__ = [
    "BaseParser",
    "ParserFactory",
    "ParsedContent",
    "DocumentMetadata",
    "TextElement",
    "ParserError",
    "main",
]
