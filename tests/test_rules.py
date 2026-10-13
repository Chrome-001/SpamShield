"""Tests for rule-based indicators (independent of the trained model)."""
from spamshield.rules import advisory_level, detect_indicators


def test_empty_input_has_no_indicators():
    assert detect_indicators("") == []
    assert detect_indicators("   ") == []


def test_suspicious_url_detected():
    inds = detect_indicators("Verify now at http://bit.ly/xyz123 with your password")
    assert any("url" in i for i in inds)


def test_password_and_otp_request():
    assert any("sensitive" in i for i in detect_indicators("Send me your password and OTP now"))


def test_prize_claim():
    assert any("prize" in i for i in detect_indicators("Congratulations! You won a free prize, claim now"))


def test_money_request():
    assert any("money" in i for i in detect_indicators("Please send money via GCash now, urgent"))


def test_ordinary_message_has_no_indicators():
    assert detect_indicators("Hey, are we still meeting for lunch tomorrow?") == []


def test_advisory_level_is_heuristic_not_probability():
    level, msg = advisory_level("spam", 2, 0.9)
    assert level == "elevated"
    assert isinstance(msg, str)
    level2, _ = advisory_level("ham", 0, 0.95)
    assert level2 == "low"
