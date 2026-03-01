"""
Кастомные исключения для Parser Manager
"""


class ParserError(Exception):
    """Базовое исключение для всех ошибок парсера"""
    pass


class UnsupportedFormatError(ParserError):
    """Исключение для неподдерживаемых форматов файлов"""
    pass


class DocumentNotFoundError(ParserError):
    """Исключение когда файл не найден"""
    pass


class ParsingFailedError(ParserError):
    """Исключение когда парсинг не удался"""
    pass


class CorruptedFileError(ParserError):
    """Исключение для поврежденных файлов"""
    pass


class InvalidConfigurationError(ParserError):
    """Исключение для ошибок конфигурации парсеров"""
    pass
