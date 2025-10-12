from grid.model import mark_last


def test_1() -> None:
    assert tuple(mark_last((1, 2, 3, 4, 5))) == (
        (False, 1),
        (False, 2),
        (False, 3),
        (False, 4),
        (True, 5),
    )


def test_2() -> None:
    sentinel = object()

    value = next(mark_last(()), sentinel)

    assert value is sentinel
