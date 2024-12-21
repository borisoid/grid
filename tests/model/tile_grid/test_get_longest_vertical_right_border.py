from grid.model import Cell, SharedBorders, Tile, TileAsCorners, TileGrid


def test_1() -> None:
    t1 = Tile.build(
        TileAsCorners(Cell(0, 0), Cell(5, 5)),
        handle=1,
    )
    t2 = Tile.build(TileAsCorners(Cell(0, 6), Cell(5, 10)))
    t3 = Tile.build(TileAsCorners(Cell(6, 0), Cell(10, 5)))
    t4 = Tile.build(TileAsCorners(Cell(6, 6), Cell(10, 10)))
    g = TileGrid((t1, t2, t3, t4))

    assert g.get_longest_vertical_right_border(1) == SharedBorders({t1, t2}, {t3, t4})
