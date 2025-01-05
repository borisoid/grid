from grid.model import Cell, TileAsCorners


def test_1() -> None:
    # Setup {{{
    tile_as_corners = TileAsCorners(
        c0=Cell(5, 1),
        c3=Cell(1, 5),
    )
    # }}} Setup

    # Act {{{
    tile_as_corners_normalized = tile_as_corners.normalize()
    # }}} Act

    # Assert {{{
    assert tile_as_corners_normalized == TileAsCorners(
        c0=Cell(1, 1),
        c3=Cell(5, 5),
    )
    # }}} Assert
