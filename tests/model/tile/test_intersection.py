from grid.model import Tile, TileAsCorners, Cell


def test_1() -> None:
    vertical = Tile.build(TileAsCorners(c0=Cell(x=0, y=0), c3=Cell(x=0, y=20)))
    horizontal = Tile.build(TileAsCorners(c0=Cell(x=-10, y=10), c3=Cell(x=10, y=10)))

    assert vertical.intersection(horizontal) == Tile.build(
        TileAsCorners(c0=Cell(0, 10), c3=Cell(0, 10))
    )


def test_2() -> None:
    t1 = Tile.build(TileAsCorners(c0=Cell(x=0, y=11), c3=Cell(x=10, y=20)))
    t2 = Tile.build(TileAsCorners(c0=Cell(x=-10, y=10), c3=Cell(x=-1, y=20)))

    intersection = t1.intersection(t2)
    assert intersection is None

def test_3() -> None:
    t1 = Tile.build(TileAsCorners(c0=Cell(x=0, y=0), c3=Cell(x=10, y=10)))
    t2 = Tile.build(TileAsCorners(c0=Cell(x=-10, y=5), c3=Cell(x=-1, y=9)))

    intersection = t1.intersection(t2)
    assert intersection is None
