from source.grid.model import Cell, Tile, TileAsCorners, TileAsStep


def test_TileAsCorners_normalize() -> None:
    # Setup {{{
    tile_as_corners = TileAsCorners(
        c1=Cell(5, 1),
        c2=Cell(1, 5),
    )
    # }}} Setup

    # Act {{{
    tile_as_corners_normalized = tile_as_corners.normalize()
    # }}} Act

    # Assert {{{
    assert tile_as_corners_normalized == TileAsCorners(
        c1=Cell(1, 1),
        c2=Cell(5, 5),
    )
    # }}} Assert


def test_TileAsStep_as_corners__when_normalized_and_origin() -> None:
    # Setup {{{
    tile_as_step = TileAsStep(
        cell=Cell(0, 0),
        step=Cell(2, 3),
    )
    # }}} Setup

    # Act {{{
    tile_as_corners = tile_as_step.as_corners()
    # }}} Act

    # Assert {{{
    assert tile_as_corners == TileAsCorners(
        c1=Cell(0, 0),
        c2=Cell(2, 3),
    )
    # }}} Assert


def test_Tile_from_cells__when_false() -> None:
    # Setup {{{
    cells = (
        Cell(0, 1),
        Cell(1, 0),
    )
    # }}} Setup

    # Act {{{
    result = Tile.from_cells(cells)
    # }}} Act

    # Assert {{{
    assert result is None
    # }}} Assert


def test_Tile_from_cells__when_true() -> None:
    # Setup {{{
    cells = (
        Cell(0, 0),
        Cell(0, 1),
        Cell(1, 0),
        Cell(1, 1),
    )
    # }}} Setup

    # Act {{{
    result = Tile.from_cells(cells)
    # }}} Act

    # Assert {{{
    assert result == Tile.build(
        TileAsCorners(
            c1=Cell(0, 0),
            c2=Cell(1, 1),
        )
    )
    # }}} Assert


def test_Tile_from_cells__when_single_cell() -> None:
    # Setup {{{
    cells = (Cell(0, 0),)
    # }}} Setup

    # Act {{{
    result = Tile.from_cells(cells)
    # }}} Act

    # Assert {{{
    assert result == Tile.build(
        TileAsCorners(
            c1=Cell(0, 0),
            c2=Cell(0, 0),
        )
    )
    # }}} Assert
