
import math

import pytest

from app.classifier import score


def test_score_returns_probability():
    result = score("Explain how to make a cup of tea.")

    assert isinstance(result, float)
    assert math.isfinite(result)
    assert 0.0 <= result <= 1.0


def test_empty_text_returns_zero():
    assert score("") == 0.0
    assert score("   ") == 0.0


def test_non_string_input_is_rejected():
    with pytest.raises(TypeError):
        score(None)
