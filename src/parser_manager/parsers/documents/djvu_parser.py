"""
DJVU-парсер.

Использует внешние утилиты DjVuLibre:
- djvutxt: извлечение текста
- djvused: метаданные / кол-во страниц
"""

import logging
import shutil
import subprocess
from datetime import datetime

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


class DjvuParser(BaseParser):
    """Парсер файлов `.djvu` / `.djv`."""

    supported_extensions: tuple = (".djvu", ".djv")
    format_name: str = "djvu"

    def _run(self, command: list[str], required: str) -> subprocess.CompletedProcess:
        exe = shutil.which(required)
        if not exe:
            raise ParsingFailedError(
                f"Для парсинга DJVU требуется '{required}'. "
                "Установите DjVuLibre и добавьте утилиты в PATH."
            )
        try:
            return subprocess.run(
                [exe, *command],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
        except Exception as exc:
            raise CorruptedFileError(
                f"Ошибка запуска '{required}' для файла '{self.file_path.name}': {exc}"
            ) from exc

    def extract_text(self) -> str:
        proc = self._run([str(self.file_path)], required="djvutxt")
        if proc.returncode != 0:
            raise ParsingFailedError(
                f"djvutxt завершился с ошибкой ({proc.returncode}): {proc.stderr.strip()}"
            )
        text = proc.stdout.strip()
        if not text:
            raise ParsingFailedError("В DJVU не найден текстовый слой")
        return text

    def extract_metadata(self) -> DocumentMetadata:
        pages = None
        proc_pages = self._run(["-e", "n", str(self.file_path)], required="djvused")
        if proc_pages.returncode == 0:
            raw = proc_pages.stdout.strip()
            if raw.isdigit():
                pages = int(raw)

        custom_fields: dict = {}
        proc_meta = self._run(
            ["-e", "print-meta", str(self.file_path)], required="djvused"
        )
        if proc_meta.returncode == 0 and proc_meta.stdout.strip():
            custom_fields["raw_meta"] = proc_meta.stdout.strip()

        return DocumentMetadata(pages=pages, custom_fields=custom_fields)

    def extract_structure(self) -> list:
        text = self.extract_text()
        page_chunks = [part.strip() for part in text.split("\f") if part.strip()]

        elements: list[TextElement] = []
        if page_chunks:
            for idx, chunk in enumerate(page_chunks, start=1):
                elements.append(
                    TextElement(content=chunk, element_type="paragraph", page=idx)
                )
        else:
            elements.append(TextElement(content=text, element_type="paragraph", page=1))

        return [element.to_dict() for element in elements]

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
                raw_data={
                    "parsed_with": "djvutxt/djvused",
                    "parsed_at": datetime.now().isoformat(),
                    "semantic_summary": semantic_summary(semantic_blocks),
                },
                success=True,
            )
        except (CorruptedFileError, ParsingFailedError):
            raise
        except Exception as exc:
            logger.exception("Ошибка при парсинге DJVU: %s", self.file_path)
            raise ParsingFailedError(
                f"Не удалось разобрать файл '{self.file_path.name}': {exc}"
            ) from exc
