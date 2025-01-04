from grid.model import Cell, Tile, TileAsCorners, TileGrid


def test_1() -> None:
    g1 = TileGrid.from_(
        Tile.build(TileAsCorners(Cell(6, 0), Cell(10, 5)), handle=1),
        Tile.build(TileAsCorners(Cell(7, 6), Cell(10, 10)), handle=2),
        Tile.build(TileAsCorners(Cell(0, 0), Cell(5, 5)), handle=3),
        Tile.build(TileAsCorners(Cell(0, 6), Cell(6, 10)), handle=4),
    )
    g2 = TileGrid.from_(
        Tile.build(TileAsCorners(Cell(6, 0), Cell(10, 5)), handle=1),
        Tile.build(TileAsCorners(Cell(6, 6), Cell(10, 10)), handle=2),
        Tile.build(TileAsCorners(Cell(0, 0), Cell(5, 5)), handle=3),
        Tile.build(TileAsCorners(Cell(0, 6), Cell(5, 10)), handle=4),
    )

    assert g1.align_below_tile_left_border_to_left(handle=1) == g2


# def test_2() -> None:
#     g1 = TileGrid.from_(
#         Tile.build(TileAsCorners(c0=Cell(x=10, y=0), c3=Cell(x=20, y=10)), handle=0),
#         Tile.build(TileAsCorners(c0=Cell(x=0, y=10), c3=Cell(x=9, y=12)), handle=1),
#         Tile.build(TileAsCorners(c0=Cell(x=10, y=11), c3=Cell(x=20, y=20)), handle=2),
#         Tile.build(TileAsCorners(c0=Cell(x=0, y=0), c3=Cell(x=9, y=9)), handle=3),
#         Tile.build(TileAsCorners(c0=Cell(x=0, y=16), c3=Cell(x=9, y=20)), handle=4),
#         Tile.build(TileAsCorners(c0=Cell(x=0, y=13), c3=Cell(x=9, y=15)), handle=5),
#     )

#     g2 = TileGrid.from_(
#         Tile.build(TileAsCorners(c0=Cell(x=10, y=0), c3=Cell(x=20, y=9)), handle=0),
#         Tile.build(TileAsCorners(c0=Cell(x=0, y=10), c3=Cell(x=9, y=12)), handle=1),
#         Tile.build(TileAsCorners(c0=Cell(x=10, y=10), c3=Cell(x=20, y=20)), handle=2),
#         Tile.build(TileAsCorners(c0=Cell(x=0, y=0), c3=Cell(x=9, y=9)), handle=3),
#         Tile.build(TileAsCorners(c0=Cell(x=0, y=16), c3=Cell(x=9, y=20)), handle=4),
#         Tile.build(TileAsCorners(c0=Cell(x=0, y=13), c3=Cell(x=9, y=15)), handle=5),
#     )

#     assert g1.align_borders(proximity=3) == g2
