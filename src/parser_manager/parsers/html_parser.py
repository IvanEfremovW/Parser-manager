"""
HTML-парсер на основе BeautifulSoup4
"""

import logging
from typing import Any

from bs4 import BeautifulSoup
from bs4.element import Tag

from parser_manager.core.base_parser import BaseParser
from parser_manager.models import (
    ParsedContent,
    DocumentMetadata,
    TextElement,
    ParsingFailedError,
)
from parser_manager.utils import (
    derive_semantic_blocks,
    semantic_summary,
    score_quality,
    collect_file_metrics,
)

logger = logging.getLogger(__name__)


class HtmlParser(BaseParser):
    """Парсер HTML-файлов на базе BeautifulSoup4."""

    supported_extensions: tuple = (".html", ".htm")
    format_name: str = "html"

    _BLOCK_TAGS = {"p", "div", "section", "article", "blockquote", "pre"}
    _HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

    @staticmethod
    def _attr_to_str(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None
        if isinstance(value, list):
            joined = " ".join(str(item).strip() for item in value if str(item).strip())
            return joined or None
        cleaned = str(value).strip()
        return cleaned or None

    def _load_soup(self) -> BeautifulSoup:
        raw = self.file_path.read_bytes()
        encoding = self.options.get("encoding", None)
        if encoding:
            return BeautifulSoup(raw, "lxml", from_encoding=str(encoding))

        # 1) Предпочитаем UTF-8 как самый частый вариант
        try:
            text = raw.decode("utf-8")
            return BeautifulSoup(text, "lxml")
        except UnicodeDecodeError:
            pass

        # 2) Если UTF-8 не подходит — пробуем автоопределение
        import chardet

        detected = chardet.detect(raw)
        detected_encoding = detected.get("encoding") or "utf-8"

        # 3) Безопасный резервный вариант: cp1251 для русскоязычного контента, затем замена ошибок
        for candidate in (detected_encoding, "cp1251", "utf-8"):
            try:
                text = raw.decode(candidate)
                return BeautifulSoup(text, "lxml")
            except (LookupError, UnicodeDecodeError):
                continue

        return BeautifulSoup(raw.decode("utf-8", errors="replace"), "lxml")

    def extract_text(self) -> str:
        soup = self._load_soup()
        for removable in soup(["script", "style", "noscript"]):
            removable.decompose()
        return soup.get_text(separator="\n", strip=True)

    def extract_metadata(self) -> DocumentMetadata:
        soup = self._load_soup()
        head = soup.head or BeautifulSoup("", "lxml")

        title = soup.title.string.strip() if soup.title and soup.title.string else None

        def _meta(name: str) -> str | None:
            tag = head.find("meta", attrs={"name": name})
            if tag:
                return self._attr_to_str(tag.get("content"))
            return None

        def _meta_prop(prop: str) -> str | None:
            tag = head.find("meta", attrs={"property": prop})
            if tag:
                return self._attr_to_str(tag.get("content"))
            return None

        charset_tag = head.find("meta", attrs={"charset": True})
        encoding = (
            self._attr_to_str(charset_tag.get("charset")) if charset_tag else None
        )
        if not encoding:
            ct_tag = head.find("meta", attrs={"http-equiv": "Content-Type"})
            if ct_tag:
                ct = self._attr_to_str(ct_tag.get("content")) or ""
                if "charset=" in ct.lower():
                    encoding = ct.lower().split("charset=")[-1].strip() or None

        author = _meta("author") or _meta_prop("article:author")
        description = _meta("description") or _meta_prop("og:description")
        language = self._attr_to_str(soup.html.get("lang")) if soup.html else None

        custom: dict = {}
        if description:
            custom["description"] = description
        og_title = _meta_prop("og:title")
        if og_title:
            custom["og_title"] = og_title

        return DocumentMetadata(
            title=title,
            author=author,
            language=language,
            encoding=encoding,
            custom_fields=custom,
        )

    def extract_structure(self) -> list:
        soup = self._load_soup()
        for removable in soup(["script", "style", "noscript"]):
            removable.decompose()

        elements: list[TextElement] = []

        for node in soup.body.descendants if soup.body else []:
            if not isinstance(node, Tag):
                continue

            text = node.get_text(strip=True)
            if not text:
                continue

            if node.name in self._HEADING_TAGS:
                level = int(node.name[1])
                elements.append(
                    TextElement(content=text, element_type="heading", level=level)
                )
            elif node.name in self._BLOCK_TAGS:
                elements.append(TextElement(content=text, element_type="paragraph"))
            elif node.name == "li":
                elements.append(TextElement(content=text, element_type="list"))
            elif node.name == "a":
                href = self._attr_to_str(node.get("href")) or ""
                elements.append(
                    TextElement(
                        content=text, element_type="link", metadata={"href": href}
                    )
                )
            elif node.name == "table":
                elements.append(TextElement(content=text, element_type="table"))

        return [e.to_dict() for e in elements]

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
        except Exception as exc:
            logger.exception("Ошибка при парсинге HTML: %s", self.file_path)
            raise ParsingFailedError(
                f"Не удалось разобрать файл '{self.file_path.name}': {exc}"
            ) from exc
