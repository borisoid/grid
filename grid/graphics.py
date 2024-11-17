import itertools
import sys
from enum import Enum
from typing import Generator, Iterable

import pygame as pg

from .model import (
    CardinalDirection,
    Cell,
    IntHandle,
    Tile,
    TileAsCorners,
    TileGrid,
    get_box,
)


FPS = 24

WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 1000

CELL_SIDE_LENGTH = 20  # 35

CELLS_X = WINDOW_WIDTH // CELL_SIDE_LENGTH
CELLS_Y = WINDOW_HEIGHT // CELL_SIDE_LENGTH

GRID_LINE_WIDTH = 1
GRID_LINE_WIDTH_BOLD = 2
CELL_PADDING = 1

# Colors {{{
BLACK = pg.Color(0, 0, 0)
GREY_20 = pg.Color(20, 20, 20)
GREY_50 = pg.Color(50, 50, 50)
GREY_100 = pg.Color(100, 100, 100)
GREY_150 = pg.Color(150, 150, 150)
GREY_200 = pg.Color(200, 200, 200)
WHITE = pg.Color(255, 255, 255)

RED = pg.Color(255, 0, 0)
RED_150 = pg.Color(150, 0, 0)
RED_50 = pg.Color(50, 0, 0)

GREEN = pg.Color(0, 255, 0)
GREEN_170 = pg.Color(0, 170, 0)
GREEN_50 = pg.Color(0, 50, 0)

BLUE = pg.Color(0, 0, 255)
BLUE_150 = pg.Color(0, 0, 150)
BLUE_50 = pg.Color(0, 0, 50)

YELLOW = pg.Color(255, 255, 0)

ORANGE = pg.Color(255, 150, 100)

BACKGROUND_COLOR = BLACK
GRID_COLOR = GREY_100
AXIS_COLOR = WHITE
BOX_COLOR = RED
# }}} Colors


clock = pg.time.Clock()
screen = pg.display.set_mode(pg.Vector2(WINDOW_WIDTH, WINDOW_HEIGHT))


tile_colors: list[pg.Color] = []
for i, color in zip(range(20), itertools.cycle((RED, GREEN_170, BLUE_150))):
    tile_colors.append(color)


def handle_generator() -> Generator[IntHandle, None, None]:
    handle = 0
    while True:
        yield handle
        handle += 1


HANDLE_GENERATOR = handle_generator()


def generate_handle() -> IntHandle:
    return next(HANDLE_GENERATOR)


ORIGIN_HANDLE = generate_handle()


