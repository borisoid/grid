from grid.model import Cell, TileCoordsAsCorners, TileCoordsAsStep


def test_1() -> None:
    # Setup {{{
    tile_as_step = TileCoordsAsStep(
        cell=Cell(0, 0),
        step=Cell(2, 3),
    )
    # }}} Setup

    # Act {{{
    tile_as_corners = tile_as_step.as_corners()
    # }}} Act

    # Assert {{{
    assert tile_as_corners == TileCoordsAsCorners(
        c0=Cell(0, 0),
        c3=Cell(2, 3),
    )
    # }}} Assert
