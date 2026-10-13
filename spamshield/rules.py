"""Transparent rule-based warning indicators.

These rules SUPPLEMENT the trained ML model — they never replace it.
A triggered rule means "this pattern is often seen in suspicious messages",
NOT "this message is definitely a scam". The app displays them separately
from the model prediction, with that caveat.

Each rule returns a short human-readable indicator string.
"""

from __future__ import annotations

import re

URL_RE = re.compile(r"(https?://\S+|www\.\S+|\S+\.(?:com|net|org|io|ph|xyz|top|click|link|info)\b\S*)", re.IGNORECASE)
SHORT_URL_RE = re.compile(r"\b(?:bit\.ly|tinyurl|t\.co|goo\.gl|ow\.ly|is\.gd|cutt\.ly)/\S+", re.IGNORECASE)
OTP_RE = re.compile(r"\b(?:otp|one[\s-]?time\s+(?:pin|password)|verification\s+code|verify.*code|code\s*(?:is|:))\b", re.IGNORECASE)
PASSWORD_RE = re.compile(r"\bpassw(?:ord|hrase)|pin(?:\s*(?:code|number))?|account\s+(?:number|details)|bank\s+details|credit\s+card|cvv|cvc\b", re.IGNORECASE)
MONEY_RE = re.compile(
    r"\b(?:send|transfer|wire|pay|deposit|remit|gcash|paymaya|load|top[\s-]?up)\b.{0,40}\b(?:money|cash|php|peso|₱|\d[\d,]*\s*(?:php|pesos?)?)\b"
    r"|₱\s*\d|\bphp\s*\d|\b\d[\d,]*\s*pesos?\b",
    re.IGNORECASE,
)
URGENCY_RE = re.compile(
    r"\b(?:urgent|immediately|right\s+now|act\s+now|limited\s+time|expires?\s+(?:today|soon)|last\s+chance|final\s+(?:notice|warning)|account\s+(?:suspended|locked|blocked|closed|frozen)|verify\s+immediately)\b",
    re.IGNORECASE,
)
PRIZE_RE = re.compile(
    r"\b(?:congratulations|you(?:'ve|\s+have)\s+(?:won|been\s+selected)|claim\s+(?:your|this|now)|free\s+(?:prize|gift|reward|load|cash)|lottery|raffle|sweepstakes|winner)\b",
    re.IGNORECASE,
)
IMPERSONATION_RE = re.compile(
    r"\b(?:this\s+is\s+(?:your\s+)?(?:bank|bsp|gcash|paymaya|dti|nbi|police|pnp|cidg|court|sheriff|bir|sss|pag-?ibig|philhealth|comelec|support\s+team|admin|manager|boss|ceo)|dear\s+(?:valued\s+)?customer|from\s+(?:the\s+)?(?:head\s+office|management|central\s+bank))\b",
    re.IGNORECASE,
)
THREAT_RE = re.compile(
    r"\b(?:arrest(?:ed)?|warrant|lawsuit|legal\s+action|police|jail|prison|penalty|fine|blacklist|suspend|suspended|deactivat|terminat|cancelled|forfeit|lose\s+access)\b",
    re.IGNORECASE,
)
CONTACT_RE = re.compile(
    r"\b(?:call|text|reply|contact|message|whatsapp|viber|telegram)\b.{0,30}(?:\b\d[\d\s\-()]{6,}\b|@\S+)",
    re.IGNORECASE,
)


def detect_indicators(text: str) -> list[str]:
    """Return a list of triggered warning indicator labels for *text*.

    Pure function of the input string; independent of any trained model.
    Empty/whitespace input yields no indicators.
    """
    if not isinstance(text, str) or not text.strip():
        return []
    indicators: list[str] = []
    if URL_RE.search(text):
        if SHORT_URL_RE.search(text):
            indicators.append("shortened_url: contains a shortened link (often hides the real destination)")
        else:
            indicators.append("suspicious_url: contains a link — verify the sender before tapping")
    if URGENCY_RE.search(text):
        indicators.append("urgency_pressure: creates urgency or threats to rush you")
    if MONEY_RE.search(text):
        indicators.append("money_request: asks to send money, load, or top-up")
    if PASSWORD_RE.search(text) or OTP_RE.search(text):
        indicators.append("sensitive_info_request: asks for passwords, OTPs, or account details")
    if PRIZE_RE.search(text):
        indicators.append("prize_claim: unexpected prize / winnings claim — a common lure")
    if IMPERSONATION_RE.search(text):
        indicators.append("possible_impersonation: claims to be an authority, bank, or support team")
    if THREAT_RE.search(text) and "urgency_pressure: creates urgency or threats to rush you" not in indicators:
        indicators.append("threat_language: threatens arrest, fines, or account closure")
    if CONTACT_RE.search(text):
        indicators.append("off_channel_contact: pushes you to call, text, or chat elsewhere")
    return indicators


def advisory_level(prediction: str, n_indicators: int, confidence: float | None) -> tuple[str, str]:
    """Heuristic advisory level (NOT a calibrated fraud probability).

    Levels: low / caution / elevated. Combines the model prediction with the
    count of rule-based indicators. Documented as a heuristic in the UI.
    """
    pred = (prediction or "").lower()
    if pred == "scam" or (pred == "spam" and n_indicators >= 2):
        return "elevated", "Several warning signs point to a likely unwanted or deceptive message. Do not reply, tap links, or share personal details."
    if pred == "spam" or n_indicators >= 1 or (confidence is not None and confidence < 0.6):
        return "caution", "Some warning signs present. Pause and verify the sender through an official channel before acting."
    return "low", "No strong warning signs detected, but stay alert — this tool cannot guarantee a message is safe."
