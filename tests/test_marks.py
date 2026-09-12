from pytrm.utils import marks


def test_is_set_returns_true_for_value() -> None:
    assert marks.is_set("value") is True


def test_is_set_returns_false_for_not_set() -> None:
    assert marks.is_set(marks.NOT_SET) is False


def test_is_set_returns_true_for_none() -> None:
    # None — обычное значение, а не отсутствие значения
    assert marks.is_set(None) is True


def test_value_or_returns_value_when_set() -> None:
    assert marks.value_or("value", "fallback") == "value"


def test_value_or_returns_fallback_when_not_set() -> None:
    assert marks.value_or(marks.NOT_SET, "fallback") == "fallback"


def test_not_set_is_instance_of_not_set() -> None:
    assert isinstance(marks.NOT_SET, marks.NotSet)


def test_not_set_has_no_dict() -> None:
    assert not hasattr(marks.NOT_SET, "__dict__")
