"""
Parsers package - содержит парсеры для различных форматов файлов
При импорте пакета все реализованные парсеры автоматически регистрируются
в ParserFactory.
"""

from parser_manager.core.parser_factory import ParserFactory
from parser_manager.parsers.html_parser import HtmlParser
from parser_manager.parsers.documents.doc_parser import DocParser
from parser_manager.parsers.documents.docx_parser import DocxParser
from parser_manager.parsers.documents.djvu_parser import DjvuParser
from parser_manager.parsers.documents.pdf_parser import PdfParser

# ---------- регистрация парсеров ----------
ParserFactory.register_parsers(
    {ext: HtmlParser for ext in HtmlParser.supported_extensions}
)
ParserFactory.register_parsers(
    {ext: DocParser for ext in DocParser.supported_extensions}
)
ParserFactory.register_parsers(
    {ext: DocxParser for ext in DocxParser.supported_extensions}
)
ParserFactory.register_parsers(
    {ext: DjvuParser for ext in DjvuParser.supported_extensions}
)
ParserFactory.register_parsers(
    {ext: PdfParser for ext in PdfParser.supported_extensions}
)

__all__ = [
    "HtmlParser",
    "DocParser",
    "DocxParser",
    "DjvuParser",
    "PdfParser",
]
