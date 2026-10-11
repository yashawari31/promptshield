
import base64
import binascii
import codecs
import re
import unicodedata


ZERO_WIDTH_RE = re.compile(r"[\u200b-\u200f\u2060\ufeff]")
SPACED_LETTERS_RE = re.compile(
    r"(?<!\w)(?:[a-zA-Z]\s+){3,}[a-zA-Z](?!\w)"
)


def _clean_unicode(text: str) -> str:
    """Normalize Unicode and remove zero-width formatting characters."""
    text = unicodedata.normalize("NFKC", text)
    return ZERO_WIDTH_RE.sub("", text)


def _collapse_spaced_letters(text: str) -> str:
    """
    Convert strings such as 'i g n o r e' to 'ignore'.
    Avoid collapsing ordinary multi-word sentences.
    """
    def replace(match):
        return re.sub(r"\s+", "", match.group(0))

    return SPACED_LETTERS_RE.sub(replace, text)


def _printable(text: str) -> bool:
    """Accept decoded content only if it is mostly readable text."""
    if not text:
        return False

    printable_count = sum(
        char.isprintable() or char in "\r\n\t"
        for char in text
    )
    return printable_count / len(text) >= 0.90


def _decode_base64_candidates(text: str) -> list[str]:
    """Decode long Base64-looking tokens when the result is readable."""
    decoded = []

    pattern = r"(?<![A-Za-z0-9+/=_-])[A-Za-z0-9+/]{16,}={0,2}(?![A-Za-z0-9+/=])"

    for match in re.finditer(pattern, text):
        token = match.group(0)

        try:
            padded = token + "=" * (-len(token) % 4)
            raw = base64.b64decode(padded, validate=True)
            candidate = raw.decode("utf-8")

            if _printable(candidate):
                decoded.append(candidate)

        except (binascii.Error, UnicodeDecodeError, ValueError):
            continue

    return decoded


def _decode_hex_candidates(text: str) -> list[str]:
    """Decode long hexadecimal strings when the result is readable."""
    decoded = []

    for match in re.finditer(r"(?<![0-9a-fA-F])(?:[0-9a-fA-F]{2}){8,}(?![0-9a-fA-F])", text):
        try:
            raw = bytes.fromhex(match.group(0))
            candidate = raw.decode("utf-8")

            if _printable(candidate):
                decoded.append(candidate)

        except (ValueError, UnicodeDecodeError):
            continue

    return decoded


def normalize(text: str) -> dict:
    """
    Return normalized text views and flags describing transformations.

    Views include original text, normalized text, and readable decoded
    candidates. The caller should inspect every view for attack signals.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    flags = []
    views = [text]

    cleaned = _clean_unicode(text)

    if cleaned != text:
        flags.append("unicode_normalized")

    spaced = _collapse_spaced_letters(cleaned)

    if spaced != cleaned:
        flags.append("spaced_letters_collapsed")

    canonical = spaced.lower()
    canonical = re.sub(r"\s+", " ", canonical).strip()

    if canonical != text:
        flags.append("canonicalized")

    views.append(canonical)

    # ROT13 is a reversible text transformation, not encryption.
    rot13_view = codecs.decode(canonical, "rot_13")
    if rot13_view != canonical:
        views.append(rot13_view)
        flags.append("rot13_view_generated")

    for candidate in _decode_base64_candidates(cleaned):
        views.append(candidate.lower())
        flags.append("base64_decoded")

    for candidate in _decode_hex_candidates(cleaned):
        views.append(candidate.lower())
        flags.append("hex_decoded")

    # Deduplicate views without changing their order.
    unique_views = list(dict.fromkeys(views))

    return {
        "views": unique_views,
        "flags": list(dict.fromkeys(flags)),
    }
