import pytest

from whisperlite.metrics import cer, rtf
from whisperlite.textnorm import has_digits, normalize


def test_normalize_removes_punctuation_and_spaces():
    assert normalize("안녕하세요, 여러분!  반갑습니다.") == "안녕하세요여러분반갑습니다"


def test_normalize_unifies_width_and_case():
    assert normalize("ＡＢＣ abc") == "abcabc"


def test_spacing_and_punctuation_do_not_count_as_errors():
    assert cer(["오늘 날씨가 좋다"], ["오늘날씨가 좋다."]) == 0.0


def test_cer_counts_character_errors():
    assert cer(["가나다라"], ["가나다마"]) == pytest.approx(0.25)


def test_cer_skips_empty_references():
    assert cer(["", "가나"], ["무엇", "가나"]) == 0.0


def test_has_digits():
    assert has_digits("3시에 만나요")
    assert not has_digits("세 시에 만나요")


def test_rtf():
    assert rtf(5.0, 10.0) == 0.5
    with pytest.raises(ValueError):
        rtf(1.0, 0)