def draw(*, tiles: Iterable[Tile], box_corners: Tile) -> None:
    screen.fill(BACKGROUND_COLOR)

    # Grid {{{

    for cell_x in range(CELLS_X):
        pg.draw.line(
            surface=screen,
            color=GRID_COLOR,
            start_pos=pg.Vector2(cell_x * CELL_SIDE_LENGTH, 0),
            end_pos=pg.Vector2(cell_x * CELL_SIDE_LENGTH, WINDOW_HEIGHT),
            width=GRID_LINE_WIDTH,
        )

    for cell_y in range(CELLS_Y):
        pg.draw.line(
            surface=screen,
            color=GRID_COLOR,
            start_pos=pg.Vector2(0, cell_y * CELL_SIDE_LENGTH),
            end_pos=pg.Vector2(WINDOW_WIDTH, cell_y * CELL_SIDE_LENGTH),
            width=GRID_LINE_WIDTH,
        )

    # }}} Grid

    # Axis {{{

    for start, end in (
        (
            pg.Vector2((CELLS_X // 2) * CELL_SIDE_LENGTH, 0),
            pg.Vector2((CELLS_X // 2) * CELL_SIDE_LENGTH, WINDOW_HEIGHT),
        ),
        (
            pg.Vector2(((CELLS_X // 2) + 1) * CELL_SIDE_LENGTH, 0),
            pg.Vector2(((CELLS_X // 2) + 1) * CELL_SIDE_LENGTH, WINDOW_HEIGHT),
        ),
        (
            pg.Vector2(0, (CELLS_Y // 2) * CELL_SIDE_LENGTH),
            pg.Vector2(WINDOW_WIDTH, (CELLS_Y // 2) * CELL_SIDE_LENGTH),
        ),
        (
            pg.Vector2(0, ((CELLS_Y // 2) + 1) * CELL_SIDE_LENGTH),
            pg.Vector2(WINDOW_WIDTH, ((CELLS_Y // 2) + 1) * CELL_SIDE_LENGTH),
        ),
    ):
        pg.draw.line(
            surface=screen,
            color=AXIS_COLOR,
            start_pos=start,
            end_pos=end,
            width=GRID_LINE_WIDTH_BOLD,
        )

    # }}} Axis

    # Box {{{

    box_corners_2 = box_corners.as_corners()

    for start, end in (
        (
            pg.Vector2(box_corners_2.c1.x * CELL_SIDE_LENGTH, 0),
            pg.Vector2(box_corners_2.c1.x * CELL_SIDE_LENGTH, WINDOW_HEIGHT),
        ),
        (
            pg.Vector2((box_corners_2.c2.x + 1) * CELL_SIDE_LENGTH, 0),
            pg.Vector2((box_corners_2.c2.x + 1) * CELL_SIDE_LENGTH, WINDOW_HEIGHT),
        ),
        (
            pg.Vector2(0, box_corners_2.c1.y * CELL_SIDE_LENGTH),
            pg.Vector2(WINDOW_WIDTH, box_corners_2.c1.y * CELL_SIDE_LENGTH),
        ),
        (
            pg.Vector2(0, (box_corners_2.c2.y + 1) * CELL_SIDE_LENGTH),
            pg.Vector2(WINDOW_WIDTH, (box_corners_2.c2.y + 1) * CELL_SIDE_LENGTH),
        ),
    ):
        pg.draw.line(
            surface=screen,
            color=BOX_COLOR,
            start_pos=start,
            end_pos=end,
            width=GRID_LINE_WIDTH,
        )

    # }}} Box

    # Tiles {{{

    for tile, color in zip(tiles, tile_colors):
        tile_as_step = tile.as_step()
        pg.draw.rect(
            surface=screen,
            color=color,
            rect=pg.Rect(
                (tile_as_step.cell.x * CELL_SIDE_LENGTH) + CELL_PADDING,
                (tile_as_step.cell.y * CELL_SIDE_LENGTH) + CELL_PADDING,
                ((tile_as_step.step.x + 1) * CELL_SIDE_LENGTH) - (2 * CELL_PADDING),
                ((tile_as_step.step.y + 1) * CELL_SIDE_LENGTH) - (2 * CELL_PADDING),
            ),
        )

        if tile.handle == ORIGIN_HANDLE:
            pg.draw.rect(
                surface=screen,
                color=YELLOW,
                rect=pg.Rect(
                    (
                        (tile_as_step.cell.x * CELL_SIDE_LENGTH)
                        + ((tile_as_step.step.x // 3) * CELL_SIDE_LENGTH)
                    ),
                    (
                        (tile_as_step.cell.y * CELL_SIDE_LENGTH)
                        + ((tile_as_step.step.y // 3) * CELL_SIDE_LENGTH)
                    ),
                    (
                        ((tile_as_step.step.x + 1) * CELL_SIDE_LENGTH)
                        - ((tile_as_step.step.x // 3) * 2 * CELL_SIDE_LENGTH)
                    ),
                    (
                        ((tile_as_step.step.y + 1) * CELL_SIDE_LENGTH)
                        - ((tile_as_step.step.y // 3) * 2 * CELL_SIDE_LENGTH)
                    ),
                ),
            )

    # }}} Tiles

    pg.display.flip()


def translate_tile(tile: Tile) -> Tile:
    corners = tile.as_corners()

    delta = Cell(x=CELLS_X // 2, y=CELLS_Y // 2)
    return tile.keep_handle(
        TileAsCorners(
            c1=corners.c1 + delta,
            c2=corners.c2 + delta,
        )
    )


class Mode(Enum):
    NORMAL = "NORMAL"
    DELETE = "DELETE"

    INSERT_UP = "INSERT_UP"
    INSERT_DOWN = "INSERT_DOWN"
    INSERT_LEFT = "INSERT_LEFT"
    INSERT_RIGHT = "INSERT_RIGHT"

    SPLIT_UP = "SPLIT_UP"
    SPLIT_DOWN = "SPLIT_DOWN"
    SPLIT_LEFT = "SPLIT_LEFT"
    SPLIT_RIGHT = "SPLIT_RIGHT"


def start() -> None:
    # for _ in range(2):
    #     clock.tick(FPS)
    #     draw_grid_setup(tiles=TILES_NORMALIZED, box_corners=BOX_CORNERS)

    # print(list(box_iter(get_box_corners(TILES).normalize())))

    # ORIGINAL_TILE_GRID = tile_grid = TileGrid(
    #     origin=Tile.build(
    #         TileAsCorners(
    #             c1=Cell(x=0, y=-1),
    #             c2=Cell(x=0, y=-2),
    #         ),
    #         handle=ORIGIN_HANDLE,
    #     ),
    #     other=(
    #         Tile.build(
    #             TileAsCorners(
    #                 c1=Cell(x=0, y=1),
    #                 c2=Cell(x=1, y=1),
    #             ),
    #             handle=generate_handle(),
    #         ),
    #         Tile.build(
    #             TileAsCorners(
    #                 c1=Cell(x=-1, y=0),
    #                 c2=Cell(x=-1, y=1),
    #             ),
    #             handle=generate_handle(),
    #         ),
    #         Tile.build(
    #             TileAsCorners(
    #                 c1=Cell(x=1, y=-1),
    #                 c2=Cell(x=1, y=-1),
    #             ),
    #             handle=generate_handle(),
    #         ),
    #         Tile.build(
    #             TileAsCorners(
    #                 c1=Cell(x=0, y=0),
    #                 c2=Cell(x=1, y=0),
    #             ),
    #             handle=generate_handle(),
    #         ),
    #         Tile.build(
    #             TileAsCorners(
    #                 c1=Cell(x=-1, y=-1),
    #                 c2=Cell(x=-1, y=-1),
    #             ),
    #             handle=generate_handle(),
    #         ),
    #     ),
    # )

    ORIGINAL_TILE_GRID = tile_grid = TileGrid(
        origin=Tile.build(
            TileAsCorners(
                c1=Cell(x=0, y=0),
                c2=Cell(x=20, y=20),
            ),
            handle=ORIGIN_HANDLE,
        ),
        other=(),
    )

    mode = Mode.NORMAL
    mode_next = mode
    while True:
        # Controls {{{
        for e in pg.event.get():
            if (e.type == pg.QUIT) or ((e.type == pg.KEYDOWN) and (e.key == pg.K_q)):
                sys.exit()

            if e.type == pg.KEYDOWN:
                match e.key:
                    case pg.K_ESCAPE:
                        if mode == Mode.NORMAL:
                            sys.exit()
                        else:
                            mode_next = Mode.NORMAL

                    case pg.K_d:
                        mode_next = Mode.DELETE

                    case pg.K_h:
                        mode_next = Mode.SPLIT_LEFT
                    case pg.K_j:
                        mode_next = Mode.SPLIT_DOWN
                    case pg.K_k:
                        mode_next = Mode.SPLIT_UP
                    case pg.K_l:
                        mode_next = Mode.SPLIT_RIGHT

                    case pg.K_0:
                        tile_grid = tile_grid.compact().centralize_origin()
                        tile_grid = tile_grid.expand().centralize_origin()
                        tile_grid = tile_grid.compact().centralize_origin()

                    case pg.K_c:
                        tile_grid = tile_grid.compact().centralize_origin()

                    case pg.K_e:
                        tile_grid = tile_grid.expand().centralize_origin()

                    case pg.K_s:
                        # tile_grid = tile_grid.resize(new_boundary=Cell(x=10, y=10))
                        tile_grid = tile_grid.resize_along_x(x_length_new=10)

                    case pg.K_r:
                        tile_grid = ORIGINAL_TILE_GRID

                    case pg.K_z:
                        tile_grid = (
                            tile_grid.rotate_counterclockwise().centralize_origin()
                        )

                    case pg.K_x:
                        tile_grid = tile_grid.rotate_clockwise().centralize_origin()

                    case _:
                        pass

            if e.type == pg.MOUSEBUTTONUP:
                x, y = e.pos

                selected_tile: Tile | None = None
                for tile_translated in (
                    translate_tile(tile)
                    for tile in tile_grid.centralize_origin().get_tiles()
                ):
                    if tile_translated.contains_cell(
                        Cell(x=x // CELL_SIDE_LENGTH, y=y // CELL_SIDE_LENGTH)
                    ):
                        selected_tile = tile_translated
                        break

                if selected_tile is not None:
                    match mode:
                        case Mode.NORMAL:
                            pass
                        case Mode.DELETE:
                            tile_grid = tile_grid.delete_by_handle(selected_tile.handle)

                        case (
                            Mode.SPLIT_UP
                            | Mode.SPLIT_DOWN
                            | Mode.SPLIT_LEFT
                            | Mode.SPLIT_RIGHT
                        ):
                            tile_grid = tile_grid.split_tile(
                                tile_handle=selected_tile.handle,
                                new_tile_handle=generate_handle(),
                                direction={
                                    Mode.SPLIT_UP: CardinalDirection.UP,
                                    Mode.SPLIT_DOWN: CardinalDirection.DOWN,
                                    Mode.SPLIT_LEFT: CardinalDirection.LEFT,
                                    Mode.SPLIT_RIGHT: CardinalDirection.RIGHT,
                                }[mode],
                            )

        # }}} Controls

        if mode_next != mode:
            mode = mode_next
            print(f"Mode: {mode.value}")

        # Logic {{{
        tiles_translated = [
            translate_tile(tile) for tile in tile_grid.centralize_origin().get_tiles()
        ]
        box_corners = get_box(tiles_translated)
        # }}} Logic

        # Draw {{{
        draw(tiles=tiles_translated, box_corners=box_corners)
        clock.tick(FPS)
        # }}} Draw


def main() -> None:
    start()


if __name__ == "__main__":
    main()
