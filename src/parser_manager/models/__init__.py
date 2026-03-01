"""
Models package - содержит модели данных для Parser Manager
"""

from .exceptions import (
    ParserError,
    UnsupportedFormatError,
    DocumentNotFoundError,
    ParsingFailedError,
    CorruptedFileError,
    InvalidConfigurationError,
)

from .parsed_content import (
    ParsedContent,
    DocumentMetadata,
    TextElement,
)

__all__ = [
    'ParserError',
    'UnsupportedFormatError',
    'DocumentNotFoundError',
    'ParsingFailedError',
    'CorruptedFileError',
    'InvalidConfigurationError',
    'ParsedContent',
    'DocumentMetadata',
    'TextElement',
]
