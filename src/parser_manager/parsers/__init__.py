"""
Parsers package - содержит парсеры для различных форматов файлов
При импорте пакета все реализованные парсеры автоматически регистрируются
в ParserFactory.
"""

from parser_manager.core.parser_factory import ParserFactory
from parser_manager.parsers.documents.djvu_parser import DjvuParser
from parser_manager.parsers.documents.doc_parser import DocParser
from parser_manager.parsers.documents.docx_parser import DocxParser
from parser_manager.parsers.documents.pdf_parser import PdfParser
from parser_manager.parsers.html_parser import HtmlParser

# ---------- регистрация парсеров ----------
ParserFactory.register_parsers(dict.fromkeys(HtmlParser.supported_extensions, HtmlParser))
ParserFactory.register_parsers(dict.fromkeys(DocParser.supported_extensions, DocParser))
ParserFactory.register_parsers(dict.fromkeys(DocxParser.supported_extensions, DocxParser))
ParserFactory.register_parsers(dict.fromkeys(DjvuParser.supported_extensions, DjvuParser))
ParserFactory.register_parsers(dict.fromkeys(PdfParser.supported_extensions, PdfParser))

__all__ = [
    "HtmlParser",
    "DocParser",
    "DocxParser",
    "DjvuParser",
    "PdfParser",
]
