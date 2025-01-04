from grid.model import Cell, GridSection, Tile, TileAsCorners, get_grid_section


def test_get_grid_section__when_origin() -> None:
    # Setup {{{
    cell = Cell(x=0, y=0)
    origin_tile = Tile.build(
        TileAsCorners(
            c0=Cell(x=0, y=0),
            c3=Cell(x=5, y=5),
        )
    )
    # }}} Setup

    # Act {{{
    result = get_grid_section(cell=cell, origin_tile=origin_tile)
    # }}} Act

    # Assert {{{
    assert result == GridSection.ORIGIN
    # }}}


def test_get_grid_section__when_top() -> None:
    # Setup {{{
    cell = Cell(x=0, y=-1)
    origin_tile = Tile.build(
        TileAsCorners(
            c0=Cell(x=0, y=0),
            c3=Cell(x=5, y=5),
        )
    )
    # }}} Setup

    # Act {{{
    result = get_grid_section(cell=cell, origin_tile=origin_tile)
    # }}} Act

    # Assert {{{
    assert result == GridSection.TOP
    # }}}


def test_get_grid_section__when_bottom() -> None:
    # Setup {{{
    cell = Cell(x=0, y=6)
    origin_tile = Tile.build(
        TileAsCorners(
            c0=Cell(x=0, y=0),
            c3=Cell(x=5, y=5),
        )
    )
    # }}} Setup

    # Act {{{
    result = get_grid_section(cell=cell, origin_tile=origin_tile)
    # }}} Act

    # Assert {{{
    assert result == GridSection.BOTTOM
    # }}}


def test_get_grid_section__when_left() -> None:
    # Setup {{{
    cell = Cell(x=-1, y=0)
    origin_tile = Tile.build(
        TileAsCorners(
            c0=Cell(x=0, y=0),
            c3=Cell(x=5, y=5),
        )
    )
    # }}} Setup

    # Act {{{
    result = get_grid_section(cell=cell, origin_tile=origin_tile)
    # }}} Act

    # Assert {{{
    assert result == GridSection.LEFT
    # }}}


def test_get_grid_section__when_right() -> None:
    # Setup {{{
    cell = Cell(x=6, y=0)
    origin_tile = Tile.build(
        TileAsCorners(
            c0=Cell(x=0, y=0),
            c3=Cell(x=5, y=5),
        )
    )
    # }}} Setup

    # Act {{{
    result = get_grid_section(cell=cell, origin_tile=origin_tile)
    # }}} Act

    # Assert {{{
    assert result == GridSection.RIGHT
    # }}}


def test_get_grid_section__when_top_left() -> None:
    # Setup {{{
    cell = Cell(x=-1, y=-1)
    origin_tile = Tile.build(
        TileAsCorners(
            c0=Cell(x=0, y=0),
            c3=Cell(x=5, y=5),
        )
    )
    # }}} Setup

    # Act {{{
    result = get_grid_section(cell=cell, origin_tile=origin_tile)
    # }}} Act

    # Assert {{{
    assert result == GridSection.TOP_LEFT
    # }}}


def test_get_grid_section__when_top_right() -> None:
    # Setup {{{
    cell = Cell(x=6, y=-1)
    origin_tile = Tile.build(
        TileAsCorners(
            c0=Cell(x=0, y=0),
            c3=Cell(x=5, y=5),
        )
    )
    # }}} Setup

    # Act {{{
    result = get_grid_section(cell=cell, origin_tile=origin_tile)
    # }}} Act

    # Assert {{{
    assert result == GridSection.TOP_RIGHT
    # }}}


def test_get_grid_section__when_bottom_left() -> None:
    # Setup {{{
    cell = Cell(x=-1, y=6)
    origin_tile = Tile.build(
        TileAsCorners(
            c0=Cell(x=0, y=0),
            c3=Cell(x=5, y=5),
        )
    )
    # }}} Setup

    # Act {{{
    result = get_grid_section(cell=cell, origin_tile=origin_tile)
    # }}} Act

    # Assert {{{
    assert result == GridSection.BOTTOM_LEFT
    # }}}


def test_get_grid_section__when_bottom_right() -> None:
    # Setup {{{
    cell = Cell(x=6, y=6)
    origin_tile = Tile.build(
        TileAsCorners(
            c0=Cell(x=0, y=0),
            c3=Cell(x=5, y=5),
        )
    )
    # }}} Setup

    # Act {{{
    result = get_grid_section(cell=cell, origin_tile=origin_tile)
    # }}} Act

    # Assert {{{
    assert result == GridSection.BOTTOM_RIGHT
    # }}}
