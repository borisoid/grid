"""
Coordinates:
0 - +X
|
+Y


"""

import dataclasses
import functools
import itertools
from collections import Counter, defaultdict
from enum import Enum, IntEnum, auto
from types import MappingProxyType
from typing import Iterable, Literal, NewType, Sequence

from kiwisolver import Expression, Solver, Variable


class Unreachable(Exception):
    pass


class CardinalDirection(IntEnum):
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3


class GridSection(Enum):
    ORIGIN = auto()
    #
    TOP = auto()
    BOTTOM = auto()
    LEFT = auto()
    RIGHT = auto()
    #
    TOP_LEFT = auto()
    TOP_RIGHT = auto()
    BOTTOM_LEFT = auto()
    BOTTOM_RIGHT = auto()


grid_section_inverse = MappingProxyType(
    {
        GridSection.TOP: GridSection.BOTTOM,
        GridSection.BOTTOM: GridSection.TOP,
        GridSection.LEFT: GridSection.RIGHT,
        GridSection.RIGHT: GridSection.LEFT,
        GridSection.TOP_LEFT: GridSection.BOTTOM_RIGHT,
        GridSection.TOP_RIGHT: GridSection.BOTTOM_LEFT,
        GridSection.BOTTOM_LEFT: GridSection.TOP_RIGHT,
        GridSection.BOTTOM_RIGHT: GridSection.TOP_LEFT,
    }
)


@dataclasses.dataclass(frozen=True, slots=True, eq=True)
class Cell:
    x: int
    y: int

    def __add__(self, other: "Cell") -> "Cell":
        return Cell(
            x=self.x + other.x,
            y=self.y + other.y,
        )

    def __sub__(self, other: "Cell") -> "Cell":
        return Cell(
            x=self.x - other.x,
            y=self.y - other.y,
        )

    def rotate_clockwise(self) -> "Cell":
        return Cell(x=-self.y, y=self.x)

    def rotate_counterclockwise(self) -> "Cell":
        return Cell(x=self.y, y=-self.x)

    def rotate(self, side: CardinalDirection, /, *, to: CardinalDirection) -> "Cell":
        match (to - side) % 4:
            case 0:
                return self
            case 1:
                return self.rotate_clockwise()
            case 2:
                return self.rotate_clockwise().rotate_clockwise()
            case 3:
                return self.rotate_counterclockwise()
            case _:
                raise Unreachable


@dataclasses.dataclass(frozen=True, slots=True)
class TileAsStep:
    cell: Cell
    step: Cell

    def as_corners(self) -> "TileAsCornersNormalized":
        return TileAsCorners(
            c1=self.cell,
            c2=self.cell + self.step,
        ).normalize()


@dataclasses.dataclass(frozen=True, slots=True)
class TileAsCorners:
    c1: Cell
    c2: Cell

    def normalize(self) -> "TileAsCornersNormalized":
        return TileAsCornersNormalized(
            TileAsCorners(
                c1=Cell(
                    x=min(self.c1.x, self.c2.x),
                    y=min(self.c1.y, self.c2.y),
                ),
                c2=Cell(
                    x=max(self.c1.x, self.c2.x),
                    y=max(self.c1.y, self.c2.y),
                ),
            )
        )


TileAsStepNormalized = NewType("TileAsStepNormalized", TileAsStep)
"""
`cell` is the top left corner - `cell.x` and `cell.y` are low.

```
assert cell.step.x >= 0
assert cell.step.y >= 0
```
"""

TileAsCornersNormalized = NewType("TileAsCornersNormalized", TileAsCorners)
"""
`c1` is the top left corner - `c1.x` and `c1.y` are low.

`c2` is the bottom right corner - `c2.x` and `c2.y` are high.

```
delta = c2 - c1
assert delta.x >= 0
assert delta.y >= 0
```
"""


