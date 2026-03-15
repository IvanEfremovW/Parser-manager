# Тестовый План — Parser Manager

## 1. Введение

### Цели Тестирования
- Проверка функциональности всех парсеров
- Валидация выходных данных (semantic JSON)
- Проверка обработки ошибок и исключительных ситуаций
- Тестирование API endpoints и рабочих процессов
- Оценка качества парсинга (quality scoring)
- Интеграционное тестирование полного пайплайна
- Проверка конкурентной обработки задач

---

## 2. Технологический Стек Тестирования

### 2.1 Инструменты

| Компонент     | Технология         | Версия  | Назначение                     |
| ---------------| --------------------| ---------| --------------------------------|
| Test Runner   | pytest             | ≥9.0.0  | Запуск и организация тестов    |
| Coverage      | pytest-cov         | ≥7.0.0  | Измерение покрытия кода        |
| Async Testing | pytest-asyncio     | ≥1.3.0  | Тестирование асинхронного кода |
| Mocking       | pytest-mock        | ≥3.15.0 | Мокирование зависимостей       |
| HTTP Testing  | httpx + TestClient | ≥0.27.0 | Тестирование API               |

### 2.2 Конфигурация

**Файл:** `pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--tb=short",
    "--strict-markers",
    "--cov=parser_manager",
    "--cov-report=term-missing",
    "--cov-report=html:htmlcov",
    "--cov-report=xml:coverage.xml",
]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "api: marks tests as API tests",
    "parser: marks tests as parser-specific tests",
    "requires_external: marks tests requiring external dependencies",
]
asyncio_mode = "auto"
```

---

## 3. Уровни Тестирования

### 3.1 Unit Tests (Юнит-тесты)

**Объект тестирования:** Отдельные функции, классы, методы

**Структура:**
```
tests/unit/
├── core/           # Ядро системы
├── models/         # Модели данных
├── parsers/        # Парсеры форматов
├── utils/          # Утилиты
└── api/            # REST API
```

**Критерии входа:**
- Код модуля написан
- Зависимости доступны
- Фикстуры настроены

**Критерии выхода:**
- Все тесты проходят
- Покрытие ≥85%
- Нет критических замечаний

---

### 3.2 Integration Tests (Интеграционные тесты)

**Объект тестирования:** Взаимодействие между компонентами

**Структура:**
```
tests/integration/
└── test_full_pipeline.py  # Полный пайплайн парсинга
```

**Сценарии:**
- Полный пайплайн парсинга (file → parser → semantic JSON)
- API workflow (create job → process → get result)
- Консистентность метрик качества
-Propagation ошибок
- Параллельные операции парсинга
- Персистентность реестра парсеров

**Критерии входа:**
- Все юнит-тесты проходят
- Интеграционные точки определены
- Тестовое окружение готово

**Критерии выхода:**
- Все интеграционные сценарии работают
- Время выполнения приемлемо
- Ошибки обрабатываются корректно

---

## 4. Детальный План Тестов

### 4.1 Core Module (Ядро)

#### 4.1.1 BaseParser (test_base_parser.py)

**Файл:** `tests/unit/core/test_base_parser.py`

| ID Теста | Название | Описание | Приоритет |
|----------|----------|----------|-----------|
| UT-CORE-001 | test_parser_init_with_valid_file | Инициализация с валидным файлом | Высокий |
| UT-CORE-002 | test_parser_init_stores_options | Сохранение опций инициализации | Средний |
| UT-CORE-003 | test_parser_repr | Строковое представление | Низкий |
| UT-CORE-004 | test_parser_raises_on_missing_file | Ошибка при отсутствующем файле | Высокий |
| UT-CORE-005 | test_parser_raises_on_directory | Ошибка при пути-директории | Высокий |
| UT-CORE-006 | test_parser_raises_on_unsupported_extension | Ошибка неподдерживаемого расширения | Высокий |
| UT-CORE-007 | test_parser_accepts_supported_extension | Принятие поддерживаемого расширения | Высокий |
| UT-CORE-008 | test_get_file_info | Получение информации о файле | Средний |
| UT-CORE-009 | test_validate_parse_result_success | Валидация успешного результата | Высокий |
| UT-CORE-010 | test_validate_parse_result_wrong_type | Валидация неверного типа | Средний |
| UT-CORE-011 | test_validate_parse_result_wrong_format | Валидация неверного формата | Средний |
| UT-CORE-012 | test_validate_parse_result_failed_without_error | Валидация failed без error | Средний |
| UT-CORE-013 | test_extract_structure_default_implementation | Структура по умолчанию | Низкий |
| UT-CORE-014 | test_parser_with_unicode_path | Unicode в пути | Средний |
| UT-CORE-015 | test_parser_with_spaces_in_path | Пробелы в пути | Низкий |
| UT-CORE-016 | test_parser_case_insensitive_extension | Регистронезависимость расширений | Средний |

---

#### 4.1.2 ParserFactory (test_parser_factory.py)

**Файл:** `tests/unit/core/test_parser_factory.py`

