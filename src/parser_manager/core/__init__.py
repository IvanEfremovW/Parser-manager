"""
Core module - содержит основные компоненты парсер-менеджера
"""

from .base_parser import BaseParser
from .parser_factory import ParserFactory

__all__ = [
    'BaseParser',
    'ParserFactory',
]
