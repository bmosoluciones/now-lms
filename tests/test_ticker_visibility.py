"""
Test for stock ticker visibility in finance theme home page.
"""

import re
import os


def test_stock_ticker_visibility():
    """Test that the stock ticker has sufficient contrast for visibility."""
    # Path to the finance theme home template
    template_path = os.path.join(os.path.dirname(__file__), "../now_lms/templates/themes/finance/overrides/home.j2")

    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find the static ticker background bar
    ticker_pattern = r"<!-- Static ticker background bar -->(.*?)<!-- Scrolling ticker text -->"
    ticker_match = re.search(ticker_pattern, content, re.DOTALL)

    assert ticker_match, "Static ticker background bar not found"

    ticker_bg_content = ticker_match.group(1)

    # Check that background has proper green color
    assert "background: #006647" in ticker_bg_content, "Ticker background should be green (#006647)"

    # Find the scrolling ticker text
    text_pattern = r"<!-- Scrolling ticker text -->(.*?)</div>"
    text_match = re.search(text_pattern, content, re.DOTALL)

    assert text_match, "Scrolling ticker text element not found"

    ticker_text_content = text_match.group(1)

    # Check for white color text (high contrast against green background)
    assert "color: #ffffff" in ticker_text_content, "Text color should be white (#ffffff) for high contrast"

    # Check that font-weight is bold
    assert "font-weight: bold" in ticker_text_content, "Font should be bold for better visibility"

    # Check that the ticker uses real LMS data
    assert "lms_info.courses_count" in ticker_text_content, "Ticker should display real course count"
    assert "lms_info.students_count" in ticker_text_content, "Ticker should display real student count"
    assert "lms_info.teachers_count" in ticker_text_content, "Ticker should display real teacher count"
    assert "lms_info.moderators_count" in ticker_text_content, "Ticker should display real moderator count"

    # Check for enhanced LMS data
    assert "lms_info.enrollments_count" in ticker_text_content, "Ticker should display enrollment count"
    assert "lms_info.certificates_count" in ticker_text_content, "Ticker should display certificate count"
    assert "lms_info.programs_count" in ticker_text_content, "Ticker should display program count"

    # Check that emojis are present for visual appeal
    assert "📚" in ticker_text_content, "Ticker should contain books emoji"
    assert "👥" in ticker_text_content, "Ticker should contain people emoji"
    assert "👨‍🏫" in ticker_text_content, "Ticker should contain teacher emoji"

    # Check that the ticker has proper animation
    assert "constrained-scroll" in ticker_text_content, "Ticker should use constrained-scroll animation"


if __name__ == "__main__":
    test_stock_ticker_visibility()
    print("✅ Stock ticker visibility test passed!")