| ID Теста | Название | Описание | Приоритет |
|----------|----------|----------|-----------|
| UT-CORE-017 | test_register_single_parser | Регистрация одного парсера | Высокий |
| UT-CORE-018 | test_register_parser_normalizes_extension | Нормализация расширения | Средний |
| UT-CORE-019 | test_register_parser_case_insensitive | Регистронезависимость регистрации | Средний |
| UT-CORE-020 | test_register_multiple_parsers | Массовая регистрация | Высокий |
| UT-CORE-021 | test_register_parser_overwrites_existing | Перезапись регистрации | Низкий |
| UT-CORE-022 | test_get_available_formats | Получение списка форматов | Высокий |
| UT-CORE-023 | test_get_available_formats_empty | Пустой список форматов | Низкий |
| UT-CORE-024 | test_clear_registry | Очистка реестра | Средний |
| UT-CORE-025 | test_is_format_supported_true | Проверка поддержки (true) | Высокий |
| UT-CORE-026 | test_is_format_supported_false | Проверка поддержки (false) | Высокий |
| UT-CORE-027 | test_create_parser_auto_detect | Авто-определение парсера | Высокий |
| UT-CORE-028 | test_create_parser_explicit_class | Явное указание класса | Средний |
| UT-CORE-029 | test_create_parser_passes_kwargs | Передача kwargs | Средний |
| UT-CORE-030 | test_create_parser_unsupported_format | Неподдерживаемый формат | Высокий |
| UT-CORE-031 | test_create_parser_case_insensitive_extension | Регистронезависимость создания | Средний |
| UT-CORE-032 | test_registry_thread_safety | Потокобезопасность реестра | Средний |
| UT-CORE-033 | test_register_parser_with_complex_extension | Сложное расширение | Низкий |
| UT-CORE-034 | test_create_parser_with_path_object | Path объект | Низкий |
| UT-CORE-035 | test_multiple_extensions_same_parser | Несколько расширений одного парсера | Средний |

---

### 4.2 Models Module (Модели)

#### 4.2.1 DocumentMetadata (test_parsed_content.py)

**Файл:** `tests/unit/models/test_parsed_content.py`

| ID Теста | Название | Описание | Приоритет |
|----------|----------|----------|-----------|
| UT-MOD-001 | test_create_metadata_with_all_fields | Создание со всеми полями | Высокий |
| UT-MOD-002 | test_create_metadata_minimal | Создание с минимальными полями | Высокий |
| UT-MOD-003 | test_metadata_to_dict | Конвертация в dict | Высокий |
| UT-MOD-004 | test_metadata_to_dict_datetime_format | Формат datetime | Средний |
| UT-MOD-005 | test_metadata_to_dict_none_datetime | None datetime | Средний |
| UT-MOD-006 | test_metadata_custom_fields_merged | Объединение custom полей | Средний |

---

#### 4.2.2 TextElement (test_parsed_content.py)

| ID Теста | Название | Описание | Приоритет |
|----------|----------|----------|-----------|
| UT-MOD-007 | test_create_text_element_minimal | Минимальный элемент | Высокий |
| UT-MOD-008 | test_create_text_element_full | Полный элемент | Средний |
| UT-MOD-009 | test_text_element_to_dict | Конвертация в dict | Высокий |
| UT-MOD-010 | test_text_element_all_types | Все типы элементов | Высокий |
| UT-MOD-011 | test_text_element_link_metadata | Метаданные ссылки | Средний |

---

#### 4.2.3 ParsedContent (test_parsed_content.py)

| ID Теста | Название | Описание | Приоритет |
|----------|----------|----------|-----------|
| UT-MOD-012 | test_create_parsed_content_success | Успешное создание | Высокий |
| UT-MOD-013 | test_create_parsed_content_validation_error | Ошибка валидации | Высокий |
| UT-MOD-014 | test_create_parsed_content_unsupported_format | Неподдерживаемый формат | Высокий |
| UT-MOD-015 | test_create_parsed_content_supported_formats | Поддерживаемые форматы | Высокий |
| UT-MOD-016 | test_parsed_content_text_length | Длина текста | Средний |
| UT-MOD-017 | test_parsed_content_has_error_true | has_error = true | Средний |
| UT-MOD-018 | test_parsed_content_has_error_false | has_error = false | Средний |
| UT-MOD-019 | test_parsed_content_to_dict | Конвертация в dict | Высокий |
| UT-MOD-020 | test_parsed_content_to_dict_parsed_at_iso | ISO формат parsed_at | Средний |
| UT-MOD-021 | test_parsed_content_to_dict_includes_text_length | text_length в dict | Средний |
| UT-MOD-022 | test_parsed_content_default_values | Значения по умолчанию | Средний |
| UT-MOD-023 | test_parsed_content_parsed_at_auto | Авто parsed_at | Низкий |
| UT-MOD-024 | test_parsed_content_with_error_message | Сообщение ошибки | Средний |
| UT-MOD-025 | test_parsed_content_empty_text | Пустой текст | Низкий |
| UT-MOD-026 | test_parsed_content_unicode_text | Unicode текст | Средний |
| UT-MOD-027 | test_parsed_content_large_text | Большой текст | Низкий |
| UT-MOD-028 | test_parsed_content_complex_metadata | Сложные метаданные | Средний |

---

#### 4.2.4 Exceptions (test_exceptions.py)

**Файл:** `tests/unit/models/test_exceptions.py`

