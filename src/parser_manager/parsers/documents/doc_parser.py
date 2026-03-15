"""
DOC-парсер (legacy binary .doc)

Стратегия извлечения:
1) antiword/catdoc (если доступны в системе)
2) fallback: извлечение печатных строк из бинарных данных через olefile
"""

import logging
import re
import shutil
import subprocess
from datetime import datetime

import olefile

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


class DocParser(BaseParser):
    """Парсер старого формата Microsoft Word `.doc`."""

    supported_extensions: tuple = (".doc",)
    format_name: str = "doc"

    def _extract_with_cli(self) -> str:
        """Пробует извлечь текст через antiword/catdoc."""
        file_str = str(self.file_path)

        antiword = shutil.which("antiword")
        if antiword:
            proc = subprocess.run(
                [antiword, "-w", "0", file_str],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                return proc.stdout.strip()

        catdoc = shutil.which("catdoc")
        if catdoc:
            proc = subprocess.run(
                [catdoc, file_str],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if proc.returncode == 0 and proc.stdout.strip():
                return proc.stdout.strip()

        return ""

    def _extract_binary_strings(self) -> str:
        """Fallback-извлечение печатных строк из бинарного файла."""
        data = self.file_path.read_bytes()

        utf16_candidates = re.findall(rb"(?:[\x20-\x7E]\x00){4,}", data)
        utf16_text = [
            chunk.decode("utf-16le", errors="ignore") for chunk in utf16_candidates
        ]

        ascii_candidates = re.findall(rb"[\x20-\x7E]{5,}", data)
        ascii_text = [
            chunk.decode("utf-8", errors="ignore") for chunk in ascii_candidates
        ]

        lines: list[str] = []
        seen: set[str] = set()
        for value in utf16_text + ascii_text:
            cleaned = value.strip()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            lines.append(cleaned)

        return "\n".join(lines)

    def extract_text(self) -> str:
        text = self._extract_with_cli()
        if text:
            return text

        fallback = self._extract_binary_strings()
        if fallback:
            return fallback

        raise ParsingFailedError(
            "Не удалось извлечь текст из .doc. "
            "Установите antiword/catdoc для более точного извлечения."
        )

    def extract_metadata(self) -> DocumentMetadata:
        if not olefile.isOleFile(str(self.file_path)):
            raise CorruptedFileError(
                f"Файл '{self.file_path.name}' не является валидным OLE DOC"
            )

        try:
            with olefile.OleFileIO(str(self.file_path)) as ole:
                meta = ole.get_metadata()

                return DocumentMetadata(
                    title=meta.title or None,
                    author=meta.author or None,
                    subject=meta.subject or None,
                    creation_date=meta.create_time
                    if isinstance(meta.create_time, datetime)
                    else None,
                    modification_date=meta.last_saved_time
                    if isinstance(meta.last_saved_time, datetime)
                    else None,
                    pages=meta.num_pages
                    if isinstance(meta.num_pages, int) and meta.num_pages > 0
                    else None,
                    custom_fields={
                        "company": getattr(meta, "company", None),
                        "last_saved_by": getattr(meta, "last_saved_by", None),
                        "revision_number": getattr(meta, "revision_number", None),
                    },
                )
        except Exception as exc:
            raise CorruptedFileError(
                f"Не удалось прочитать метаданные DOC '{self.file_path.name}': {exc}"
            ) from exc

    def extract_structure(self) -> list:
        text = self.extract_text()
        paragraphs = [part.strip() for part in text.split("\n\n") if part.strip()]
        elements = [
            TextElement(content=p, element_type="paragraph").to_dict()
            for p in paragraphs
        ]
        if not elements and text.strip():
            elements = [
                TextElement(content=text.strip(), element_type="paragraph").to_dict()
            ]
        return elements

    def parse(self) -> ParsedContent:
        try:
            text = self.extract_text()
            metadata = self.extract_metadata()
            structure = self.extract_structure()
            semantic_blocks = derive_semantic_blocks(text, structure)
            quality = score_quality(text, semantic_blocks)
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
                raw_data={"semantic_summary": semantic_summary(semantic_blocks)},
                success=True,
            )
        except (CorruptedFileError, ParsingFailedError):
            raise
        except Exception as exc:
            logger.exception("Ошибка при парсинге DOC: %s", self.file_path)
            raise ParsingFailedError(
                f"Не удалось разобрать файл '{self.file_path.name}': {exc}"
            ) from exc
