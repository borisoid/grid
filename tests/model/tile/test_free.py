from source.grid.model import Cell, Orientation, Tile, TileAsCorners


def test_1() -> None:
    t1 = Tile.build(TileAsCorners(Cell(0, 0), Cell(5, 5)))
    t2 = Tile.build(TileAsCorners(Cell(0, 0), Cell(4, 4)))

    assert t1.free(t2, prefer=Orientation.HORIZONTAL) == Tile.build(
        TileAsCorners(Cell(0, 5), Cell(5, 5))
    )


def test_2() -> None:
    t1 = Tile.build(TileAsCorners(Cell(0, 0), Cell(5, 5)))
    t2 = Tile.build(TileAsCorners(Cell(0, 0), Cell(4, 4)))

    assert t1.free(t2, prefer=Orientation.VERTICAL) == Tile.build(
        TileAsCorners(Cell(5, 0), Cell(5, 5))
    )


def test_3() -> None:
    t1 = t2 = Tile.build(TileAsCorners(Cell(0, 0), Cell(5, 5)))

    assert t1.free(t2, prefer=Orientation.VERTICAL) is None


def test_4() -> None:
    t1 = Tile.build(TileAsCorners(Cell(0, 0), Cell(5, 5)))
    t2 = Tile.build(TileAsCorners(Cell(-2, -2), Cell(-1, -1)))

    assert t1.free(t2, prefer=Orientation.VERTICAL) == t1


def test_5() -> None:
    t1 = Tile.build(TileAsCorners(Cell(0, 0), Cell(5, 5)))
    t2 = Tile.build(TileAsCorners(Cell(2, -2), Cell(3, 3)))

    assert t1.free(t2, prefer=Orientation.VERTICAL) is None


def test_6() -> None:
    t1 = Tile.build(TileAsCorners(Cell(0, 0), Cell(5, 5)))
    t2 = Tile.build(TileAsCorners(Cell(2, -2), Cell(6, 3)))

    assert t1.free(t2, prefer=Orientation.VERTICAL) == Tile.build(
        TileAsCorners(Cell(0, 0), Cell(1, 5))
    )
