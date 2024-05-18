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
from enum import Enum, auto
from types import MappingProxyType
from typing import Generator, Iterable, Literal, NewType, Sequence

from kiwisolver import Expression, Solver, Variable
from typing_extensions import deprecated


class Unreachable(Exception):
    pass


class CardinalDirection(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()


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


@dataclasses.dataclass(frozen=True, slots=True)
class TileAsSpan:
    cell: Cell
    span: Cell

    def as_corners(self) -> "TileAsCornersNormalized":
        return TileAsCorners(
            c1=self.cell,
            c2=self.cell + self.span,
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


TileAsSpanNormalized = NewType("TileAsSpanNormalized", TileAsSpan)
"""
`cell` is the top left corner - `cell.x` and `cell.y` are low.

```
assert cell.span.x >= 0
assert cell.span.y >= 0
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


@dataclasses.dataclass(frozen=True, slots=True)
class Tile:
    tile: TileAsCornersNormalized
    handle: IntHandle

    @staticmethod
    def build(arg: TileAsCorners | TileAsSpan, /, *, handle: IntHandle = -1) -> "Tile":
        if isinstance(arg, TileAsSpan):
            return Tile(tile=arg.as_corners(), handle=handle)

        return Tile(tile=arg.normalize(), handle=handle)

    def keep_handle(self, arg: TileAsCorners | TileAsSpan) -> "Tile":
        return Tile.build(arg, handle=self.handle)

    @deprecated("I probably don't need it")
    @staticmethod
    def from_cells(cells: Iterable[Cell]) -> "Tile | None":
        cells = set(cells)

        box = get_box(Tile.build(TileAsCorners(c1=cell, c2=cell)) for cell in cells)
        box_cells = set(box.cells())

        if box_cells == cells:
            return box
        else:
            return None

    def as_corners(self) -> TileAsCornersNormalized:
        return self.tile

    def as_span(self) -> TileAsSpanNormalized:
        tile = self.as_corners()

        return TileAsSpanNormalized(
            TileAsSpan(
                cell=tile.c1,
                span=tile.c2 - tile.c1,
            )
        )

    def cells(self) -> Generator[Cell, None, None]:
        tile = self.as_corners()

        for x in range(tile.c1.x, tile.c2.x + 1):
            for y in range(tile.c1.y, tile.c2.y + 1):
                yield Cell(x=x, y=y)

    def contains_cell(self, cell: Cell) -> bool:
        return cell in self.cells()

    def intersection_cells(self, other: "Tile") -> set[Cell]:
        return set(self.cells()).intersection(other.cells())

    def intersects_with(self, other: "Tile") -> bool:
        return len(self.intersection_cells(other)) > 0

    def contains_tile(self, other: "Tile") -> bool:
        return self.intersection_cells(other) == set(other.cells())

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

    @deprecated("I probably don't need it")
    def slice(self, *, line: "Line") -> "tuple[Tile, Tile] | Tile":
        tile = self.as_corners()

        if (
            (line.orientation == Orientation.HORIZONTAL)
            and ((line.coordinate <= tile.c1.y) or (line.coordinate > tile.c2.y))
        ) or (
            (line.orientation == Orientation.VERTICAL)
            and ((line.coordinate <= tile.c1.x) or (line.coordinate > tile.c2.x))
        ):
            return self

        t1c2, t2c1 = {
            Orientation.HORIZONTAL: (
                Cell(x=tile.c2.x, y=line.coordinate - 1),
                Cell(x=tile.c1.x, y=line.coordinate),
            ),
            Orientation.VERTICAL: (
                Cell(x=line.coordinate - 1, y=tile.c2.y),
                Cell(x=line.coordinate, y=tile.c1.y),
            ),
        }[line.orientation]

        return (
            Tile.build(TileAsCorners(c1=tile.c1, c2=t1c2)),
            Tile.build(TileAsCorners(c1=t2c1, c2=tile.c2)),
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

    def relation_to_line(self, line: "Line") -> "TileRelationToLine":
        span = self.as_span()
        corners = self.as_corners()

        if (
            (line.orientation == Orientation.HORIZONTAL)
            and (span.span.y == 0)
            and (span.cell.y == line.coordinate)
        ) or (
            (line.orientation == Orientation.VERTICAL)
            and (span.span.x == 0)
            and (span.cell.x == line.coordinate)
        ):
            return TileRelationToLine.FULLY_CONTAINED

        if (
            (line.orientation == Orientation.HORIZONTAL)
            and (line.coordinate < corners.c1.y)
        ) or (
            (line.orientation == Orientation.VERTICAL)
            and (line.coordinate < corners.c1.x)
        ):
            return TileRelationToLine.NO_INTERSECT_AND_MORE_POSITIVE

        if (
            (line.orientation == Orientation.HORIZONTAL)
            and (line.coordinate > corners.c2.y)
        ) or (
            (line.orientation == Orientation.VERTICAL)
            and (line.coordinate > corners.c2.x)
        ):
            return TileRelationToLine.NO_INTERSECT_AND_MORE_NEGATIVE

        if (
            (line.orientation == Orientation.HORIZONTAL)
            and (line.coordinate == corners.c1.y)
        ) or (
            (line.orientation == Orientation.VERTICAL)
            and (line.coordinate == corners.c1.x)
        ):
            return TileRelationToLine.EDGE_CONTAINED_REST_MORE_POSITIVE

        if (
            (line.orientation == Orientation.HORIZONTAL)
            and (line.coordinate == corners.c2.y)
        ) or (
            (line.orientation == Orientation.VERTICAL)
            and (line.coordinate == corners.c2.x)
        ):
            return TileRelationToLine.EDGE_CONTAINED_REST_MORE_NEGATIVE

        return TileRelationToLine.HAVE_COMMON_CELLS

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

    def get_uncovered_cells(self) -> set[Cell]:
        tiles = self.get_tiles()
        box = get_box(tiles)

        tiles_cells = set(itertools.chain(*(map(lambda t: t.cells(), tiles))))
        box_cells = set(box.cells())

        return box_cells - tiles_cells

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
            # # {{{ Prevent "shear line" problem. I.e. when
            # # 112 -> 12
            # # 344    34
            # if {
            #     TileRelationToLine.EDGE_CONTAINED_REST_MORE_NEGATIVE,
            #     TileRelationToLine.EDGE_CONTAINED_REST_MORE_POSITIVE,
            # }.issubset(t.relation_to_line(line) for t in current_grid.get_tiles()):
            #     continue
            # # }}}

            delta = {
                Orientation.HORIZONTAL: Cell(x=0, y=-1),
                Orientation.VERTICAL: Cell(x=-1, y=0),
            }[line.orientation]

            new_tiles: list[Tile] = []
            for tile in current_grid.get_tiles():
                match tile.relation_to_line(line):
                    case TileRelationToLine.FULLY_CONTAINED:
                        break
                    case TileRelationToLine.NO_INTERSECT_AND_MORE_NEGATIVE:
                        new_tiles.append(tile)
                    case TileRelationToLine.NO_INTERSECT_AND_MORE_POSITIVE:
                        new_tiles.append(
                            tile.keep_handle(
                                TileAsCorners(
                                    c1=tile.as_corners().c1 + delta,
                                    c2=tile.as_corners().c2 + delta,
                                )
                            )
                        )
                    case (
                        TileRelationToLine.HAVE_COMMON_CELLS
                        | TileRelationToLine.EDGE_CONTAINED_REST_MORE_NEGATIVE
                        | TileRelationToLine.EDGE_CONTAINED_REST_MORE_POSITIVE
                    ):
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
        # Guard {{{
        anchor_tile = self.get_tile_by_handle(anchor_handle)
        if anchor_tile is None:
            return self
        # }}}

        # Prepare. Rotate grid so that insert to the RIGHT needs to be done {{{
        match direction:
            case CardinalDirection.RIGHT:
                current_grid = self
            case CardinalDirection.DOWN:
                current_grid = self.rotate_counterclockwise()
            case CardinalDirection.UP:
                current_grid = self.rotate_clockwise()
            case CardinalDirection.LEFT:
                current_grid = self.rotate_counterclockwise().rotate_counterclockwise()
        # }}}

        anchor_tile = current_grid.get_tile_by_handle(anchor_handle)
        if anchor_tile is None:
            return self

        new_tiles: list[Tile] = []
        # Make space (to the RIGHT) {{{
        for tile in current_grid.get_tiles():
            if tile.handle == anchor_handle:
                new_tiles.append(tile)

            else:
                match tile.relation_to_line(
                    Line(
                        coordinate=anchor_tile.as_corners().c2.x,
                        orientation=Orientation.VERTICAL,
                    )
                ):
                    case TileRelationToLine.NO_INTERSECT_AND_MORE_NEGATIVE:
                        new_tiles.append(tile)
                    case (
                        TileRelationToLine.FULLY_CONTAINED
                        | TileRelationToLine.EDGE_CONTAINED_REST_MORE_NEGATIVE
                        | TileRelationToLine.EDGE_CONTAINED_REST_MORE_POSITIVE
                        | TileRelationToLine.HAVE_COMMON_CELLS
                    ):
                        new_tiles.append(
                            tile.keep_handle(
                                TileAsCorners(
                                    c1=tile.as_corners().c1,
                                    c2=tile.as_corners().c2 + Cell(x=1, y=0),
                                )
                            )
                        )
                    case TileRelationToLine.NO_INTERSECT_AND_MORE_POSITIVE:
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
                TileAsSpan(
                    cell=anchor_tile.as_corners().c2 + Cell(x=1, y=0),
                    span=Cell(x=0, y=-anchor_tile.as_span().span.y),
                ),
                handle=new_tile_handle,
            )
        )
        # }}}

        current_grid = TileGrid(origin=new_tiles[0], other=new_tiles[1:])
        # Rotate back to original orientation {{{
        match direction:
            case CardinalDirection.RIGHT:
                pass
            case CardinalDirection.DOWN:
                current_grid = current_grid.rotate_clockwise()
            case CardinalDirection.UP:
                current_grid = current_grid.rotate_counterclockwise()
            case CardinalDirection.LEFT:
                current_grid = current_grid.rotate_clockwise().rotate_clockwise()
        # }}}

        return current_grid

    def split_tile(
        self,
        *,
        tile_handle: IntHandle,
        direction: CardinalDirection,
        new_tile_handle: IntHandle,
    ) -> "TileGrid":
        # Guards {{{
        tile = self.get_tile_by_handle(tile_handle)
        if tile is None:
            return self
        # }}}

        # Prepare. Rotate grid so that insert to the RIGHT needs to be done {{{
        match direction:
            case CardinalDirection.RIGHT:
                current_grid = self
            case CardinalDirection.DOWN:
                current_grid = self.rotate_counterclockwise()
            case CardinalDirection.UP:
                current_grid = self.rotate_clockwise()
            case CardinalDirection.LEFT:
                current_grid = self.rotate_counterclockwise().rotate_counterclockwise()
        # }}}

        new_tiles: list[Tile] = []
        for tile in current_grid.get_tiles():
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

        current_grid = TileGrid(origin=new_tiles[0], other=new_tiles[1:])

        # Rotate back to original orientation {{{
        match direction:
            case CardinalDirection.RIGHT:
                pass
            case CardinalDirection.DOWN:
                current_grid = current_grid.rotate_clockwise()
            case CardinalDirection.UP:
                current_grid = current_grid.rotate_counterclockwise()
            case CardinalDirection.LEFT:
                current_grid = current_grid.rotate_clockwise().rotate_clockwise()
        # }}}

        return current_grid

    def translate(self, *, delta: Cell) -> "TileGrid":
        return TileGrid.from_tiles(
            tuple(tile.translate(delta=delta) for tile in self.get_tiles())
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

        @dataclasses.dataclass(frozen=True, slots=True)
        class TileVar:
            cell_x: Variable
            span_x: Variable

            cell_y: int
            span_y: int

            handle: IntHandle

        tiles_sorted = tuple(
            sorted(self.get_tiles(), key=lambda tile: tile.as_corners().c1.x)
        )

        # Variable declaration {{{
        tile_vars: dict[IntHandle, TileVar] = {
            tile.handle: TileVar(
                cell_x=Variable(f"cell.x.{tile.handle}"),
                span_x=Variable(f"span.x.{tile.handle}"),
                cell_y=tile.as_span().cell.y,
                span_y=tile.as_span().span.y,
                handle=tile.handle,
            )
            for tile in tiles_sorted
        }
        # }}}

        # Lines {{{
        tile_vars_groups: defaultdict[int, list[TileVar]] = defaultdict(list)
        for y in self.get_ys():
            for tile in tiles_sorted:
                match tile.relation_to_line(
                    Line(coordinate=y, orientation=Orientation.HORIZONTAL)
                ):
                    case (
                        TileRelationToLine.HAVE_COMMON_CELLS
                        | TileRelationToLine.FULLY_CONTAINED
                        | TileRelationToLine.EDGE_CONTAINED_REST_MORE_NEGATIVE
                        | TileRelationToLine.EDGE_CONTAINED_REST_MORE_POSITIVE
                    ):
                        tile_vars_groups[y].append(tile_vars[tile.handle])
                    case _:
                        pass

        max_tiles = max(len(tiles) for tiles in tile_vars_groups.values())
        # }}}

        solver = Solver()

        for tile_var in tile_vars.values():
            solver.addConstraint(tile_var.span_x >= 0)
            solver.addConstraint(tile_var.span_x <= x_length_new)

            match mode:
                case "scale":
                    # Scaling {{{

                    # span_x_new   x_length_new
                    # ---------- = ------------
                    # span_x_old   x_length_old

                    # span_x_new = (span_x_old * x_length_new) / x_length_old

                    a = self.get_tile_by_handle(tile_var.handle)
                    if a is None:
                        raise Unreachable

                    solver.addConstraint(
                        (tile_var.span_x + 1)
                        >= (
                            ((a.as_span().span.x + 1) * x_length_new)
                            // (self.get_box().as_span().span.x + 1)
                        )
                    )
                    # }}}
                case "balance":
                    # Balancing {{{
                    solver.addConstraint(
                        (tile_var.span_x + 1) >= (x_length_new // max_tiles)
                    )
                    # }}}

        # Position constraints {{{
        for tile_vars_group in tile_vars_groups.values():
            # Span constraints {{{
            def reducer(
                a: Variable | Expression, b: Variable | Expression
            ) -> Expression:
                return a + b

            expression = functools.reduce(
                reducer, (tile_vars.span_x + 1 for tile_vars in tile_vars_group)
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
                    tile.cell_x == (previous_tile.cell_x + previous_tile.span_x + 1)
                )
            # }}}

        # }}}

        solver.updateVariables()
        return TileGrid.from_tiles(
            Tile.build(
                TileAsSpan(
                    cell=Cell(
                        x=int(tile_var.cell_x.value()),
                        y=tile_var.cell_y,
                    ),
                    span=Cell(
                        x=int(tile_var.span_x.value()),
                        y=tile_var.span_y,
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


@dataclasses.dataclass(frozen=True, slots=True)
class Line:
    coordinate: int
    orientation: Orientation


# }}} Line


class TileRelationToLine(Enum):
    NO_INTERSECT_AND_MORE_NEGATIVE = auto()
    NO_INTERSECT_AND_MORE_POSITIVE = auto()
    HAVE_COMMON_CELLS = auto()
    FULLY_CONTAINED = auto()
    EDGE_CONTAINED_REST_MORE_NEGATIVE = auto()
    EDGE_CONTAINED_REST_MORE_POSITIVE = auto()


def get_grid_section(*, cell: Cell, origin_tile: Tile) -> GridSection:
    for c in origin_tile.cells():
        if c == cell:
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
