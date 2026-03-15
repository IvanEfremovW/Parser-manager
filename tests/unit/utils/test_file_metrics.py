"""
Unit tests for file metrics utilities.
"""

import pytest
from pathlib import Path

from parser_manager.utils.file_metrics import collect_file_metrics


class TestCollectFileMetrics:
    """Tests for collect_file_metrics function."""

    def test_collect_file_metrics_basic(self, temp_dir: Path):
        """Test basic file metrics collection."""
        file_path = temp_dir / "test.html"
        file_path.write_text("Test content", encoding="utf-8")

        semantic_blocks = [
            {"content": "Block 1", "element_type": "paragraph"},
            {"content": "Block 2", "element_type": "heading"},
        ]
        text = "Test content"

        result = collect_file_metrics(str(file_path), semantic_blocks, text)

        assert result["file_name"] == "test.html"
        assert result["extension"] == ".html"
        assert result["file_size_bytes"] > 0
        assert result["text_length"] == len(text)
        assert result["semantic_blocks"] == 2

    def test_collect_file_metrics_all_fields(self, temp_dir: Path):
        """Test that all expected fields are present."""
        file_path = temp_dir / "test.pdf"
        file_path.write_text("Test", encoding="utf-8")

        result = collect_file_metrics(str(file_path), [], "")

        expected_fields = [
            "file_name",
            "extension",
            "file_size_bytes",
            "text_length",
            "semantic_blocks",
            "avg_block_length",
            "max_block_length",
        ]

        for field in expected_fields:
            assert field in result

    def test_collect_file_metrics_extension_lowercase(self, temp_dir: Path):
        """Test that extension is lowercase."""
        file_path = temp_dir / "test.HTML"
        file_path.write_text("Test", encoding="utf-8")

        result = collect_file_metrics(str(file_path), [], "")

        assert result["extension"] == ".html"

    def test_collect_file_metrics_avg_block_length(self, temp_dir: Path):
        """Test average block length calculation."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("Test", encoding="utf-8")

        blocks = [
            {"content": "12345", "element_type": "paragraph"},  # 5 chars
            {"content": "1234567890", "element_type": "paragraph"},  # 10 chars
        ]

        result = collect_file_metrics(str(file_path), blocks, "")

        assert result["avg_block_length"] == 7.5

    def test_collect_file_metrics_avg_block_length_empty(self, temp_dir: Path):
        """Test average block length with no blocks."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("Test", encoding="utf-8")

        result = collect_file_metrics(str(file_path), [], "")

        assert result["avg_block_length"] == 0

    def test_collect_file_metrics_max_block_length(self, temp_dir: Path):
        """Test max block length calculation."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("Test", encoding="utf-8")

        blocks = [
            {"content": "short", "element_type": "paragraph"},
            {"content": "much longer content", "element_type": "paragraph"},
            {"content": "medium", "element_type": "paragraph"},
        ]

        result = collect_file_metrics(str(file_path), blocks, "")

        assert result["max_block_length"] == 19

    def test_collect_file_metrics_max_block_length_empty(self, temp_dir: Path):
        """Test max block length with no blocks."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("Test", encoding="utf-8")

        result = collect_file_metrics(str(file_path), [], "")

        assert result["max_block_length"] == 0

    def test_collect_file_metrics_nonexistent_file(self):
        """Test metrics for non-existent file."""
        result = collect_file_metrics("/nonexistent/path/file.txt", [], "")

        assert result["file_name"] == "file.txt"
        assert result["extension"] == ".txt"
        assert result["file_size_bytes"] == 0

    def test_collect_file_metrics_strips_block_content(self, temp_dir: Path):
        """Test that block content is stripped for length calculation."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("Test", encoding="utf-8")

        blocks = [
            {"content": "  padded content  ", "element_type": "paragraph"},
        ]

        result = collect_file_metrics(str(file_path), blocks, "")

        # "padded content" = 14 chars (stripped)
        assert result["avg_block_length"] == 14.0

    def test_collect_file_metrics_empty_block_content(self, temp_dir: Path):
        """Test handling of empty block content."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("Test", encoding="utf-8")

        blocks = [
            {"content": "", "element_type": "paragraph"},
            {"content": "valid", "element_type": "paragraph"},
            {"content": None, "element_type": "paragraph"},
        ]

        result = collect_file_metrics(str(file_path), blocks, "")

        assert result["semantic_blocks"] == 3
        # avg: (0 + 5 + 0) / 3 = 1.67
        assert abs(result["avg_block_length"] - 1.67) < 0.01

    def test_collect_file_metrics_none_blocks(self, temp_dir: Path):
        """Test handling of None blocks."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("Test", encoding="utf-8")

        result = collect_file_metrics(str(file_path), None, "")

        assert result["semantic_blocks"] == 0
        assert result["avg_block_length"] == 0
        assert result["max_block_length"] == 0

    def test_collect_file_metrics_file_size_accuracy(self, temp_dir: Path):
        """Test that file size is accurate."""
        file_path = temp_dir / "test.txt"
        content = "x" * 1000
        file_path.write_text(content, encoding="utf-8")

        result = collect_file_metrics(str(file_path), [], "")

        assert result["file_size_bytes"] == 1000

    def test_collect_file_metrics_complex_path(self, temp_dir: Path):
        """Test with complex file path."""
        nested_dir = temp_dir / "level1" / "level2" / "level3"
        nested_dir.mkdir(parents=True)

        file_path = nested_dir / "complex-file_name.test.html"
        file_path.write_text("Test", encoding="utf-8")

        result = collect_file_metrics(str(file_path), [], "")

        assert result["file_name"] == "complex-file_name.test.html"
        assert result["extension"] == ".html"


class TestCollectFileMetricsEdgeCases:
    """Edge case tests for file metrics."""

    def test_collect_file_metrics_unicode_filename(self, temp_dir: Path):
        """Test with unicode characters in filename."""
        file_path = temp_dir / "тест_文件.html"
        file_path.write_text("Test", encoding="utf-8")

        result = collect_file_metrics(str(file_path), [], "")

        assert "тест_文件.html" in result["file_name"]

    def test_collect_file_metrics_spaces_in_path(self, temp_dir: Path):
        """Test with spaces in file path."""
        file_path = temp_dir / "file with spaces.html"
        file_path.write_text("Test", encoding="utf-8")

        result = collect_file_metrics(str(file_path), [], "")

        assert result["file_name"] == "file with spaces.html"

    def test_collect_file_metrics_no_extension(self, temp_dir: Path):
        """Test file without extension."""
        file_path = temp_dir / "README"
        file_path.write_text("Test", encoding="utf-8")

        result = collect_file_metrics(str(file_path), [], "")

        assert result["extension"] == ""

    def test_collect_file_metrics_multiple_dots(self, temp_dir: Path):
        """Test file with multiple dots in name."""
        file_path = temp_dir / "file.name.with.dots.tar.gz"
        file_path.write_text("Test", encoding="utf-8")

        result = collect_file_metrics(str(file_path), [], "")

        assert result["extension"] == ".gz"
        assert result["file_name"] == "file.name.with.dots.tar.gz"

    def test_collect_file_metrics_very_long_blocks(self, temp_dir: Path):
        """Test with very long block content."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("Test", encoding="utf-8")

        blocks = [
            {"content": "x" * 10000, "element_type": "paragraph"},
        ]

        result = collect_file_metrics(str(file_path), blocks, "")

        assert result["max_block_length"] == 10000
        assert result["avg_block_length"] == 10000.0

    def test_collect_file_metrics_many_blocks(self, temp_dir: Path):
        """Test with many blocks."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("Test", encoding="utf-8")

        blocks = [
            {"content": f"block_{i}", "element_type": "paragraph"}
            for i in range(1000)
        ]

        result = collect_file_metrics(str(file_path), blocks, "")

        assert result["semantic_blocks"] == 1000