| ID Теста | Название | Описание | Приоритет |
|----------|----------|----------|-----------|
| UT-MOD-029 | test_parser_error_basic | Базовый ParserError | Высокий |
| UT-MOD-030 | test_parser_error_inheritance | Наследование ParserError | Высокий |
| UT-MOD-031 | test_parser_error_raise_catch | Выброс и перехват | Высокий |
| UT-MOD-032 | test_unsupported_format_error_basic | Базовый UnsupportedFormatError | Высокий |
| UT-MOD-033 | test_unsupported_format_error_inheritance | Наследование UnsupportedFormatError | Высокий |
| UT-MOD-034 | test_unsupported_format_error_detailed | Детальный UnsupportedFormatError | Средний |
| UT-MOD-035 | test_document_not_found_error_basic | Базовый DocumentNotFoundError | Высокий |
| UT-MOD-036 | test_document_not_found_error_inheritance | Наследование DocumentNotFoundError | Высокий |
| UT-MOD-037 | test_parsing_failed_error_basic | Базовый ParsingFailedError | Высокий |
| UT-MOD-038 | test_parsing_failed_error_inheritance | Наследование ParsingFailedError | Высокий |
| UT-MOD-039 | test_parsing_failed_error_with_cause | ParsingFailedError с причиной | Средний |
| UT-MOD-040 | test_corrupted_file_error_basic | Базовый CorruptedFileError | Высокий |
| UT-MOD-041 | test_corrupted_file_error_inheritance | Наследование CorruptedFileError | Высокий |
| UT-MOD-042 | test_invalid_configuration_error_basic | Базовый InvalidConfigurationError | Средний |
| UT-MOD-043 | test_invalid_configuration_error_inheritance | Наследование InvalidConfigurationError | Средний |
| UT-MOD-044 | test_all_exceptions_are_parser_errors | Все исключения — ParserError | Высокий |
| UT-MOD-045 | test_catch_all_with_base_exception | Перехват базовым исключением | Высокий |
| UT-MOD-046 | test_specific_exception_can_be_caught | Перехват специфичных | Высокий |

---

### 4.3 Utils Module (Утилиты)

#### 4.3.1 semantic_json (test_semantic_json.py)

**Файл:** `tests/unit/utils/test_semantic_json.py`

| ID Теста | Название | Описание | Приоритет |
|----------|----------|----------|-----------|
| UT-UTIL-001 | test_normalize_block_basic | Базовая нормализация | Высокий |
| UT-UTIL-002 | test_normalize_block_preserves_all_fields | Сохранение полей | Высокий |
| UT-UTIL-003 | test_normalize_block_invalid_element_type | Invalid element_type | Высокий |
| UT-UTIL-004 | test_normalize_block_element_type_case_insensitive | Регистронезависимость | Средний |
| UT-UTIL-005 | test_normalize_block_all_allowed_types | Все разрешённые типы | Высокий |
| UT-UTIL-006 | test_normalize_block_strips_content | Обрезка content | Средний |
| UT-UTIL-007 | test_normalize_block_empty_content | Пустой content | Средний |
| UT-UTIL-008 | test_normalize_block_none_content | None content | Высокий |
| UT-UTIL-009 | test_normalize_block_level_conversion | Конверсия level | Средний |
| UT-UTIL-010 | test_normalize_block_none_level | None level | Средний |
| UT-UTIL-011 | test_normalize_block_default_page | Default page | Средний |
| UT-UTIL-012 | test_normalize_block_page_override | Override page | Средний |
| UT-UTIL-013 | test_normalize_block_none_metadata | None metadata | Средний |
| UT-UTIL-014 | test_normalize_structure_basic | Базовая нормализация структуры | Высокий |
| UT-UTIL-015 | test_normalize_structure_empty | Пустая структура | Средний |
| UT-UTIL-016 | test_normalize_structure_none | None структура | Средний |
| UT-UTIL-017 | test_normalize_structure_filters_empty_content | Фильтрация пустого content | Высокий |
| UT-UTIL-018 | test_normalize_structure_filters_non_dicts | Фильтрация не-dict | Высокий |
| UT-UTIL-019 | test_normalize_structure_normalizes_each_block | Нормализация каждого блока | Высокий |
| UT-UTIL-020 | test_derive_semantic_blocks_from_structure | Получение из структуры | Высокий |
| UT-UTIL-021 | test_derive_semantic_blocks_fallback_to_text | Fallback на текст | Высокий |
| UT-UTIL-022 | test_derive_semantic_blocks_fallback_none_structure | Fallback при None структуре | Высокий |
| UT-UTIL-023 | test_derive_semantic_blocks_empty_text | Пустой текст | Средний |
| UT-UTIL-024 | test_derive_semantic_blocks_structure_takes_precedence | Приоритет структуры | Высокий |
| UT-UTIL-025 | test_semantic_summary_basic | Базовый summary | Высокий |
| UT-UTIL-026 | test_semantic_summary_empty | Пустой summary | Средний |
| UT-UTIL-027 | test_semantic_summary_none_blocks | None блоки | Высокий |
| UT-UTIL-028 | test_semantic_summary_pages_detected | Обнаруженные страницы | Средний |
| UT-UTIL-029 | test_semantic_summary_all_block_types | Все типы блоков | Высокий |
| UT-UTIL-030 | test_semantic_summary_missing_element_type | Missing element_type | Средний |

---

#### 4.3.2 quality (test_quality.py)

**Файл:** `tests/unit/utils/test_quality.py`

