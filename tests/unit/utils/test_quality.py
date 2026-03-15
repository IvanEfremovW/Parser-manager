"""
Unit tests for quality scoring utilities.

Test Cases:
- TC-UTIL-002: Quality Scoring
"""

import pytest

from parser_manager.utils.quality import score_quality, _safe_ratio


class TestSafeRatio:
    """Tests for _safe_ratio helper function."""

    def test_safe_ratio_basic(self):
        """Test basic ratio calculation."""
        assert _safe_ratio(50, 100) == 0.5
        assert _safe_ratio(25, 100) == 0.25
        assert _safe_ratio(100, 100) == 1.0

    def test_safe_ratio_zero_denominator(self):
        """Test that zero denominator returns 0."""
        assert _safe_ratio(50, 0) == 0.0

    def test_safe_ratio_negative_denominator(self):
        """Test that negative denominator returns 0."""
        assert _safe_ratio(50, -10) == 0.0

    def test_safe_ratio_clamps_to_1(self):
        """Test that ratio is clamped to maximum 1."""
        assert _safe_ratio(150, 100) == 1.0

    def test_safe_ratio_clamps_to_0(self):
        """Test that ratio is clamped to minimum 0."""
        assert _safe_ratio(-10, 100) == 0.0


class TestScoreQuality:
    """Tests for score_quality function."""

    def test_score_quality_basic(self):
        """Test TC-UTIL-002: Basic quality scoring."""
        text = "This is a test paragraph with sufficient content." * 10
        semantic_blocks = [
            {"element_type": "heading", "content": "Title"},
            {"element_type": "paragraph", "content": "Paragraph 1"},
            {"element_type": "paragraph", "content": "Paragraph 2"},
        ]

        result = score_quality(text, semantic_blocks)

        assert "overall_score" in result
        assert 0.0 <= result["overall_score"] <= 1.0
        assert "text_completeness" in result
        assert "structure_score" in result
        assert "noise_ratio" in result
        assert "broken_chars_ratio" in result
        assert "table_coverage" in result

    def test_score_quality_all_metrics_present(self):
        """Test that all expected metrics are returned."""
        text = "Test content" * 20
        blocks = [{"element_type": "paragraph", "content": "Test"}]

        result = score_quality(text, blocks)

        expected_keys = [
            "overall_score",
            "text_completeness",
            "structure_score",
            "noise_ratio",
            "broken_chars_ratio",
            "table_coverage",
            "char_count",
            "word_count",
            "block_count",
        ]

        for key in expected_keys:
            assert key in result

    def test_score_quality_empty_text(self):
        """Test scoring with empty text."""
        result = score_quality("", [])

        assert result["overall_score"] >= 0.0
        assert result["char_count"] == 0
        assert result["word_count"] == 0
        assert result["block_count"] == 0

    def test_score_quality_text_completeness_threshold(self):
        """Test text_completeness reaches 1.0 at 200 chars."""
        # Less than 200 characters
        short_text = "x" * 100
        result_short = score_quality(short_text, [])
        assert result_short["text_completeness"] < 1.0

        # Exactly 200 characters
        exact_text = "x" * 200
        result_exact = score_quality(exact_text, [])
        assert result_exact["text_completeness"] == 1.0

        # More than 200 characters
        long_text = "x" * 300
        result_long = score_quality(long_text, [])
        assert result_long["text_completeness"] == 1.0

    def test_score_quality_structure_score_threshold(self):
        """Test structure_score reaches 1.0 at 3+ blocks."""
        text = "Test content" * 20

        # Less than 3 blocks
        result_few = score_quality(text, [{"element_type": "paragraph"}] * 2)
        assert result_few["structure_score"] < 1.0

        # Exactly 3 blocks
        result_exact = score_quality(text, [{"element_type": "paragraph"}] * 3)
        assert result_exact["structure_score"] == 1.0

        # More than 3 blocks
        result_many = score_quality(text, [{"element_type": "paragraph"}] * 10)
        assert result_many["structure_score"] == 1.0

    def test_score_quality_noise_ratio_non_printable(self):
        """Test noise_ratio increases with non-printable characters."""
        clean_text = "Clean text. " * 20
        noisy_text = clean_text + "\x00\x01\x02" * 10

        result_clean = score_quality(clean_text, [])
        result_noisy = score_quality(noisy_text, [])

        assert result_noisy["noise_ratio"] > result_clean["noise_ratio"]

    def test_score_quality_broken_chars_ratio(self):
        """Test broken_chars_ratio with replacement characters."""
        clean_text = "Clean text. " * 20
        # Use actual replacement character 
        broken_text = clean_text + "\ufffd" * 10

        result_clean = score_quality(clean_text, [])
        result_broken = score_quality(broken_text, [])

        assert result_broken["broken_chars_ratio"] > result_clean["broken_chars_ratio"]
        # The broken text should have a non-zero broken ratio
        assert result_broken["broken_chars_ratio"] > 0.0 or result_clean["broken_chars_ratio"] == 0.0

    def test_score_quality_table_coverage(self):
        """Test table_coverage calculation."""
        text = "Test content" * 20

        # No tables
        result_no_table = score_quality(
            text,
            [{"element_type": "paragraph"} for _ in range(10)],
        )
        assert result_no_table["table_coverage"] == 0.0

        # Some tables
        blocks_with_tables = [
            {"element_type": "paragraph"},
            {"element_type": "table"},
            {"element_type": "table"},
        ]
        result_with_tables = score_quality(text, blocks_with_tables)
        assert result_with_tables["table_coverage"] > 0.0

    def test_score_quality_char_count(self):
        """Test that char_count matches text length."""
        text = "Test content" * 17  # 204 characters

        result = score_quality(text, [])

        assert result["char_count"] == len(text)

    def test_score_quality_word_count(self):
        """Test that word_count is calculated correctly."""
        text = "one two three four five"

        result = score_quality(text, [])

        assert result["word_count"] == 5

    def test_score_quality_word_count_unicode(self):
        """Test word count with unicode text."""
        text = "привет мир как дела"  # 4 words in Russian

        result = score_quality(text, [])

        assert result["word_count"] == 4

    def test_score_quality_block_count(self):
        """Test that block_count matches number of blocks."""
        text = "Test"
        blocks = [{"element_type": "paragraph"} for _ in range(5)]

        result = score_quality(text, blocks)

        assert result["block_count"] == 5

    def test_score_quality_overall_score_bounds(self):
        """Test that overall_score is always in [0, 1] range."""
        test_cases = [
            ("", []),
            ("x", []),
            ("x" * 1000, [{"element_type": "paragraph"}] * 100),
            ("\x00" * 100, []),
            ("test", [{"element_type": "table"}]),
        ]

        for text, blocks in test_cases:
            result = score_quality(text, blocks)
            assert 0.0 <= result["overall_score"] <= 1.0

    def test_score_quality_rounding(self):
        """Test that metrics are rounded to 4 decimal places."""
        text = "Test content" * 20
        blocks = [{"element_type": "paragraph"}]

        result = score_quality(text, blocks)

        # Check that values are rounded to 4 decimal places
        for key in ["overall_score", "text_completeness", "structure_score", "noise_ratio"]:
            value = result[key]
            # Multiply by 10000 and check if it's an integer
            assert round(value, 4) == value

    def test_score_quality_none_blocks(self):
        """Test handling of None blocks."""
        text = "Test content" * 20

        result = score_quality(text, None)

        assert result["block_count"] == 0
        assert result["table_coverage"] == 0.0

    def test_score_quality_weird_symbols(self):
        """Test noise detection with weird symbols."""
        clean_text = "Clean text. " * 20
        weird_text = clean_text + "□■▪•◊¤§¶" * 5

        result_clean = score_quality(clean_text, [])
        result_weird = score_quality(weird_text, [])

        assert result_weird["noise_ratio"] > result_clean["noise_ratio"]


class TestScoreQualityEdgeCases:
    """Edge case tests for quality scoring."""

    def test_score_quality_very_long_text(self):
        """Test with very long text."""
        text = "Test content. " * 10000
        blocks = [{"element_type": "paragraph"} for _ in range(100)]

        result = score_quality(text, blocks)

        assert result["overall_score"] >= 0.0
        assert result["char_count"] == len(text)

    def test_score_quality_single_character(self):
        """Test with single character text."""
        result = score_quality("x", [])

        assert result["char_count"] == 1
        assert result["word_count"] == 1

    def test_score_quality_only_whitespace(self):
        """Test with whitespace-only text."""
        result = score_quality("   \n\t   ", [])

        assert result["char_count"] > 0
        assert result["word_count"] == 0

    def test_score_quality_mixed_block_types(self):
        """Test with mixed block types."""
        text = "Test" * 50
        blocks = [
            {"element_type": "heading"},
            {"element_type": "paragraph"},
            {"element_type": "table"},
            {"element_type": "list"},
            {"element_type": "link"},
            {"element_type": "invalid_type"},  # Should be counted but not as table
        ]

        result = score_quality(text, blocks)

        assert result["block_count"] == 6
