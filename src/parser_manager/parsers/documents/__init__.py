"""
Document parsers - парсеры для документов.
"""

from parser_manager.parsers.documents.djvu_parser import DjvuParser
from parser_manager.parsers.documents.doc_parser import DocParser
from parser_manager.parsers.documents.docx_parser import DocxParser
from parser_manager.parsers.documents.pdf_parser import PdfParser

__all__ = [
    "DocParser",
    "DocxParser",
    "DjvuParser",
    "PdfParser",
]