| ID Теста | Название | Описание | Приоритет |
|----------|----------|----------|-----------|
| UT-UTIL-031 | test_safe_ratio_basic | Базовое соотношение | Высокий |
| UT-UTIL-032 | test_safe_ratio_zero_denominator | Нулевой знаменатель | Высокий |
| UT-UTIL-033 | test_safe_ratio_negative_denominator | Отрицательный знаменатель | Средний |
| UT-UTIL-034 | test_safe_ratio_clamps_to_1 | Ограничение до 1 | Высокий |
| UT-UTIL-035 | test_safe_ratio_clamps_to_0 | Ограничение до 0 | Высокий |
| UT-UTIL-036 | test_score_quality_basic | Базовая оценка качества | Высокий |
| UT-UTIL-037 | test_score_quality_all_metrics_present | Все метрики присутствуют | Высокий |
| UT-UTIL-038 | test_score_quality_empty_text | Пустой текст | Высокий |
| UT-UTIL-039 | test_score_quality_text_completeness_threshold | Порог text_completeness | Высокий |
| UT-UTIL-040 | test_score_quality_structure_score_threshold | Порог structure_score | Высокий |
| UT-UTIL-041 | test_score_quality_noise_ratio_non_printable | noise_ratio непечатные | Высокий |
| UT-UTIL-042 | test_score_quality_broken_chars_ratio | broken_chars_ratio | Высокий |
| UT-UTIL-043 | test_score_quality_table_coverage | table_coverage | Высокий |
| UT-UTIL-044 | test_score_quality_char_count | char_count | Средний |
| UT-UTIL-045 | test_score_quality_word_count | word_count | Средний |
| UT-UTIL-046 | test_score_quality_word_count_unicode | word_count unicode | Средний |
| UT-UTIL-047 | test_score_quality_block_count | block_count | Средний |
| UT-UTIL-048 | test_score_quality_overall_score_bounds | Границы overall_score | Высокий |
| UT-UTIL-049 | test_score_quality_rounding | Округление | Средний |
| UT-UTIL-050 | test_score_quality_none_blocks | None блоки | Высокий |
| UT-UTIL-051 | test_score_quality_weird_symbols | Странные символы | Средний |
| UT-UTIL-052 | test_score_quality_very_long_text | Очень длинный текст | Низкий |
| UT-UTIL-053 | test_score_quality_single_character | Один символ | Низкий |
| UT-UTIL-054 | test_score_quality_only_whitespace | Только пробелы | Низкий |
| UT-UTIL-055 | test_score_quality_mixed_block_types | Смешанные типы блоков | Средний |

---

#### 4.3.3 file_metrics (test_file_metrics.py)

**Файл:** `tests/unit/utils/test_file_metrics.py`

| ID Теста | Название | Описание | Приоритет |
|----------|----------|----------|-----------|
| UT-UTIL-056 | test_collect_file_metrics_basic | Базовый сбор метрик | Высокий |
| UT-UTIL-057 | test_collect_file_metrics_all_fields | Все поля присутствуют | Высокий |
| UT-UTIL-058 | test_collect_file_metrics_extension_lowercase | Lowercase расширение | Средний |
| UT-UTIL-059 | test_collect_file_metrics_avg_block_length | Средняя длина блока | Высокий |
| UT-UTIL-060 | test_collect_file_metrics_avg_block_length_empty | Пустая средняя длина | Средний |
| UT-UTIL-061 | test_collect_file_metrics_max_block_length | Максимальная длина блока | Высокий |
| UT-UTIL-062 | test_collect_file_metrics_max_block_length_empty | Пустая максимальная длина | Средний |
| UT-UTIL-063 | test_collect_file_metrics_nonexistent_file | Несуществующий файл | Высокий |
| UT-UTIL-064 | test_collect_file_metrics_strips_block_content | Обрезка content блока | Средний |
| UT-UTIL-065 | test_collect_file_metrics_empty_block_content | Пустой content блока | Средний |
| UT-UTIL-066 | test_collect_file_metrics_none_blocks | None блоки | Высокий |
| UT-UTIL-067 | test_collect_file_metrics_file_size_accuracy | Точность размера файла | Средний |
| UT-UTIL-068 | test_collect_file_metrics_complex_path | Сложный путь | Низкий |
| UT-UTIL-069 | test_collect_file_metrics_unicode_filename | Unicode имя файла | Средний |
| UT-UTIL-070 | test_collect_file_metrics_spaces_in_path | Пробелы в пути | Низкий |
| UT-UTIL-071 | test_collect_file_metrics_no_extension | Без расширения | Низкий |
| UT-UTIL-072 | test_collect_file_metrics_multiple_dots | Множественные точки | Низкий |
| UT-UTIL-073 | test_collect_file_metrics_very_long_blocks | Очень длинные блоки | Низкий |
| UT-UTIL-074 | test_collect_file_metrics_many_blocks | Много блоков | Низкий |

---

### 4.4 Parsers Module (Парсеры)

#### 4.4.1 HtmlParser (test_html_parser.py)

**Файл:** `tests/unit/parsers/test_html_parser.py`

