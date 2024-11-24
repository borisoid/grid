from grid.model import Cell, Tile, TileAsCorners, TileGrid


def test_1() -> None:
    t1 = Tile.build(
        TileAsCorners(Cell(0, 0), Cell(5, 5)),
        handle=1,
    )
    t2 = Tile.build(TileAsCorners(Cell(0, 6), Cell(5, 10)))
    t3 = Tile.build(TileAsCorners(Cell(6, 0), Cell(10, 10)))
    g = TileGrid(t1, (t2, t3))

    assert g.get_uninterrupted_vertical_right_border(1) == ({t1, t2}, {t3})


def test_2() -> None:
    t1 = Tile.build(
        TileAsCorners(Cell(0, 0), Cell(5, 5)),
        handle=1,
    )
    t2 = Tile.build(TileAsCorners(Cell(0, 6), Cell(5, 10)))
    t3 = Tile.build(TileAsCorners(Cell(6, 0), Cell(10, 5)))
    t4 = Tile.build(TileAsCorners(Cell(6, 6), Cell(10, 10)))
    g = TileGrid(t1, (t2, t3, t4))

    assert g.get_uninterrupted_vertical_right_border(1) == ({t1}, {t3})


def test_3() -> None:
    t1 = Tile.build(
        TileAsCorners(Cell(0, 0), Cell(5, 5)),
        handle=1,
    )
    t2 = Tile.build(TileAsCorners(Cell(0, 6), Cell(5, 10)))
    t3 = Tile.build(TileAsCorners(Cell(6, 0), Cell(10, 6)))
    t4 = Tile.build(TileAsCorners(Cell(6, 7), Cell(10, 10)))
    g = TileGrid(t1, (t2, t3, t4))

    assert g.get_uninterrupted_vertical_right_border(1) == ({t1, t2}, {t3, t4})


def test_4() -> None:
    t1 = Tile.build(
        TileAsCorners(Cell(0, 0), Cell(5, 5)),
        handle=1,
    )
    t2 = Tile.build(TileAsCorners(Cell(0, 6), Cell(5, 10)))
    t3 = Tile.build(TileAsCorners(Cell(6, 0), Cell(10, 2)))
    t4 = Tile.build(TileAsCorners(Cell(6, 3), Cell(10, 7)))
    t5 = Tile.build(TileAsCorners(Cell(6, 8), Cell(10, 10)))
    t6 = Tile.build(TileAsCorners(Cell(0, 11), Cell(10, 11)))
    g = TileGrid(t1, (t2, t3, t4, t5, t6))

    assert g.get_uninterrupted_vertical_right_border(1) == ({t1, t2}, {t3, t4, t5})


def test_5() -> None:
    t1 = Tile.build(TileAsCorners(Cell(0, 0), Cell(5, 5)))
    t2 = Tile.build(
        TileAsCorners(Cell(0, 6), Cell(5, 10)),
        handle=1,
    )
    t3 = Tile.build(TileAsCorners(Cell(6, 0), Cell(10, 2)))
    t4 = Tile.build(TileAsCorners(Cell(6, 3), Cell(10, 7)))
    t5 = Tile.build(TileAsCorners(Cell(6, 8), Cell(10, 10)))
    t6 = Tile.build(TileAsCorners(Cell(0, 11), Cell(10, 11)))
    g = TileGrid(t1, (t2, t3, t4, t5, t6))

    assert g.get_uninterrupted_vertical_right_border(1) == ({t1, t2}, {t3, t4, t5})


def test_6() -> None:
    t1 = Tile.build(TileAsCorners(Cell(0, 0), Cell(5, 5)))
    t2 = Tile.build(TileAsCorners(Cell(0, 6), Cell(5, 10)))
    t3 = Tile.build(
        TileAsCorners(Cell(6, 0), Cell(10, 2)),
        handle=1,
    )
    t4 = Tile.build(TileAsCorners(Cell(6, 3), Cell(10, 7)))
    t5 = Tile.build(TileAsCorners(Cell(6, 8), Cell(10, 10)))
    t6 = Tile.build(TileAsCorners(Cell(0, 11), Cell(10, 11)))
    g = TileGrid(t1, (t2, t3, t4, t5, t6))

    assert g.get_uninterrupted_vertical_right_border(1) == ({t3, t4, t5, t6}, set())
