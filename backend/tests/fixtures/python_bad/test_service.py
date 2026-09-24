from service import collect


def test_collect():
    assert collect("first") == ["first"]