| ID Теста | Название | Описание | Приоритет |
|----------|----------|----------|-----------|
| UT-PARSER-001 | test_html_parser_supported_extensions | Поддерживаемые расширения | Высокий |
| UT-PARSER-002 | test_html_parser_parse_success | Успешный парсинг | Высокий |
| UT-PARSER-003 | test_html_parser_extract_text | Извлечение текста | Высокий |
| UT-PARSER-004 | test_html_parser_extract_metadata | Извлечение метаданных | Высокий |
| UT-PARSER-005 | test_html_parser_extract_structure | Извлечение структуры | Высокий |
| UT-PARSER-006 | test_html_parser_heading_levels | Уровни заголовков | Высокий |
| UT-PARSER-007 | test_html_parser_link_metadata | Метаданные ссылок | Средний |
| UT-PARSER-008 | test_html_parser_empty_file | Пустой файл | Средний |
| UT-PARSER-009 | test_html_parser_missing_file | Отсутствующий файл | Высокий |
| UT-PARSER-010 | test_html_parser_malformed_html | Неправильный HTML | Средний |
| UT-PARSER-011 | test_html_parser_encoding_detection | Определение кодировки | Высокий |
| UT-PARSER-012 | test_html_parser_explicit_encoding | Явная кодировка | Средний |
| UT-PARSER-013 | test_html_parser_htm_extension | Расширение .htm | Средний |
| UT-PARSER-014 | test_html_parser_case_insensitive_tags | Регистронезависимые теги | Низкий |
| UT-PARSER-015 | test_html_parser_nested_elements | Вложенные элементы | Средний |
| UT-PARSER-016 | test_html_parser_whitespace_handling | Обработка пробелов | Средний |
| UT-PARSER-017 | test_html_parser_result_has_quality_metrics | Метрики качества в результате | Высокий |
| UT-PARSER-018 | test_html_parser_result_has_file_metrics | Метрики файла в результате | Высокий |
| UT-PARSER-019 | test_html_parser_result_has_semantic_blocks | Semantic блоки в результате | Высокий |
| UT-PARSER-020 | test_html_parser_result_has_raw_data | raw_data в результате | Средний |

---

#### 4.4.2 PdfParser (test_pdf_parser.py)

**Файл:** `tests/unit/parsers/test_pdf_parser.py`

| ID Теста | Название | Описание | Приоритет |
|----------|----------|----------|-----------|
| UT-PARSER-021 | test_pdf_parser_supported_extensions | Поддерживаемые расширения | Высокий |
| UT-PARSER-022 | test_pdf_parser_quality_threshold | Порог качества fallback | Высокий |
| UT-PARSER-023 | test_pdf_parser_parse_success | Успешный парсинг | Высокий |
| UT-PARSER-024 | test_pdf_parser_extract_text | Извлечение текста | Высокий |
| UT-PARSER-025 | test_pdf_parser_extract_metadata | Извлечение метаданных | Высокий |
| UT-PARSER-026 | test_pdf_parser_extract_structure | Извлечение структуры | Высокий |
| UT-PARSER-027 | test_pdf_parser_structure_has_pages | Страницы в структуре | Высокий |
| UT-PARSER-028 | test_pdf_parser_raw_data_backend | backend_used в raw_data | Высокий |
| UT-PARSER-029 | test_pdf_parser_raw_data_pages | pages в raw_data | Высокий |
| UT-PARSER-030 | test_pdf_parser_fallback_attempted_flag | Флаг fallback_attempted | Высокий |
| UT-PARSER-031 | test_pdf_parser_quality_score_present | quality_score присутствует | Высокий |
| UT-PARSER-032 | test_pdf_parser_missing_file | Отсутствующий файл | Высокий |
| UT-PARSER-033 | test_pdf_parser_corrupted_file | Повреждённый файл | Высокий |
| UT-PARSER-034 | test_pdf_parser_empty_file | Пустой файл | Средний |
| UT-PARSER-035 | test_pdf_parser_clean_text_method | Метод _clean_text | Средний |
| UT-PARSER-036 | test_pdf_parser_multiple_pages_pdf | Многостраничный PDF | Средний |
| UT-PARSER-037 | test_pdf_parser_result_has_quality_metrics | Метрики качества | Высокий |
| UT-PARSER-038 | test_pdf_parser_result_has_file_metrics | Метрики файла | Высокий |
| UT-PARSER-039 | test_pdf_parser_result_has_semantic_blocks | Semantic блоки | Высокий |
| UT-PARSER-040 | test_pdf_parser_tables_extraction | Извлечение таблиц | Средний |

---

#### 4.4.3 DocxParser (test_docx_parser.py)

**Файл:** `tests/unit/parsers/test_docx_parser.py`

| ID Теста | Название | Описание | Приоритет |
|----------|----------|----------|-----------|
| UT-PARSER-041 | test_docx_parser_supported_extensions | Поддерживаемые расширения | Высокий |
| UT-PARSER-042 | test_docx_parser_parse_success | Успешный парсинг | Высокий |
| UT-PARSER-043 | test_docx_parser_extract_text | Извлечение текста | Высокий |
| UT-PARSER-044 | test_docx_parser_extract_metadata | Извлечение метаданных | Высокий |
| UT-PARSER-045 | test_docx_parser_extract_structure | Извлечение структуры | Высокий |
| UT-PARSER-046 | test_docx_parser_heading_levels | Уровни заголовков | Высокий |
| UT-PARSER-047 | test_docx_parser_table_extraction | Извлечение таблиц | Высокий |
| UT-PARSER-048 | test_docx_parser_list_extraction | Извлечение списков | Средний |
| UT-PARSER-049 | test_docx_parser_missing_file | Отсутствующий файл | Высокий |
| UT-PARSER-050 | test_docx_parser_corrupted_file | Повреждённый файл | Высокий |
| UT-PARSER-051 | test_docx_parser_empty_document | Пустой документ | Средний |
| UT-PARSER-052 | test_docx_parser_document_only_text | Только текст | Средний |
| UT-PARSER-053 | test_docx_parser_document_complex_structure | Сложная структура | Высокий |
| UT-PARSER-054 | test_docx_parser_metadata_dates | Даты в метаданных | Средний |
| UT-PARSER-055 | test_docx_parser_metadata_custom_fields | Custom поля метаданных | Средний |
| UT-PARSER-056 | test_docx_parser_result_has_quality_metrics | Метрики качества | Высокий |
| UT-PARSER-057 | test_docx_parser_result_has_file_metrics | Метрики файла | Высокий |
| UT-PARSER-058 | test_docx_parser_result_has_semantic_blocks | Semantic блоки | Высокий |
| UT-PARSER-059 | test_docx_parser_result_has_raw_data | raw_data | Средний |
| UT-PARSER-060 | test_docx_parser_paragraphs_count | Количество параграфов | Низкий |
| UT-PARSER-061 | test_docx_parser_style_name_none | None имя стиля | Низкий |
| UT-PARSER-062 | test_docx_parser_unicode_content | Unicode контент | Средний |