type IntHandle = int


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Tile:
    tile: TileAsCornersNormalized
    handle: IntHandle

    @staticmethod
    def build(arg: TileAsCorners | TileAsStep, /, *, handle: IntHandle = -1) -> "Tile":
        if isinstance(arg, TileAsStep):
            return Tile(tile=arg.as_corners(), handle=handle)

        return Tile(tile=arg.normalize(), handle=handle)

    def keep_handle(self, arg: TileAsCorners | TileAsStep) -> "Tile":
        return Tile.build(arg, handle=self.handle)

    @staticmethod
    def from_cells(cells: Iterable[Cell]) -> "Tile":
        return get_box(Tile.build(TileAsCorners(c1=cell, c2=cell)) for cell in cells)

    def as_corners(self) -> TileAsCornersNormalized:
        return self.tile

    def as_step(self) -> TileAsStepNormalized:
        tile = self.as_corners()

        return TileAsStepNormalized(
            TileAsStep(
                cell=tile.c1,
                step=tile.c2 - tile.c1,
            )
        )

    def contains_cell(self, cell: Cell) -> bool:
        c = self.as_corners()
        return (c.c1.x <= cell.x <= c.c2.x) and (c.c1.y <= cell.y <= c.c2.y)

    def intersection(self, other: "Tile") -> "Tile | None":
        self_s = self.as_step()
        other_s = other.as_step()

        cells = tuple(
            cell
            for cell in (
                self_s.cell,
                self_s.cell + dataclasses.replace(self_s.step, x=0),
                self_s.cell + dataclasses.replace(self_s.step, y=0),
                self_s.cell + self_s.step,
            )
            if other.contains_cell(cell)
        ) + tuple(
            cell
            for cell in (
                other_s.cell,
                other_s.cell + dataclasses.replace(other_s.step, x=0),
                other_s.cell + dataclasses.replace(other_s.step, y=0),
                other_s.cell + other_s.step,
            )
            if self.contains_cell(cell)
        )
        if len(cells) > 0:
            return Tile.from_cells(cells)
        return None

    def intersects_with(self, other: "Tile") -> bool:
        return self.intersection(other) is not None

    def contains_tile(self, other: "Tile") -> bool:
        return self.intersection(other) == other

    def min_max(self: "Tile", other: "Tile", /) -> "Tile":
        tile_1 = self.as_corners()
        tile_2 = other.as_corners()

        return Tile.build(
            TileAsCorners(
                c1=Cell(
                    x=min(tile_1.c1.x, tile_1.c2.x, tile_2.c1.x, tile_2.c2.x),
                    y=min(tile_1.c1.y, tile_1.c2.y, tile_2.c1.y, tile_2.c2.y),
                ),
                c2=Cell(
                    x=max(tile_1.c1.x, tile_1.c2.x, tile_2.c1.x, tile_2.c2.x),
                    y=max(tile_1.c1.y, tile_1.c2.y, tile_2.c1.y, tile_2.c2.y),
                ),
            )
        )

    def shred_vertically(self) -> tuple["Line", ...]:
        tile = self.as_corners()

        return tuple(
            Line(coordinate=x, orientation=Orientation.VERTICAL)
            for x in range(tile.c1.x, tile.c2.x + 1)
        )

    def shred_horizontally(self) -> tuple["Line", ...]:
        tile = self.as_corners()

        return tuple(
            Line(coordinate=y, orientation=Orientation.HORIZONTAL)
            for y in range(tile.c1.y, tile.c2.y + 1)
        )

    def rotate_clockwise(self) -> "Tile":
        return self.keep_handle(
            TileAsCorners(
                c1=self.as_corners().c1.rotate_clockwise(),
                c2=self.as_corners().c2.rotate_clockwise(),
            )
        )

    def rotate_counterclockwise(self) -> "Tile":
        return self.keep_handle(
            TileAsCorners(
                c1=self.as_corners().c1.rotate_counterclockwise(),
                c2=self.as_corners().c2.rotate_counterclockwise(),
            )
        )

    def rotate(self, side: CardinalDirection, /, *, to: CardinalDirection) -> "Tile":
        return self.keep_handle(
            TileAsCorners(
                c1=self.as_corners().c1.rotate(side, to=to),
                c2=self.as_corners().c2.rotate(side, to=to),
            )
        )

    def translate(self, *, delta: Cell) -> "Tile":
        return self.keep_handle(
            TileAsCorners(
                c1=self.as_corners().c1 + delta,
                c2=self.as_corners().c2 + delta,
            )
        )


def get_box(tiles: Iterable[Tile]) -> Tile:
    tiles = tuple(tiles)

    def reducer(a: Tile, b: Tile) -> Tile:
        return a.min_max(b)

    return functools.reduce(reducer, tiles, tiles[0])


