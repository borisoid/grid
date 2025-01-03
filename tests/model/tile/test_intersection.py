from grid.model import Tile, TileAsCorners, Cell


def test_1() -> None:
    vertical = Tile.build(TileAsCorners(c1=Cell(x=0, y=0), c4=Cell(x=0, y=20)))
    horizontal = Tile.build(TileAsCorners(c1=Cell(x=-10, y=10), c4=Cell(x=10, y=10)))

    assert vertical.intersection(horizontal) == Tile.build(
        TileAsCorners(c1=Cell(0, 10), c4=Cell(0, 10))
    )


def test_2() -> None:
    t1 = Tile.build(TileAsCorners(c1=Cell(x=0, y=11), c4=Cell(x=10, y=20)))
    t2 = Tile.build(TileAsCorners(c1=Cell(x=-10, y=10), c4=Cell(x=-1, y=20)))

    intersection = t1.intersection(t2)
    assert intersection is None