---

#### 4.4.4 DocParser (test_doc_parser.py)

**Файл:** `tests/unit/parsers/test_doc_parser.py`

| ID Теста | Название | Описание | Приоритет |
|----------|----------|----------|-----------|
| UT-PARSER-063 | test_doc_parser_supported_extensions | Поддерживаемые расширения | Высокий |
| UT-PARSER-064 | test_doc_parser_corrupted_file_raises_error | Ошибка повреждённого файла | Высокий |
| UT-PARSER-065 | test_doc_parser_not_ole_file | Не OLE файл | Высокий |
| UT-PARSER-066 | test_doc_parser_missing_file | Отсутствующий файл | Высокий |
| UT-PARSER-067 | test_doc_parser_extract_text_fallback | Fallback извлечение текста | Средний |
| UT-PARSER-068 | test_doc_parser_extract_text_no_tools | Без внешних инструментов | Высокий |
| UT-PARSER-069 | test_doc_parser_extract_structure | Извлечение структуры | Средний |
| UT-PARSER-070 | test_doc_parser_extract_with_cli_antiword_not_found | antiword не найден | Средний |
| UT-PARSER-071 | test_doc_parser_extract_with_cli_catdoc_success | catdoc успешен | Средний |
| UT-PARSER-072 | test_doc_parser_binary_string_extraction | Бинарное извлечение строк | Средний |
| UT-PARSER-073 | test_doc_parser_binary_string_extraction_utf16 | UTF-16 извлечение | Средний |
| UT-PARSER-074 | test_doc_parser_metadata_ole_check | OLE проверка метаданных | Высокий |
| UT-PARSER-075 | test_doc_parser_repr | Строковое представление | Низкий |
| UT-PARSER-076 | test_doc_parser_get_file_info | Информация о файле | Средний |
| UT-PARSER-077 | test_doc_parser_external_tools_check | Проверка внешних инструментов | Средний |
| UT-PARSER-078 | test_doc_parser_with_antiword | С antiword (если доступен) | Низкий |

---

#### 4.4.5 DjvuParser (test_djvu_parser.py)

**Файл:** `tests/unit/parsers/test_djvu_parser.py`

| ID Теста | Название | Описание | Приоритет |
|----------|----------|----------|-----------|
| UT-PARSER-079 | test_djvu_parser_supported_extensions | Поддерживаемые расширения | Высокий |
| UT-PARSER-080 | test_djvu_parser_missing_djvutxt_raises_error | Отсутствие djvutxt | Высокий |
| UT-PARSER-081 | test_djvu_parser_missing_djvused_raises_error | Отсутствие djvused | Высокий |
| UT-PARSER-082 | test_djvu_parser_extract_text_command_failure | Ошибка команды извлечения текста | Высокий |
| UT-PARSER-083 | test_djvu_parser_extract_text_empty_output | Пустой вывод извлечения текста | Высокий |
| UT-PARSER-084 | test_djvu_parser_extract_metadata_command_failure | Ошибка команды извлечения метаданных | Высокий |
| UT-PARSER-085 | test_djvu_parser_extract_metadata_pages_parsing | Парсинг количества страниц | Высокий |
| UT-PARSER-086 | test_djvu_parser_extract_metadata_pages_non_numeric | Не-числовое количество страниц | Средний |
| UT-PARSER-087 | test_djvu_parser_extract_structure_from_text | Структура из текста | Высокий |
| UT-PARSER-088 | test_djvu_parser_extract_structure_single_page | Одностраничная структура | Средний |
| UT-PARSER-089 | test_djvu_parser_missing_file | Отсутствующий файл | Высокий |
| UT-PARSER-090 | test_djvu_parser_djv_extension | Расширение .djv | Средний |
| UT-PARSER-091 | test_djvu_parser_run_method_success | Успешный _run метод | Средний |
| UT-PARSER-092 | test_djvu_parser_run_method_missing_tool | Отсутствие инструмента в _run | Высокий |
| UT-PARSER-093 | test_djvu_parser_run_method_exception | Исключение в _run | Высокий |
| UT-PARSER-094 | test_djvu_parser_parse_full_flow | Полный поток парсинга | Высокий |
| UT-PARSER-095 | test_djvu_parser_repr | Строковое представление | Низкий |
| UT-PARSER-096 | test_djvu_parser_get_file_info | Информация о файле | Средний |
| UT-PARSER-097 | test_djvu_parser_unicode_error_handling | Обработка unicode ошибок | Средний |
| UT-PARSER-098 | test_djvu_parser_metadata_raw_meta | raw_meta в метаданных | Низкий |

