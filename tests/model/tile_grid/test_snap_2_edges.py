from grid.model import Cell, Tile, TileAsCorners, TileGrid


def test_1() -> None:
    g1 = TileGrid.from_tiles(
        (
            Tile.build(TileAsCorners(Cell(0, 0), Cell(5, 5)), handle=1),
            Tile.build(TileAsCorners(Cell(0, 6), Cell(4, 10)), handle=2),
            Tile.build(TileAsCorners(Cell(6, 0), Cell(10, 5)), handle=3),
            Tile.build(TileAsCorners(Cell(5, 6), Cell(10, 10)), handle=4),
        ),
    )
    g2 = TileGrid.from_tiles(
        (
            Tile.build(TileAsCorners(Cell(0, 0), Cell(5, 5)), handle=1),
            Tile.build(TileAsCorners(Cell(0, 6), Cell(5, 10)), handle=2),
            Tile.build(TileAsCorners(Cell(6, 0), Cell(10, 5)), handle=3),
            Tile.build(TileAsCorners(Cell(6, 6), Cell(10, 10)), handle=4),
        ),
    )

    assert g1.snap_2_edges(handle=1) == g2
