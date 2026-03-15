"""
Models package - содержит модели данных для Parser Manager
"""

from .exceptions import (
    CorruptedFileError,
    DocumentNotFoundError,
    InvalidConfigurationError,
    ParserError,
    ParsingFailedError,
    UnsupportedFormatError,
)
from .parsed_content import (
    DocumentMetadata,
    ParsedContent,
    TextElement,
)

__all__ = [
    "ParserError",
    "UnsupportedFormatError",
    "DocumentNotFoundError",
    "ParsingFailedError",
    "CorruptedFileError",
    "InvalidConfigurationError",
    "ParsedContent",
    "DocumentMetadata",
    "TextElement",
]