---

### 4.5 API Module

#### 4.5.1 App (test_app.py)

**Файл:** `tests/unit/api/test_app.py`

| ID Теста | Название | Описание | Приоритет |
|----------|----------|----------|-----------|
| UT-API-001 | test_health_endpoint_success | Успешный health endpoint | Высокий |
| UT-API-002 | test_health_endpoint_response_structure | Структура ответа health | Высокий |
| UT-API-003 | test_create_parse_job_success | Успешное создание задачи | Высокий |
| UT-API-004 | test_create_parse_job_with_webhook | Создание с webhook | Высокий |
| UT-API-005 | test_create_parse_job_missing_file | Создание без файла | Высокий |
| UT-API-006 | test_create_parse_job_job_id_format | Формат job_id | Высокий |
| UT-API-007 | test_get_job_status_not_found | Статус несуществующей задачи | Высокий |
| UT-API-008 | test_get_job_status_structure | Структура статуса задачи | Высокий |
| UT-API-009 | test_get_job_result_not_found | Результат несуществующей задачи | Высокий |
| UT-API-010 | test_get_job_result_processing | Результат во время обработки | Высокий |
| UT-API-011 | test_api_cors_headers | CORS заголовки | Низкий |
| UT-API-012 | test_api_invalid_method | Неверный HTTP метод | Средний |
| UT-API-013 | test_api_root_not_found | Корневой endpoint | Низкий |
| UT-API-014 | test_api_docs_available | Доступность документации | Средний |
| UT-API-015 | test_api_openapi_schema | OpenAPI схема | Высокий |
| UT-API-016 | test_api_multiple_jobs | Множественные задачи | Средний |
| UT-API-017 | test_api_large_file | Большой файл | Средний |
| UT-API-018 | test_api_binary_file | Бинарный файл | Средний |
| UT-API-019 | test_api_unicode_filename | Unicode имя файла | Средний |
| UT-API-020 | test_job_queue_startup | Запуск очереди задач | Высокий |
| UT-API-021 | test_job_queue_health | Health очереди | Высокий |
| UT-API-022 | test_parse_job_with_mocked_result | Задача с мокнутым результатом | Высокий |
| UT-API-023 | test_parse_job_with_mocked_error | Задача с мокнутой ошибкой | Высокий |

---

#### 4.5.2 Jobs (test_jobs.py)

**Файл:** `tests/unit/api/test_jobs.py`

| ID Теста | Название | Описание | Приоритет |
|----------|----------|----------|-----------|
| UT-API-024 | test_job_record_creation | Создание JobRecord | Высокий |
| UT-API-025 | test_job_record_with_webhook | JobRecord с webhook | Высокий |
| UT-API-026 | test_job_record_to_dict | JobRecord в dict | Высокий |
| UT-API-027 | test_job_record_to_dict_datetime_format | Формат datetime в dict | Высокий |
| UT-API-028 | test_job_record_to_dict_excludes_temp_path | Исключение temp_path | Средний |
| UT-API-029 | test_job_record_to_dict_excludes_result_when_none | Исключение None result | Средний |
| UT-API-030 | test_queue_start | Запуск очереди | Высокий |
| UT-API-031 | test_queue_stop | Остановка очереди | Высокий |
| UT-API-032 | test_enqueue_job | Добавление задачи | Высокий |
| UT-API-033 | test_get_job | Получение задачи | Высокий |
| UT-API-034 | test_get_job_not_found | Задача не найдена | Высокий |
| UT-API-035 | test_worker_processes_job | Обработка задачи worker | Высокий |
| UT-API-036 | test_worker_handles_errors | Обработка ошибок worker | Высокий |
| UT-API-037 | test_worker_cleans_temp_file | Очистка temp файла | Высокий |
| UT-API-038 | test_webhook_sent_on_completion | Webhook при завершении | Высокий |
| UT-API-039 | test_webhook_not_sent_without_url | Нет webhook без URL | Высокий |
| UT-API-040 | test_webhook_sent_on_failure | Webhook при ошибке | Высокий |
| UT-API-041 | test_multiple_jobs_queued | Множественные задачи в очереди | Средний |
| UT-API-042 | test_queue_restart | Перезапуск очереди | Средний |
| UT-API-043 | test_get_job_during_processing | Получение во время обработки | Средний |

---

#### 4.5.3 Service (test_service.py)

**Файл:** `tests/unit/api/test_service.py`

