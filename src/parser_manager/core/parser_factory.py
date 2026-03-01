"""
Factory pattern для создания парсеров
"""

from pathlib import Path
from typing import Type, Optional
import logging

from parser_manager.core.base_parser import BaseParser
from parser_manager.models import UnsupportedFormatError


logger = logging.getLogger(__name__)


class ParserFactory:
    """
    Factory класс для создания подходящего парсера в зависимости от формата файла
    """

    # Регистр парсеров: расширение -> класс парсера
    _parsers_registry: dict[str, Type[BaseParser]] = {}

    @classmethod
    def register_parser(cls, file_extension: str, parser_class: Type[BaseParser]) -> None:
        """
        Регистрация парсера для определенного расширения файла

        Args:
            file_extension: Расширение файла (например, '.pdf')
            parser_class: Класс парсера
        """
        file_extension = file_extension.lower()
        if not file_extension.startswith("."):
            file_extension = "." + file_extension

        cls._parsers_registry[file_extension] = parser_class
        logger.debug(f"Парсер {parser_class.__name__} зарегистрирован для {file_extension}")

    @classmethod
    def register_parsers(cls, parsers: dict[str, Type[BaseParser]]) -> None:
        """
        Регистрация нескольких парсеров сразу

        Args:
            parsers: Словарь {расширение: класс парсера}
        """
        for extension, parser_class in parsers.items():
            cls.register_parser(extension, parser_class)

    @classmethod
    def get_available_formats(cls) -> list[str]:
        """
        Получить список доступных форматов

        Returns:
            list[str]: Список расширений файлов
        """
        return sorted(list(cls._parsers_registry.keys()))

    @classmethod
    def create_parser(
        cls, file_path: str, parser_class: Optional[Type[BaseParser]] = None, **kwargs
    ) -> BaseParser:
        """
        Создать парсер для файла

        Args:
            file_path: Путь к файлу
            parser_class: Опциональный класс парсера (если не указан, определяется автоматически)
            **kwargs: Дополнительные опции для парсера

        Returns:
            BaseParser: Экземпляр подходящего парсера

        Raises:
            UnsupportedFormatError: Если формат файла не поддерживается
            FileNotFoundError: Если файл не существует
        """
        file_path = Path(file_path)

        # Если парсер указан явно, используем его
        if parser_class is not None:
            logger.debug(f"Использован явно указанный парсер: {parser_class.__name__}")
            return parser_class(str(file_path), **kwargs)

        # Определяем расширение файла
        extension = file_path.suffix.lower()

        # Ищем подходящий парсер в регистре
        if extension not in cls._parsers_registry:
            available = cls.get_available_formats()
            raise UnsupportedFormatError(
                f"Формат файла '{extension}' не поддерживается. "
                f"Доступные форматы: {', '.join(available)}"
            )

        parser_class = cls._parsers_registry[extension]
        logger.info(f"Создан парсер {parser_class.__name__} для файла {file_path.name}")

        return parser_class(str(file_path), **kwargs)

    @classmethod
    def is_format_supported(cls, file_path: str) -> bool:
        """
        Проверить, поддерживается ли формат файла

        Args:
            file_path: Путь к файлу

        Returns:
            bool: True если формат поддерживается
        """
        extension = Path(file_path).suffix.lower()
        return extension in cls._parsers_registry

    @classmethod
    def clear_registry(cls) -> None:
        """Очистить регистр парсеров (полезно для тестирования)"""
        cls._parsers_registry.clear()
        logger.debug("Регистр парсеров очищен")
