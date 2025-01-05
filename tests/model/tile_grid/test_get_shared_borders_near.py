from grid.model import BorderMode, Cell, SharedBorders, TileGrid, Tile, TileAsStep


def test_1() -> None:
    tg = TileGrid.from_(
        Tile.build(TileAsStep(Cell(0, 0), Cell(5, 5)), handle=1),
        Tile.build(TileAsStep(Cell(6, 0), Cell(5, 5)), handle=2),
        Tile.build(TileAsStep(Cell(0, 6), Cell(5, 5)), handle=3),
        Tile.build(TileAsStep(Cell(6, 6), Cell(5, 5)), handle=4),
    )

    borders = tg.get_shared_borders_near(Cell(5, 5), mode=BorderMode.SHORTEST)

    assert borders == SharedBorders(
        left=frozenset((tg.tiles[0], tg.tiles[2])),
        right=frozenset((tg.tiles[1], tg.tiles[3])),
        top=frozenset((tg.tiles[0], tg.tiles[1])),
        bottom=frozenset((tg.tiles[2], tg.tiles[3])),
    )
