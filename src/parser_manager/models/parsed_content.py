"""
Модели для представления распарсенного контента
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class ParsedContent:
    """
    Унифицированная модель результата парсинга для всех форматов файлов

    Attributes:
        file_path: Путь к исходному файлу
        format: Формат файла (html, pdf, docx, doc, djvu)
        text: Полный извлеченный текст
        metadata: Метаданные документа
        structure: Иерархическая структура содержимого
        raw_data: Дополнительные специфичные для формата данные
        parsed_at: Время парсинга
        success: Был ли парсинг успешным
        error: Сообщение об ошибке, если она произошла
    """

    file_path: str
    format: str  # 'html', 'pdf', 'docx', 'doc', 'djvu'
    text: str
    metadata: dict = field(default_factory=dict)
    structure: list = field(default_factory=list)
    semantic_blocks: list = field(default_factory=list)
    quality: dict = field(default_factory=dict)
    file_metrics: dict = field(default_factory=dict)
    doc_stats: dict = field(default_factory=dict)
    ast: dict = field(default_factory=dict)
    raw_data: dict = field(default_factory=dict)
    parsed_at: datetime = field(default_factory=datetime.now)
    success: bool = True
    error: Optional[str] = None

    # Поддерживаемые форматы — расширяемый набор
    SUPPORTED_FORMATS: frozenset = frozenset({"html", "pdf", "docx", "doc", "djvu"})

    def __post_init__(self):
        """Валидация полей после инициализации"""
        if self.format not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Неподдерживаемый формат: {self.format}")

        if not self.success and not self.error:
            raise ValueError("Если success=False, необходимо указать error")

        # Автоматически вычисляем статистику и AST если не переданы
        if not self.doc_stats and self.success:
            from parser_manager.utils.doc_stats import compute_doc_stats
            self.doc_stats = compute_doc_stats(
                self.text, self.semantic_blocks, self.metadata
            )
        if not self.ast and self.success:
            from parser_manager.utils.ast_builder import build_ast
            self.ast = build_ast(self.semantic_blocks)

    @property
    def text_length(self) -> int:
        """Получить длину извлеченного текста"""
        return len(self.text)

    @property
    def has_error(self) -> bool:
        """Проверить, есть ли ошибка"""
        return self.error is not None

    def to_dict(self) -> dict:
        """Преобразовать результат в словарь"""
        return {
            "file_path": self.file_path,
            "format": self.format,
            "text_length": self.text_length,
            "metadata": self.metadata,
            "structure": self.structure,
            "semantic_blocks": self.semantic_blocks,
            "quality": self.quality,
            "file_metrics": self.file_metrics,
            "doc_stats": self.doc_stats,
            "ast": self.ast,
            "raw_data": self.raw_data,
            "parsed_at": self.parsed_at.isoformat(),
            "success": self.success,
            "error": self.error,
        }

    def export(self, fmt: str = "json", **kwargs: object) -> str:
        """Экспортировать результат в заданный формат (json, md)."""
        from parser_manager.utils.exporters import export_content
        return export_content(self, fmt, **kwargs)


@dataclass
class DocumentMetadata:
    """Метаданные документа"""

    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    pages: Optional[int] = None
    language: Optional[str] = None
    encoding: Optional[str] = None
    custom_fields: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Преобразовать метаданные в словарь"""
        data = {
            "title": self.title,
            "author": self.author,
            "subject": self.subject,
            "creation_date": self.creation_date.isoformat()
            if self.creation_date
            else None,
            "modification_date": self.modification_date.isoformat()
            if self.modification_date
            else None,
            "pages": self.pages,
            "language": self.language,
            "encoding": self.encoding,
        }
        data.update(self.custom_fields)
        return data


@dataclass
class TextElement:
    """Элемент текста с метаинформацией"""

    content: str
    element_type: str  # 'paragraph', 'heading', 'table', 'list', 'link', etc
    level: int = 0  # Для заголовков
    style: dict = field(default_factory=dict)  # Форматирование (bold, italic, etc)
    position: Optional[dict] = None  # Координаты (для PDF)
    page: Optional[int] = None  # Номер страницы
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Преобразовать элемент в словарь"""
        return {
            "content": self.content,
            "element_type": self.element_type,
            "level": self.level,
            "style": self.style,
            "position": self.position,
            "page": self.page,
            "metadata": self.metadata,
        }
