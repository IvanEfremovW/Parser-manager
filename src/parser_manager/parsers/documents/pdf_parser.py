"""
PDF-парсер на основе pdfplumber (основной) и PyPDF2 (метаданные/резерв)
"""

import logging
from datetime import datetime

import pdfplumber
from PyPDF2 import PdfReader

from parser_manager.core.base_parser import BaseParser
from parser_manager.models import (
    ParsedContent,
    DocumentMetadata,
    TextElement,
    ParsingFailedError,
    CorruptedFileError,
)
from parser_manager.utils import (
    derive_semantic_blocks,
    semantic_summary,
    score_quality,
    collect_file_metrics,
)

logger = logging.getLogger(__name__)


class PdfParser(BaseParser):
    """Парсер PDF-файлов.

    Использует pdfplumber для извлечения текста и таблиц,
    PyPDF2 — для чтения стандартных метаданных документа.
    """

    supported_extensions: tuple = (".pdf",)
    format_name: str = "pdf"
    quality_fallback_threshold: float = 0.55

    def _open_plumber(self) -> pdfplumber.PDF:
        try:
            return pdfplumber.open(str(self.file_path))
        except Exception as exc:
            raise CorruptedFileError(
                f"Не удалось открыть PDF '{self.file_path.name}': {exc}"
            ) from exc

    def _open_pypdf(self) -> PdfReader:
        try:
            return PdfReader(str(self.file_path))
        except Exception as exc:
            raise CorruptedFileError(
                f"Не удалось прочитать PDF '{self.file_path.name}': {exc}"
            ) from exc

    @staticmethod
    def _clean_text(text: str | None) -> str:
        if not text:
            return ""
        lines = [line.strip() for line in text.splitlines()]
        result, prev_empty = [], False
        for line in lines:
            if line:
                result.append(line)
                prev_empty = False
            elif not prev_empty:
                result.append("")
                prev_empty = True
        return "\n".join(result).strip()

    def extract_text(self) -> str:
        pages_text: list[str] = []
        with self._open_plumber() as pdf:
            for page in pdf.pages:
                raw = page.extract_text(x_tolerance=2, y_tolerance=2)
                cleaned = self._clean_text(raw)
                if cleaned:
                    pages_text.append(cleaned)
        return "\n\n".join(pages_text)

    def _extract_text_with_pypdf(self) -> tuple[str, list[dict]]:
        reader = self._open_pypdf()
        page_elements: list[dict] = []
        pages_text: list[str] = []

        for page_idx, page in enumerate(reader.pages, start=1):
            raw = page.extract_text() or ""
            cleaned = self._clean_text(raw)
            if cleaned:
                pages_text.append(cleaned)
                page_elements.append(
                    TextElement(
                        content=cleaned,
                        element_type="paragraph",
                        page=page_idx,
                    ).to_dict()
                )

        return "\n\n".join(pages_text), page_elements

    def extract_metadata(self) -> DocumentMetadata:
        reader = self._open_pypdf()
        info: dict[str, object] = dict(reader.metadata or {})

        def _get(key: str) -> str | None:
            val = info.get(key)
            return str(val).strip() if val else None

        def _parse_date(raw: str | None) -> datetime | None:
            if not raw:
                return None
            try:
                s = raw.lstrip("D:").replace("'", "")
                for fmt in ("%Y%m%d%H%M%S%z", "%Y%m%d%H%M%S", "%Y%m%d"):
                    try:
                        return datetime.strptime(
                            s[: len(fmt.replace("%", "XX").replace("X", ""))], fmt
                        )
                    except ValueError:
                        continue
            except Exception:
                pass
            return None

        with self._open_plumber() as pdf:
            num_pages = len(pdf.pages)

        return DocumentMetadata(
            title=_get("/Title"),
            author=_get("/Author"),
            subject=_get("/Subject"),
            creation_date=_parse_date(_get("/CreationDate")),
            modification_date=_parse_date(_get("/ModDate")),
            pages=num_pages,
            custom_fields={
                k: str(v)
                for k, v in info.items()
                if k
                not in {"/Title", "/Author", "/Subject", "/CreationDate", "/ModDate"}
                and v
            },
        )

    def extract_structure(self) -> list:
        elements: list[TextElement] = []

        with self._open_plumber() as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                for table in page.extract_tables():
                    if not table:
                        continue
                    rows = [" | ".join(cell or "" for cell in row) for row in table]
                    elements.append(
                        TextElement(
                            content="\n".join(rows), element_type="table", page=page_num
                        )
                    )

                raw = page.extract_text(x_tolerance=2, y_tolerance=2)
                cleaned = self._clean_text(raw)
                if cleaned:
                    elements.append(
                        TextElement(
                            content=cleaned, element_type="paragraph", page=page_num
                        )
                    )

        return [e.to_dict() for e in elements]

    def parse(self) -> ParsedContent:
        try:
            metadata = self.extract_metadata()
            structure = self.extract_structure()
            text = self.extract_text()

            semantic_blocks = derive_semantic_blocks(text, structure)
            quality = score_quality(text, semantic_blocks)

            backend_used = "pdfplumber"
            fallback_attempted = False

            if quality["overall_score"] < self.quality_fallback_threshold:
                fallback_attempted = True
                fallback_text, fallback_structure = self._extract_text_with_pypdf()
                fallback_semantic = derive_semantic_blocks(
                    fallback_text, fallback_structure
                )
                fallback_quality = score_quality(fallback_text, fallback_semantic)

                if fallback_quality["overall_score"] > quality["overall_score"]:
                    text = fallback_text
                    structure = fallback_structure
                    semantic_blocks = fallback_semantic
                    quality = fallback_quality
                    backend_used = "pypdf2"

            file_metrics = collect_file_metrics(
                str(self.file_path), semantic_blocks, text
            )

            return ParsedContent(
                file_path=str(self.file_path),
                format=self.format_name,
                text=text,
                metadata=metadata.to_dict(),
                structure=structure,
                semantic_blocks=semantic_blocks,
                quality=quality,
                file_metrics=file_metrics,
                raw_data={
                    "pages": metadata.pages,
                    "backend_used": backend_used,
                    "fallback_attempted": fallback_attempted,
                    "semantic_summary": semantic_summary(semantic_blocks),
                },
                success=True,
            )
        except (CorruptedFileError, ParsingFailedError):
            raise
        except Exception as exc:
            logger.exception("Ошибка при парсинге PDF: %s", self.file_path)
            raise ParsingFailedError(
                f"Не удалось разобрать файл '{self.file_path.name}': {exc}"
            ) from exc