| ID Теста | Название | Описание | Приоритет |
|----------|----------|----------|-----------|
| UT-API-044 | test_parse_file_sync_html | Парсинг HTML файла | Высокий |
| UT-API-045 | test_parse_file_sync_pdf | Парсинг PDF файла | Высокий |
| UT-API-046 | test_parse_file_sync_docx | Парсинг DOCX файла | Высокий |
| UT-API-047 | test_parse_file_sync_returns_dict | Возврат dict | Высокий |
| UT-API-048 | test_parse_file_sync_has_required_fields | Обязательные поля | Высокий |
| UT-API-049 | test_parse_file_sync_missing_file | Отсутствующий файл | Высокий |
| UT-API-050 | test_parse_file_sync_unsupported_format | Неподдерживаемый формат | Высокий |
| UT-API-051 | test_save_upload_to_temp_creates_file | Создание temp файла | Высокий |
| UT-API-052 | test_save_upload_to_temp_correct_suffix | Верный суффикс | Высокий |
| UT-API-053 | test_save_upload_to_temp_default_suffix | Суффикс по умолчанию | Средний |
| UT-API-054 | test_save_upload_to_temp_in_correct_dir | Верная директория | Высокий |
| UT-API-055 | test_save_upload_to_temp_unique_names | Уникальные имена | Высокий |
| UT-API-056 | test_save_upload_to_temp_preserves_content | Сохранение контента | Высокий |
| UT-API-057 | test_save_upload_to_temp_large_file | Большой файл | Средний |
| UT-API-058 | test_save_upload_to_temp_empty_content | Пустой контент | Низкий |
| UT-API-059 | test_save_upload_to_temp_unicode_content | Unicode контент | Средний |
| UT-API-060 | test_save_upload_to_temp_cleanup | Очистка | Средний |
| UT-API-061 | test_save_upload_to_temp_special_characters_in_suffix | Спецсимволы в суффиксе | Низкий |
| UT-API-062 | test_save_upload_to_temp_no_leading_dot | Без ведущей точки | Низкий |
| UT-API-063 | test_save_upload_to_temp_concurrent_calls | Параллельные вызовы | Средний |
| UT-API-064 | test_save_upload_to_temp_directory_permissions | Права директории | Низкий |

---

### 4.6 Integration Tests (Интеграционные тесты)

**Файл:** `tests/integration/test_full_pipeline.py`

| ID Теста | Название | Описание | Приоритет |
|----------|----------|----------|-----------|
| IT-001 | test_html_full_pipeline | Полный пайплайн HTML | Высокий |
| IT-002 | test_pdf_full_pipeline | Полный пайплайн PDF | Высокий |
| IT-003 | test_docx_full_pipeline | Полный пайплайн DOCX | Высокий |
| IT-004 | test_factory_auto_registration | Авто-регистрация фабрики | Высокий |
| IT-005 | test_factory_parser_selection | Выбор парсера фабрикой | Высокий |
| IT-006 | test_api_full_workflow | Полный рабочий процесс API | Высокий |
| IT-007 | test_api_multiple_sequential_jobs | Множественные последовательные задачи | Средний |
| IT-008 | test_api_job_with_webhook_callback | Задача с webhook callback | Высокий |
| IT-009 | test_quality_metrics_consistency | Консистентность метрик качества | Высокий |
| IT-010 | test_quality_metrics_range | Диапазон метрик качества | Высокий |
| IT-011 | test_semantic_summary_accuracy | Точность semantic summary | Высокий |
| IT-012 | test_corrupted_file_error_propagation | Propagation ошибки повреждённого файла | Высокий |
| IT-013 | test_missing_file_error_propagation | Propagation ошибки отсутствующего файла | Высокий |
| IT-014 | test_unsupported_format_error_propagation | Propagation ошибки неподдерживаемого формата | Высокий |
| IT-015 | test_concurrent_parsing | Параллельный парсинг | Средний |
| IT-016 | test_concurrent_job_queue | Параллельная очередь задач | Средний |
| IT-017 | test_parser_registration_persistence | Персистентность регистрации парсеров | Высокий |
| IT-018 | test_parser_creation_repeatability | Повторяемость создания парсеров | Высокий |

---

## 5. Критерии Приёмки

### 5.1 Покрытие Кода

| Метрика    | Целевое Значение |
| ------------| ------------------|
| Statements | ≥85%             |
| Branches   | ≥80%             |
| Functions  | ≥90%             |
| Lines      | ≥85%             |

### 5.2 Прохождение Тестов

- 100% критических тестов (High Priority) должны проходить
- ≥95% всех тестов должны проходить
- 0 блокирующих ошибок

### 5.3 Качество Кода

- Type hints присутствуют во всём коде
- Docstrings для всех публичных API
- Кастомная иерархия исключений
- Логирование на уровне INFO+ для production

---

## 6. Ресурсы и Окружение

### 6.1 Тестовое Окружение

```bash
# Локальное выполнение
uv run pytest tests/ -v

# С покрытием
uv run pytest tests/ --cov=parser_manager --cov-report=html --junitxml=junit.xml

# Docker выполнение
docker compose --profile test run --rm tests
```

### 6.2 Тестовые Фикстуры

**Файл:** `tests/conftest.py`

| Фикстура                | Описание                 | Область  |
| -------------------------| --------------------------| ----------|
| `temp_dir`              | Временная директория     | function |
| `temp_file`             | Фабрика временных файлов | function |
| `sample_html_content`   | Пример HTML контента     | function |
| `sample_html_file`      | Пример HTML файла        | function |
| `sample_pdf_file`       | Пример PDF файла         | function |
| `sample_docx_file`      | Пример DOCX файла        | function |
| `sample_doc_file`       | Повреждённый DOC файл    | function |
| `sample_djvu_file`      | Фейковый DJVU файл       | function |
| `sample_metadata`       | Пример DocumentMetadata  | function |
| `sample_text_elements`  | Пример TextElements      | function |
| `sample_parsed_content` | Пример ParsedContent     | function |
| `api_client`            | TestClient для FastAPI   | function |
| `clean_parser_registry` | Очистка реестра парсеров | function |
