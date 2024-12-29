from grid.model import Tile, TileAsCorners, Cell


def test_1() -> None:
    vertical = Tile.build(TileAsCorners(c1=Cell(x=0, y=0), c2=Cell(x=0, y=20)))
    horizontal = Tile.build(TileAsCorners(c1=Cell(x=-10, y=10), c2=Cell(x=10, y=10)))

    assert vertical.intersection(horizontal) == Tile.build(
        TileAsCorners(c1=Cell(0, 10), c2=Cell(0, 10))
    )
