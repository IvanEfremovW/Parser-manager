"""
Абстрактный базовый класс для всех парсеров
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import logging

from parser_manager.models import (
    ParsedContent,
    DocumentMetadata,
    ParserError,
    DocumentNotFoundError,
    UnsupportedFormatError,
)


logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """
    Абстрактный базовый класс для всех парсеров.
    Определяет единый интерфейс для парсинга различных форматов.
    """

    # Поддерживаемые расширения файлов
    supported_extensions: tuple = ()

    # Формат документа
    format_name: str = ""

    def __init__(self, file_path: str, **kwargs):
        """
        Инициализация парсера

        Args:
            file_path: Путь к файлу для парсинга
            **kwargs: Дополнительные опции для парсера
        """
        self.file_path = Path(file_path)
        self.options = kwargs
        self._validate_file()

    def _validate_file(self) -> None:
        """Валидация файла перед парсингом"""
        if not self.file_path.exists():
            raise DocumentNotFoundError(f"Файл не найден: {self.file_path}")

        if not self.file_path.is_file():
            raise ParserError(f"Путь не является файлом: {self.file_path}")

        if self.file_path.suffix.lower() not in self.supported_extensions:
            raise UnsupportedFormatError(
                f"Файл {self.file_path.name} имеет расширение "
                f"{self.file_path.suffix}, поддерживаются только: {self.supported_extensions}"
            )

    @abstractmethod
    def parse(self) -> ParsedContent:
        """
        Главный метод парсинга. Должен быть реализован в подклассах.

        Returns:
            ParsedContent: Результат парсинга
        """
        pass

    @abstractmethod
    def extract_text(self) -> str:
        """Извлечение текста из документа"""
        pass

    @abstractmethod
    def extract_metadata(self) -> DocumentMetadata:
        """Извлечение метаданных из документа"""
        pass

    def extract_structure(self) -> list:
        """
        Извлечение структуры документа.
        По умолчанию возвращает пустой список, переопределяется в подклассах.

        Returns:
            list: Структура документа
        """
        return []

    def validate_parse_result(self, result: ParsedContent) -> bool:
        """
        Валидация результата парсинга

        Args:
            result: Результат парсинга

        Returns:
            bool: True если результат валиден
        """
        if not isinstance(result, ParsedContent):
            return False

        if result.format != self.format_name:
            return False

        if not result.success and result.error is None:
            return False

        return True

    def get_file_info(self) -> dict:
        """Получить информацию о файле"""
        return {
            "path": str(self.file_path),
            "name": self.file_path.name,
            "size": self.file_path.stat().st_size,
            "suffix": self.file_path.suffix,
            "format": self.format_name,
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(file='{self.file_path.name}')"
