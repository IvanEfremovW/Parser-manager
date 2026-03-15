"""
HTML-парсер на основе BeautifulSoup4
"""

import logging

from bs4 import BeautifulSoup

from parser_manager.core.base_parser import BaseParser
from parser_manager.models import (
    ParsedContent,
    DocumentMetadata,
    TextElement,
    ParsingFailedError,
)

logger = logging.getLogger(__name__)


class HtmlParser(BaseParser):
    """Парсер HTML-файлов на базе BeautifulSoup4."""

    supported_extensions: tuple = (".html", ".htm")
    format_name: str = "html"

    _BLOCK_TAGS = {"p", "div", "section", "article", "blockquote", "pre", "li"}
    _HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

    def _load_soup(self) -> BeautifulSoup:
        raw = self.file_path.read_bytes()
        encoding = self.options.get("encoding", None)
        if encoding:
            text = raw.decode(encoding)
        else:
            import chardet
            detected = chardet.detect(raw)
            text = raw.decode(detected.get("encoding") or "utf-8", errors="replace")
        return BeautifulSoup(text, "lxml")

    def extract_text(self) -> str:
        soup = self._load_soup()
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)

    def extract_metadata(self) -> DocumentMetadata:
        soup = self._load_soup()
        head = soup.head or BeautifulSoup("", "lxml")

        title = soup.title.string.strip() if soup.title and soup.title.string else None

        def _meta(name: str) -> str | None:
            tag = head.find("meta", attrs={"name": name})
            if tag:
                return tag.get("content", "").strip() or None
            return None

        def _meta_prop(prop: str) -> str | None:
            tag = head.find("meta", attrs={"property": prop})
            if tag:
                return tag.get("content", "").strip() or None
            return None

        charset_tag = head.find("meta", attrs={"charset": True})
        encoding = charset_tag.get("charset") if charset_tag else None
        if not encoding:
            ct_tag = head.find("meta", attrs={"http-equiv": "Content-Type"})
            if ct_tag:
                ct = ct_tag.get("content", "")
                if "charset=" in ct.lower():
                    encoding = ct.lower().split("charset=")[-1].strip()

        author = _meta("author") or _meta_prop("article:author")
        description = _meta("description") or _meta_prop("og:description")
        language = soup.html.get("lang") if soup.html else None

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
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        elements: list[TextElement] = []

        for tag in soup.body.descendants if soup.body else []:
            if not hasattr(tag, "name") or tag.name is None:
                continue

            text = tag.get_text(strip=True)
            if not text:
                continue

            if tag.name in self._HEADING_TAGS:
                level = int(tag.name[1])
                elements.append(TextElement(content=text, element_type="heading", level=level))
            elif tag.name in self._BLOCK_TAGS:
                elements.append(TextElement(content=text, element_type="paragraph"))
            elif tag.name == "a":
                href = tag.get("href", "")
                elements.append(TextElement(content=text, element_type="link", metadata={"href": href}))
            elif tag.name == "table":
                elements.append(TextElement(content=text, element_type="table"))

        return [e.to_dict() for e in elements]

    def parse(self) -> ParsedContent:
        try:
            text = self.extract_text()
            metadata = self.extract_metadata()
            structure = self.extract_structure()

            return ParsedContent(
                file_path=str(self.file_path),
                format=self.format_name,
                text=text,
                metadata=metadata.to_dict(),
                structure=structure,
                success=True,
            )
        except Exception as exc:
            logger.exception("Ошибка при парсинге HTML: %s", self.file_path)
            raise ParsingFailedError(
                f"Не удалось разобрать файл '{self.file_path.name}': {exc}"
            ) from exc
