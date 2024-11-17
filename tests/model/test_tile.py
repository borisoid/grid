from grid.model import Cell, TileAsCorners, TileAsStep


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
