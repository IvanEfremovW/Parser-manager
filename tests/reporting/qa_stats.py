"""
Модуль сбора QA статистики.

Этот модуль собирает и предоставляет статистику тестирования включая:
- Общее количество тестов
- Количество пройденных/проваленных/пропущенных
- Покрытие по модулям
- Время выполнения тестов
- Отслеживание багов/проблем
"""

import json
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class TestStatistics:
    """Контейнер для статистики тестов."""

    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    execution_time: float = 0.0
    coverage_percent: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # Покрытие по модулям
    module_coverage: dict = field(default_factory=dict)

    # Детали тестов по категориям
    by_category: dict = field(default_factory=dict)

    # Найденные проблемы/баги
    issues: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Конвертировать в словарь."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Конвертировать в JSON строку."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @property
    def pass_rate(self) -> float:
        """Рассчитать процент прохождения."""
        if self.total_tests == 0:
            return 0.0
        return (self.passed / self.total_tests) * 100

    @property
    def failure_rate(self) -> float:
        """Рассчитать процент провалов."""
        if self.total_tests == 0:
            return 0.0
        return ((self.failed + self.errors) / self.total_tests) * 100


class QAStatsCollector:
    """Собирает и управляет QA статистикой из запусков тестов."""

    def __init__(self, output_dir: str | None = None):
        """Инициализировать коллектор.

        Args:
            output_dir: Директория для выходных файлов. По умолчанию tests/reporting/output.
        """
        self.stats = TestStatistics()
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def parse_junit_xml(self, xml_path: str) -> TestStatistics:
        """Разобрать JUnit XML отчёт и извлечь статистику.

        Args:
            xml_path: Путь к JUnit XML файлу.

        Returns:
            TestStatistics объект.
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Получить атрибуты testsuite
        testsuite = root.find("testsuite")
        if testsuite is None:
            testsuite = root

        self.stats.total_tests = int(testsuite.get("tests", 0))
        self.stats.failures = int(testsuite.get("failures", 0))
        self.stats.skipped = int(testsuite.get("skipped", 0))
        self.stats.errors = int(testsuite.get("errors", 0))
        self.stats.execution_time = float(testsuite.get("time", 0))

        # Подсчитать пройденные тесты
        self.stats.passed = (
            self.stats.total_tests - self.stats.failures - self.stats.skipped - self.stats.errors
        )

        # Разобрать отдельные тест-кейсы для категоризации
        self._parse_test_cases(testsuite)

        return self.stats

    def _parse_test_cases(self, testsuite: ET.Element) -> None:
        """Разобрать отдельные тест-кейсы для категоризации.

        Категории взаимоисключающие - каждый тест считается только один раз.
        Приоритет категоризации: integration > api > parser > core > models > utils > unit
        """
        categories = {
            "unit": 0,
            "integration": 0,
            "api": 0,
            "parser": 0,
            "core": 0,
            "models": 0,
            "utils": 0,
        }

        for testcase in testsuite.findall("testcase"):
            classname = testcase.get("classname", "")
            name = testcase.get("name", "")
            categorized = False

            # Категоризировать по модулю (взаимоисключающе)
            # Приоритет: integration > api > parser > core > models > utils

            if "integration" in classname:
                categories["integration"] += 1
                categorized = True
            elif "api" in classname:
                # API тесты — это юнит-тесты API модуля, считаем их отдельно
                categories["api"] += 1
                categorized = True
            elif (
                "parser" in classname
                or "html_parser" in classname
                or "pdf_parser" in classname
                or "docx_parser" in classname
                or "doc_parser" in classname
                or "djvu_parser" in classname
            ):
                categories["parser"] += 1
                categorized = True
            elif "core" in classname:
                categories["core"] += 1
                categorized = True
            elif (
                "models" in classname or "parsed_content" in classname or "exceptions" in classname
            ):
                categories["models"] += 1
                categorized = True
            elif (
                "utils" in classname
                or "quality" in classname
                or "semantic" in classname
                or "file_metrics" in classname
            ):
                categories["utils"] += 1
                categorized = True

            # Если не попало в другие категории, но содержит unit — считаем как unit
            if not categorized and "unit" in classname:
                categories["unit"] += 1

            # Проверить на провалы и собрать проблемы
            failure = testcase.find("failure")
            error = testcase.find("error")

            if failure is not None:
                self.stats.issues.append(
                    {
                        "type": "failure",
                        "test": f"{classname}.{name}",
                        "message": failure.get("message", "")[:200],
                    }
                )
            elif error is not None:
                self.stats.issues.append(
                    {
                        "type": "error",
                        "test": f"{classname}.{name}",
                        "message": error.get("message", "")[:200],
                    }
                )

        self.stats.by_category = categories

    def parse_coverage_xml(self, xml_path: str) -> None:
        """Разобрать coverage.xml и извлечь покрытие по модулям.

        Args:
            xml_path: Путь к coverage.xml файлу.
        """
        tree = ET.parse(xml_path)
        root = tree.getroot()

        packages = {}

        for package in root.findall(".//package"):
            package_name = package.get("name", "unknown")
            coverage = package.get("line-rate", "0")

            # Упростить имя пакета
            simple_name = package_name.split(".")[-1] if "." in package_name else package_name

            packages[simple_name] = {
                "line_coverage": float(coverage) * 100,
                "branch_coverage": float(package.get("branch-rate", "0")) * 100,
            }

        self.stats.module_coverage = packages

        # Рассчитать общее покрытие
        if packages:
            total_coverage = sum(p["line_coverage"] for p in packages.values())
            self.stats.coverage_percent = total_coverage / len(packages)

    def collect_from_pytest(self, pytest_args: str = "") -> TestStatistics:
        """Запустить pytest и собрать статистику.

        Args:
            pytest_args: Дополнительные аргументы pytest.

        Returns:
            TestStatistics объект.
        """
        import subprocess

        # Запустить pytest с XML выводом
        junit_path = self.output_dir / "junit.xml"
        coverage_path = self.output_dir / "coverage.xml"

        cmd = (
            f"python -m pytest "
            f"--junit-xml={junit_path} "
            f"--cov=parser_manager "
            f"--cov-report=xml:{coverage_path} "
            f"{pytest_args}"
        )

        subprocess.run(cmd, shell=True, capture_output=True, text=True)

        # Разобрать выводы
        if junit_path.exists():
            self.parse_junit_xml(str(junit_path))

        if coverage_path.exists():
            self.parse_coverage_xml(str(coverage_path))

        return self.stats

    def save_statistics(self, filename: str = "qa_statistics.json") -> Path:
        """Сохранить статистику в JSON файл.

        Args:
            filename: Имя выходного файла.

        Returns:
            Путь к сохранённому файлу.
        """
        output_path = self.output_dir / filename
        output_path.write_text(self.stats.to_json(), encoding="utf-8")
        return output_path

    def generate_summary(self) -> str:
        """Сгенерировать читаемое резюме.

        Returns:
            Строка резюме.
        """
        lines = [
            "=" * 60,
            "РЕЗЮМЕ СТАТИСТИКИ QA ТЕСТИРОВАНИЯ",
            "=" * 60,
            f"Временная метка: {self.stats.timestamp}",
            "",
            "КОЛИЧЕСТВО ТЕСТОВ:",
            f"  Всего:     {self.stats.total_tests}",
            f"  Пройдено:  {self.stats.passed}",
            f"  Провалено: {self.stats.failed}",
            f"  Пропущено: {self.stats.skipped}",
            f"  Ошибки:    {self.stats.errors}",
            "",
            "МЕТРИКИ:",
            f"  Процент прохождения: {self.stats.pass_rate:.1f}%",
            f"  Процент провалов:    {self.stats.failure_rate:.1f}%",
            f"  Покрытие кода:       {self.stats.coverage_percent:.1f}%",
            f"  Время выполнения:    {self.stats.execution_time:.2f}s",
            "",
        ]

        if self.stats.by_category:
            lines.append("ПО КАТЕГОРИЯМ:")
            for category, count in self.stats.by_category.items():
                if count > 0:
                    lines.append(f"  {category}: {count}")
            lines.append("")

        if self.stats.module_coverage:
            lines.append("ПОКРЫТИЕ ПО МОДУЛЯМ:")
            for module, coverage in sorted(self.stats.module_coverage.items()):
                cov = coverage.get("line_coverage", 0)
                lines.append(f"  {module}: {cov:.1f}%")
            lines.append("")

        if self.stats.issues:
            lines.append(f"НАЙДЕНЫ ПРОБЛЕМЫ: {len(self.stats.issues)}")
            for issue in self.stats.issues[:10]:  # Показать первые 10
                lines.append(f"  [{issue['type']}] {issue['test']}")
                lines.append(f"    → {issue['message']}")
            if len(self.stats.issues) > 10:
                lines.append(f"  ... и ещё {len(self.stats.issues) - 10}")

        lines.append("=" * 60)

        return "\n".join(lines)


def collect_stats_from_files(
    junit_xml: str | None = None,
    coverage_xml: str | None = None,
) -> TestStatistics:
    """Собрать статистику из существующих XML файлов.

    Args:
        junit_xml: Путь к JUnit XML файлу.
        coverage_xml: Путь к coverage XML файлу.

    Returns:
        TestStatistics объект.
    """
    collector = QAStatsCollector()

    if junit_xml:
        collector.parse_junit_xml(junit_xml)

    if coverage_xml:
        collector.parse_coverage_xml(coverage_xml)

    return collector.stats


def main():
    """Точка входа для сбора статистики."""
    import argparse

    parser = argparse.ArgumentParser(description="Собрать QA статистику")
    parser.add_argument(
        "--junit",
        type=str,
        help="Путь к JUnit XML файлу",
    )
    parser.add_argument(
        "--coverage",
        type=str,
        help="Путь к coverage XML файлу",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="qa_statistics.json",
        help="Выходной JSON файл",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Вывести резюме в консоль",
    )

    args = parser.parse_args()

    collector = QAStatsCollector()

    if args.junit:
        collector.parse_junit_xml(args.junit)

    if args.coverage:
        collector.parse_coverage_xml(args.coverage)

    # Сохранить статистику
    output_path = collector.save_statistics(args.output)
    print(f"Статистика сохранена в: {output_path}")

    if args.summary:
        print(collector.generate_summary())


if __name__ == "__main__":
    main()
