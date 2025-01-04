from grid.model import Cell, Tile, TileAsCorners, TileGrid, SharedBorders


def test_1() -> None:
    t1 = Tile.build(
        TileAsCorners(Cell(6, 0), Cell(10, 5)),
        handle=1,
    )
    t2 = Tile.build(TileAsCorners(Cell(6, 6), Cell(10, 10)))
    t3 = Tile.build(TileAsCorners(Cell(0, 0), Cell(5, 10)))
    g = TileGrid((t1, t2, t3))

    assert g.get_shortest_left_border(1) == SharedBorders(
        frozenset({t3}), frozenset({t1, t2})
    )


def test_2() -> None:
    t1 = Tile.build(
        TileAsCorners(Cell(6, 0), Cell(10, 5)),
        handle=1,
    )
    t2 = Tile.build(TileAsCorners(Cell(6, 6), Cell(10, 10)))
    t3 = Tile.build(TileAsCorners(Cell(0, 0), Cell(5, 5)))
    t4 = Tile.build(TileAsCorners(Cell(0, 6), Cell(5, 10)))
    g = TileGrid((t1, t2, t3, t4))

    assert g.get_shortest_left_border(1) == SharedBorders(
        frozenset({t3}), frozenset({t1})
    )


def test_3() -> None:
    t1 = Tile.build(
        TileAsCorners(Cell(6, 0), Cell(10, 5)),
        handle=1,
    )
    t2 = Tile.build(TileAsCorners(Cell(6, 6), Cell(10, 10)))
    t3 = Tile.build(TileAsCorners(Cell(0, 0), Cell(5, 6)))
    t4 = Tile.build(TileAsCorners(Cell(0, 7), Cell(5, 10)))
    g = TileGrid((t1, t2, t3, t4))

    assert g.get_shortest_left_border(1) == SharedBorders(
        frozenset({t3, t4}), frozenset({t1, t2})
    )


def test_4() -> None:
    t1 = Tile.build(
        TileAsCorners(Cell(6, 0), Cell(10, 5)),
        handle=1,
    )
    t2 = Tile.build(TileAsCorners(Cell(6, 6), Cell(10, 10)))
    t3 = Tile.build(TileAsCorners(Cell(0, 0), Cell(5, 2)))
    t4 = Tile.build(TileAsCorners(Cell(0, 3), Cell(5, 7)))
    t5 = Tile.build(TileAsCorners(Cell(5, 8), Cell(5, 10)))
    t6 = Tile.build(TileAsCorners(Cell(0, 11), Cell(10, 11)))
    g = TileGrid((t1, t2, t3, t4, t5, t6))

    assert g.get_shortest_left_border(1) == SharedBorders(
        frozenset({t3, t4, t5}), frozenset({t1, t2})
    )


def test_5() -> None:
    t1 = Tile.build(TileAsCorners(Cell(6, 0), Cell(10, 5)))
    t2 = Tile.build(
        TileAsCorners(Cell(6, 6), Cell(10, 10)),
        handle=1,
    )
    t3 = Tile.build(TileAsCorners(Cell(0, 0), Cell(5, 2)))
    t4 = Tile.build(TileAsCorners(Cell(0, 3), Cell(5, 7)))
    t5 = Tile.build(TileAsCorners(Cell(0, 8), Cell(5, 10)))
    t6 = Tile.build(TileAsCorners(Cell(0, 11), Cell(10, 11)))
    g = TileGrid((t1, t2, t3, t4, t5, t6))

    assert g.get_shortest_left_border(1) == SharedBorders(
        frozenset({t3, t4, t5}), frozenset({t1, t2})
    )


def test_6() -> None:
    t1 = Tile.build(TileAsCorners(Cell(6, 0), Cell(10, 5)))
    t2 = Tile.build(TileAsCorners(Cell(6, 6), Cell(10, 10)))
    t3 = Tile.build(
        TileAsCorners(Cell(0, 0), Cell(5, 2)),
        handle=1,
    )
    t4 = Tile.build(TileAsCorners(Cell(0, 3), Cell(5, 7)))
    t5 = Tile.build(TileAsCorners(Cell(0, 8), Cell(5, 10)))
    t6 = Tile.build(TileAsCorners(Cell(0, 11), Cell(10, 11)))
    g = TileGrid((t1, t2, t3, t4, t5, t6))

    assert g.get_shortest_left_border(1) == SharedBorders(
        frozenset(), frozenset({t3, t4, t5, t6})
    )