@dataclasses.dataclass(frozen=True, slots=True)
class TileGrid:
    origin: Tile
    other: Sequence[Tile]

    @staticmethod
    def from_tiles(tiles: Iterable[Tile]) -> "TileGrid":
        tiles = tuple(tiles)
        return TileGrid(origin=tiles[0], other=tiles[1:])

    def get_tiles(self) -> tuple[Tile, ...]:
        return (self.origin, *self.other)

    def get_box(self) -> Tile:
        return get_box(self.get_tiles())

    def centralize_origin(self) -> "TileGrid":
        return self.translate(delta=Cell(x=0, y=0) - self.origin.as_corners().c1)

    def get_tile_by_handle(self, handle: IntHandle) -> Tile | None:
        for tile in self.get_tiles():
            if tile.handle == handle:
                return tile
        return None

    def count_handles(self) -> Counter[IntHandle]:
        return Counter(t.handle for t in self.get_tiles())

    def get_handle_errors(self) -> dict[IntHandle, int]:
        return {
            handle: count
            for handle, count in self.count_handles().items()
            if count != 1
        }

    def raise_if_handle_error(self) -> None:
        if errors := self.get_handle_errors():
            raise Exception(str(errors))

    def rotate_clockwise(self) -> "TileGrid":
        return TileGrid.from_tiles(x.rotate_clockwise() for x in self.get_tiles())

    def rotate_counterclockwise(self) -> "TileGrid":
        return TileGrid.from_tiles(
            x.rotate_counterclockwise() for x in self.get_tiles()
        )

    def rotate(
        self, side: CardinalDirection, /, *, to: CardinalDirection
    ) -> "TileGrid":
        return TileGrid.from_tiles(t.rotate(side, to=to) for t in self.get_tiles())

    def delete_by_handle(self, handle: IntHandle) -> "TileGrid":
        return TileGrid(
            origin=self.origin,
            other=tuple(x for x in self.other if x.handle != handle),
        )

    def compact(self) -> "TileGrid":
        current_grid = self

        box = self.get_box()

        for line in itertools.chain(
            sorted(box.shred_horizontally(), key=lambda l: l.coordinate, reverse=True),
            sorted(box.shred_vertically(), key=lambda l: l.coordinate, reverse=True),
        ):
            delta = {
                Orientation.HORIZONTAL: Cell(x=0, y=-1),
                Orientation.VERTICAL: Cell(x=-1, y=0),
            }[line.orientation]

            new_tiles: list[Tile] = []
            for tile in current_grid.get_tiles():
                if line.fully_contains_tile(tile):
                    break
                elif not line.intersects_tile(tile):
                    if line.on_positive_side_of_tile(tile):
                        new_tiles.append(tile)
                    elif line.on_negative_side_of_tile(tile):
                        new_tiles.append(
                            tile.keep_handle(
                                TileAsCorners(
                                    c1=tile.as_corners().c1 + delta,
                                    c2=tile.as_corners().c2 + delta,
                                )
                            )
                        )
                else:
                    new_tiles.append(
                        tile.keep_handle(
                            TileAsCorners(
                                c1=tile.as_corners().c1,
                                c2=tile.as_corners().c2 + delta,
                            )
                        )
                    )

            else:  # only executed if the loop did NOT break
                current_grid = TileGrid(origin=new_tiles[0], other=new_tiles[1:])

        return current_grid

    def expand(self) -> "TileGrid":
        tiles = tuple(self.get_tiles())
        box = get_box(tiles)
        new_tiles = list(tiles)
        for i, tile in enumerate(tiles):
            current_tiles = new_tiles[:i] + new_tiles[i + 1 :]

            for new_tile in (
                # Right
                tile.keep_handle(
                    TileAsCorners(
                        c1=tile.as_corners().c1,
                        c2=tile.as_corners().c2 + Cell(x=1, y=0),
                    )
                ),
                # Down
                tile.keep_handle(
                    TileAsCorners(
                        c1=tile.as_corners().c1,
                        c2=tile.as_corners().c2 + Cell(x=0, y=1),
                    )
                ),
                # Left
                tile.keep_handle(
                    TileAsCorners(
                        c1=tile.as_corners().c1 + Cell(x=-1, y=0),
                        c2=tile.as_corners().c2,
                    )
                ),
                # Up
                tile.keep_handle(
                    TileAsCorners(
                        c1=tile.as_corners().c1 + Cell(x=0, y=-1),
                        c2=tile.as_corners().c2,
                    )
                ),
            ):
                if (box.contains_tile(new_tile)) and (
                    not any(x.intersects_with(new_tile) for x in current_tiles)
                ):
                    new_tiles[i] = new_tile
                    break

            else:  # only executed if the loop did NOT break
                new_tiles[i] = tile

        return TileGrid(origin=new_tiles[0], other=new_tiles[1:])

    def insert(
        self,
        *,
        anchor_handle: IntHandle,
        direction: CardinalDirection,
        new_tile_handle: IntHandle,
    ) -> "TileGrid":
        return (
            self.rotate(direction, to=CardinalDirection.RIGHT)
            .insert_to_right(
                anchor_handle=anchor_handle, new_tile_handle=new_tile_handle
            )
            .rotate(CardinalDirection.RIGHT, to=direction)
        )

    def insert_to_right(
        self,
        *,
        anchor_handle: IntHandle,
        new_tile_handle: IntHandle,
    ) -> "TileGrid":
        # Guard {{{
        anchor_tile = self.get_tile_by_handle(anchor_handle)
        if anchor_tile is None:
            return self
        # }}}

        new_tiles: list[Tile] = []
        line = Line(
            coordinate=anchor_tile.as_corners().c2.x,
            orientation=Orientation.VERTICAL,
        )
        # Make space (to the RIGHT) {{{
        for tile in self.get_tiles():
            if tile.handle == anchor_handle:
                new_tiles.append(tile)

            elif (not line.intersects_tile(tile)) and line.on_positive_side_of_tile(
                tile
            ):
                new_tiles.append(tile)
            elif line.intersects_tile(tile):
                new_tiles.append(
                    tile.keep_handle(
                        TileAsCorners(
                            c1=tile.as_corners().c1,
                            c2=tile.as_corners().c2 + Cell(x=1, y=0),
                        )
                    )
                )
            elif (not line.intersects_tile(tile)) and line.on_negative_side_of_tile(
                tile
            ):
                new_tiles.append(
                    tile.keep_handle(
                        TileAsCorners(
                            c1=tile.as_corners().c1 + Cell(x=1, y=0),
                            c2=tile.as_corners().c2 + Cell(x=1, y=0),
                        )
                    )
                )
        # }}}

        # Insert new Tile (on the RIGHT) {{{
        new_tiles.append(
            Tile.build(
                TileAsStep(
                    cell=anchor_tile.as_corners().c2 + Cell(x=1, y=0),
                    step=Cell(x=0, y=-anchor_tile.as_step().step.y),
                ),
                handle=new_tile_handle,
            )
        )
        # }}}

        return TileGrid(origin=new_tiles[0], other=new_tiles[1:])

    def split_tile(
        self,
        *,
        tile_handle: IntHandle,
        direction: CardinalDirection,
        new_tile_handle: IntHandle,
    ) -> "TileGrid":
        return (
            self.rotate(direction, to=CardinalDirection.RIGHT)
            .split_tile_to_right(
                tile_handle=tile_handle,
                new_tile_handle=new_tile_handle,
            )
            .rotate(CardinalDirection.RIGHT, to=direction)
        )

    def split_tile_to_right(
        self,
        *,
        tile_handle: IntHandle,
        new_tile_handle: IntHandle,
    ) -> "TileGrid":
        # Guards {{{
        tile = self.get_tile_by_handle(tile_handle)
        if tile is None:
            return self
        # }}}

        new_tiles: list[Tile] = []
        for tile in self.get_tiles():
            corners = tile.as_corners()
            width = corners.c2.x - corners.c1.x

            if (tile.handle != tile_handle) or (width < 2):
                new_tiles.append(tile)
                continue

            c2 = Cell(x=corners.c1.x + (width // 2), y=corners.c2.y)
            c1 = Cell(x=c2.x + 1, y=corners.c1.y)

            new_tiles.extend(
                (
                    tile.keep_handle(
                        TileAsCorners(c1=corners.c1, c2=c2),
                    ),
                    Tile.build(
                        TileAsCorners(c1=c1, c2=corners.c2),
                        handle=new_tile_handle,
                    ),
                )
            )

        return TileGrid(origin=new_tiles[0], other=new_tiles[1:])

    def translate(self, *, delta: Cell) -> "TileGrid":
        return TileGrid.from_tiles(
            tile.translate(delta=delta) for tile in self.get_tiles()
        )

    def resize(self, *, new_boundary: Cell) -> "TileGrid":
        return (
            self.resize_along_x(x_length_new=new_boundary.x)
            .rotate_clockwise()
            .resize_along_x(x_length_new=new_boundary.y)
            .rotate_counterclockwise()
        )

    def resize_along_x(
        self, *, x_length_new: int, mode: Literal["balance", "scale"] = "scale"
    ) -> "TileGrid":

        self.raise_if_handle_error()

        @dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
        class TileVar:
            cell_x: Variable
            step_x: Variable

            cell_y: int
            step_y: int

            handle: IntHandle

        tiles_sorted = tuple(
            sorted(self.get_tiles(), key=lambda tile: tile.as_corners().c1.x)
        )

        # Variable declaration {{{
        tile_vars: dict[IntHandle, TileVar] = {
            tile.handle: TileVar(
                cell_x=Variable(f"cell.x.{tile.handle}"),
                step_x=Variable(f"step.x.{tile.handle}"),
                cell_y=tile.as_step().cell.y,
                step_y=tile.as_step().step.y,
                handle=tile.handle,
            )
            for tile in tiles_sorted
        }
        # }}}

        # Lines {{{
        tile_vars_groups: defaultdict[int, list[TileVar]] = defaultdict(list)
        for y in self.get_ys():
            line = Line(coordinate=y, orientation=Orientation.HORIZONTAL)
            for tile in tiles_sorted:
                if line.intersects_tile(tile):
                    tile_vars_groups[y].append(tile_vars[tile.handle])

        max_tiles = max(len(tiles) for tiles in tile_vars_groups.values())
        # }}}

        solver = Solver()

        for tile_var in tile_vars.values():
            solver.addConstraint(tile_var.step_x >= 0)
            solver.addConstraint(tile_var.step_x <= x_length_new)

            match mode:
                case "scale":
                    # Scaling {{{

                    # step_x_new   x_length_new
                    # ---------- = ------------
                    # step_x_old   x_length_old

                    # step_x_new = (step_x_old * x_length_new) / x_length_old

                    a = self.get_tile_by_handle(tile_var.handle)
                    if a is None:
                        raise Unreachable

                    solver.addConstraint(
                        (tile_var.step_x + 1)
                        >= (
                            ((a.as_step().step.x + 1) * x_length_new)
                            // (self.get_box().as_step().step.x + 1)
                        )
                    )
                    # }}}
                case "balance":
                    # Balancing {{{
                    solver.addConstraint(
                        (tile_var.step_x + 1) >= (x_length_new // max_tiles)
                    )
                    # }}}

        # Position constraints {{{
        for tile_vars_group in tile_vars_groups.values():
            # Step constraints {{{
            def reducer(
                a: Variable | Expression, b: Variable | Expression
            ) -> Expression:
                return a + b

            expression = functools.reduce(
                reducer, (tile_vars.step_x + 1 for tile_vars in tile_vars_group)
            )
            solver.addConstraint(expression == x_length_new)
            # }}}

            # Cell constraints {{{
            if len(tile_vars_group) > 0:
                # Don't let rows of tiles slide out of the box
                solver.addConstraint(tile_vars_group[0].cell_x == 0)

            for i in range(1, len(tile_vars_group)):
                previous_tile, tile = tile_vars_group[i - 1], tile_vars_group[i]
                solver.addConstraint(
                    tile.cell_x == (previous_tile.cell_x + previous_tile.step_x + 1)
                )
            # }}}

        # }}}

        solver.updateVariables()
        return TileGrid.from_tiles(
            Tile.build(
                TileAsStep(
                    cell=Cell(
                        x=int(tile_var.cell_x.value()),
                        y=tile_var.cell_y,
                    ),
                    step=Cell(
                        x=int(tile_var.step_x.value()),
                        y=tile_var.step_y,
                    ),
                ),
                handle=tile_var.handle,
            )
            for tile_var in (tile_vars[tile.handle] for tile in self.get_tiles())
        )

    def get_ys(self) -> set[int]:
        return set(
            itertools.chain(
                *((t.c1.y, t.c2.y) for t in (t.as_corners() for t in self.get_tiles()))
            )
        )


# Line {{{


class Orientation(Enum):
    HORIZONTAL = auto()
    VERTICAL = auto()

    def invert(self):
        return (
            Orientation.VERTICAL
            if self == Orientation.HORIZONTAL
            else Orientation.HORIZONTAL
        )


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Line:
    coordinate: int
    orientation: Orientation

    def rotate_clockwise(self) -> "Line":
        return Line(
            coordinate=(
                self.coordinate
                if self.orientation == Orientation.VERTICAL
                else -self.coordinate
            ),
            orientation=self.orientation.invert(),
        )

    def rotate_counterclockwise(self) -> "Line":
        return Line(
            coordinate=(
                self.coordinate
                if self.orientation == Orientation.HORIZONTAL
                else -self.coordinate
            ),
            orientation=self.orientation.invert(),
        )

    def fully_contains_tile(self, tile: Tile) -> bool:
        step = tile.as_step()

        return (
            (self.orientation == Orientation.HORIZONTAL)
            and (step.step.y == 0)
            and (step.cell.y == self.coordinate)
        ) or (
            (self.orientation == Orientation.VERTICAL)
            and (step.step.x == 0)
            and (step.cell.x == self.coordinate)
        )

    def intersects_tile(self, tile: Tile) -> bool:
        corners = tile.as_corners()

        return (
            (self.orientation == Orientation.HORIZONTAL)
            and (corners.c1.y <= self.coordinate <= corners.c2.y)
        ) or (
            (self.orientation == Orientation.VERTICAL)
            and (corners.c1.x <= self.coordinate <= corners.c2.x)
        )

    def touches_tile(self, tile: Tile) -> bool:
        corners = tile.as_corners()

        return (
            (self.orientation == Orientation.HORIZONTAL)
            and (self.coordinate in (corners.c1.y, corners.c2.y))
        ) or (
            (self.orientation == Orientation.VERTICAL)
            and (self.coordinate in (corners.c1.x, corners.c2.x))
        )

    def on_positive_side_of_tile(self, tile: Tile) -> bool:
        c = tile.as_corners()

        return (
            (self.orientation == Orientation.HORIZONTAL) and (self.coordinate >= c.c2.y)
        ) or (
            (self.orientation == Orientation.VERTICAL) and (self.coordinate >= c.c2.x)
        )

    def on_negative_side_of_tile(self, tile: Tile) -> bool:
        c = tile.as_corners()

        return (
            (self.orientation == Orientation.HORIZONTAL) and (self.coordinate <= c.c1.y)
        ) or (
            (self.orientation == Orientation.VERTICAL) and (self.coordinate <= c.c1.x)
        )


# }}} Line


def get_grid_section(*, cell: Cell, origin_tile: Tile) -> GridSection:
    if origin_tile.contains_cell(cell):
        return GridSection.ORIGIN

    origin_corners = origin_tile.as_corners()

    if (
        (cell.x >= origin_corners.c1.x)
        and (cell.x <= origin_corners.c2.x)
        and (cell.y < origin_corners.c1.y)
    ):
        return GridSection.TOP

    if (
        (cell.x >= origin_corners.c1.x)
        and (cell.x <= origin_corners.c2.x)
        and (cell.y > origin_corners.c2.y)
    ):
        return GridSection.BOTTOM

    if (
        (cell.y >= origin_corners.c1.y)
        and (cell.y <= origin_corners.c2.y)
        and (cell.x < origin_corners.c1.x)
    ):
        return GridSection.LEFT

    if (
        (cell.y >= origin_corners.c1.y)
        and (cell.y <= origin_corners.c2.y)
        and (cell.x > origin_corners.c2.x)
    ):
        return GridSection.RIGHT

    if (cell.x < origin_corners.c1.x) and (cell.y < origin_corners.c1.y):
        return GridSection.TOP_LEFT

    if (cell.x > origin_corners.c2.x) and (cell.y < origin_corners.c1.y):
        return GridSection.TOP_RIGHT

    if (cell.x < origin_corners.c1.x) and (cell.y > origin_corners.c2.y):
        return GridSection.BOTTOM_LEFT

    if (cell.x > origin_corners.c2.x) and (cell.y > origin_corners.c2.y):
        return GridSection.BOTTOM_RIGHT

    raise Unreachable
