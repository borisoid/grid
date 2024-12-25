"""
Coordinates:
0 - +X
|
+Y

Direction precedence (From most to least significant):
From LEFT to RIGHT
Along X
From TOP to BOTTOM
Along Y
"""

import dataclasses
import functools
import itertools
from collections import Counter, defaultdict
from enum import Enum, IntEnum, auto
from types import MappingProxyType
from typing import Iterable, Literal, NewType
from dataclasses import dataclass

from kiwisolver import Expression, Solver, Variable


class GridModelException(Exception):
    pass


class Unreachable(GridModelException):
    pass


class InvariantViolation(GridModelException):
    pass


@dataclass
class Changed[T]:
    obj: T
    changed: bool


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


@dataclass(frozen=True, slots=True, eq=True)
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

    def mirror_horizontally(self) -> "Cell":
        return Cell(x=-self.x, y=self.y)

    def mirror_vertically(self) -> "Cell":
        return Cell(x=self.x, y=-self.y)


@dataclass(frozen=True, slots=True)
class TileAsSpan:
    cell: Cell
    span: Cell

    def as_corners(self) -> "TileAsCornersNormalized":
        return TileAsCorners(
            c1=self.cell,
            c2=self.cell + self.span + Cell(-1, -1),
        ).normalize()


@dataclass(frozen=True, slots=True)
class TileAsStep:
    cell: Cell
    step: Cell

    def as_corners(self) -> "TileAsCornersNormalized":
        return TileAsCorners(
            c1=self.cell,
            c2=self.cell + self.step,
        ).normalize()


@dataclass(frozen=True, slots=True)
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
assert cell.span.x >= 1
assert cell.span.y >= 1
```
"""

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


@dataclass(frozen=True, slots=True, kw_only=True)
class Tile:
    tile: TileAsCornersNormalized
    handle: IntHandle

    @staticmethod
    def build(
        arg: TileAsCorners | TileAsStep | TileAsSpan,
        /,
        *,
        handle: IntHandle = -1,
    ) -> "Tile":
        if isinstance(arg, TileAsStep):
            return Tile(tile=arg.as_corners(), handle=handle)

        if isinstance(arg, TileAsSpan):
            return Tile(tile=arg.as_corners(), handle=handle)

        return Tile(tile=arg.normalize(), handle=handle)

    def replace_tile(self, arg: TileAsCorners | TileAsStep) -> "Tile":
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

    def as_span(self) -> TileAsSpanNormalized:
        tile = self.as_corners()

        return TileAsSpanNormalized(
            TileAsSpan(
                cell=tile.c1,
                span=tile.c2 - tile.c1 + Cell(1, 1),
            )
        )

    def area(self) -> int:
        s = self.as_span()
        return s.span.x * s.span.y

    def corners_c1_add(self, cell: Cell) -> "Tile":
        tc = self.as_corners()
        return self.replace_tile(TileAsCorners(c1=tc.c1 + cell, c2=tc.c2))

    def corners_c2_add(self, cell: Cell) -> "Tile":
        tc = self.as_corners()
        return self.replace_tile(TileAsCorners(c1=tc.c1, c2=tc.c2 + cell))

    def contains_cell(self, cell: Cell) -> bool:
        c = self.as_corners()
        return (c.c1.x <= cell.x <= c.c2.x) and (c.c1.y <= cell.y <= c.c2.y)

    def intersection(self, other: "Tile") -> "Tile | None":
        cells = tuple(
            itertools.chain(
                (cell for cell in self.corner_cells() if other.contains_cell(cell)),
                (cell for cell in other.corner_cells() if self.contains_cell(cell)),
            )
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
        return self.replace_tile(
            TileAsCorners(
                c1=self.as_corners().c1.rotate_clockwise(),
                c2=self.as_corners().c2.rotate_clockwise(),
            )
        )

    def rotate_counterclockwise(self) -> "Tile":
        return self.replace_tile(
            TileAsCorners(
                c1=self.as_corners().c1.rotate_counterclockwise(),
                c2=self.as_corners().c2.rotate_counterclockwise(),
            )
        )

    def rotate(self, side: CardinalDirection, /, *, to: CardinalDirection) -> "Tile":
        return self.replace_tile(
            TileAsCorners(
                c1=self.as_corners().c1.rotate(side, to=to),
                c2=self.as_corners().c2.rotate(side, to=to),
            )
        )

    def mirror_horizontally(self) -> "Tile":
        return self.replace_tile(
            TileAsCorners(
                c1=self.as_corners().c1.mirror_horizontally(),
                c2=self.as_corners().c2.mirror_horizontally(),
            )
        )

    def mirror_vertically(self) -> "Tile":
        return self.replace_tile(
            TileAsCorners(
                c1=self.as_corners().c1.mirror_vertically(),
                c2=self.as_corners().c2.mirror_vertically(),
            )
        )

    def mirror(self, orientation: "Orientation") -> "Tile":
        match orientation:
            case Orientation.HORIZONTAL:
                return self.mirror_horizontally()
            case Orientation.VERTICAL:
                return self.mirror_vertically()

    def translate(self, *, delta: Cell) -> "Tile":
        return self.replace_tile(
            TileAsCorners(
                c1=self.as_corners().c1 + delta,
                c2=self.as_corners().c2 + delta,
            )
        )

    def corner_cells(self) -> tuple[Cell, Cell, Cell, Cell]:
        """
        Returns corner cells with these indexes:
        ```
        0--1
        |  |
        2--3
        ```
        """

        self_s = self.as_step()

        return (
            self_s.cell,
            self_s.cell + dataclasses.replace(self_s.step, y=0),
            self_s.cell + dataclasses.replace(self_s.step, x=0),
            self_s.cell + self_s.step,
        )

    def un_occupy(self, area: "Tile", /, *, prefer: "Orientation") -> "Tile | None":
        curr: "Tile | None" = self
        assert curr is not None

        rotate = prefer == Orientation.VERTICAL

        if rotate:
            curr = curr.rotate(CardinalDirection.UP, to=CardinalDirection.RIGHT)
            area = area.rotate(CardinalDirection.UP, to=CardinalDirection.RIGHT)

        curr = curr.un_occupy_horizontal(area)
        if curr is None:
            return None

        if rotate:
            curr = curr.rotate(CardinalDirection.RIGHT, to=CardinalDirection.UP)

        return curr

    def un_occupy_horizontal(self, area: "Tile", /) -> "Tile | None":
        curr = self

        inter = curr.intersection(area)
        if inter is None:
            return curr

        matching_corners = tuple(
            t[0]
            for t in itertools.product(curr.corner_cells(), inter.corner_cells())
            if t[0] == t[1]
        )

        if len(matching_corners) in (1, 2):
            pass
        elif len(matching_corners) == 3:
            raise Unreachable
        else:
            return None

        area_to_free = Tile.build(
            TileAsCorners(
                c1=dataclasses.replace(inter.as_corners().c1, x=curr.as_corners().c1.x),
                c2=dataclasses.replace(inter.as_corners().c2, x=curr.as_corners().c2.x),
            )
        )

        mirror = area_to_free.as_corners().c1 == curr.as_corners().c1
        if mirror:
            curr = curr.mirror_vertically()
            area_to_free = area_to_free.mirror_vertically()

        # Cut bottom part
        curr = curr.replace_tile(
            TileAsCorners(
                c1=curr.as_corners().c1,
                c2=area_to_free.corner_cells()[1] - Cell(0, 1),
            )
        )

        if mirror:
            curr = curr.mirror_vertically()

        return curr


def get_box(tiles: Iterable[Tile]) -> Tile:
    tiles = tuple(tiles)

    def reducer(a: Tile, b: Tile) -> Tile:
        return a.min_max(b)

    return functools.reduce(reducer, tiles, tiles[0])


def get_ys(tiles: Iterable[Tile]) -> set[int]:
    return set(
        itertools.chain(*((t.c1.y, t.c2.y) for t in (t.as_corners() for t in tiles)))
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class TileGridInvariantErrorContainer:
    handles: dict[IntHandle, int]
    overlapping_tiles: tuple[tuple[Tile, Tile], ...]
    area_mismatch: int

    def has_errors(self) -> bool:
        return any(
            (
                self.handles,
                self.overlapping_tiles,
                self.area_mismatch > 0,
            )
        )


class BorderMode(Enum):
    SHORTEST = auto()
    LONGEST = auto()


@dataclass(frozen=True, slots=True)
class SharedBorders:
    left: frozenset[Tile] = frozenset()
    right: frozenset[Tile] = frozenset()
    top: frozenset[Tile] = frozenset()
    bottom: frozenset[Tile] = frozenset()

    @staticmethod
    def empty() -> "SharedBorders":
        return SharedBorders(frozenset(), frozenset(), frozenset(), frozenset())

    def check(self) -> None:
        # TODO: Check if all edges align
        raise NotImplementedError

    def pull_coords(self, grid: "TileGrid") -> "SharedBorders":
        return SharedBorders(
            left=frozenset(
                tile
                for tile in grid.tiles
                if tile.handle in (t.handle for t in self.left)
            ),
            right=frozenset(
                tile
                for tile in grid.tiles
                if tile.handle in (t.handle for t in self.right)
            ),
            top=frozenset(
                tile
                for tile in grid.tiles
                if tile.handle in (t.handle for t in self.top)
            ),
            bottom=frozenset(
                tile
                for tile in grid.tiles
                if tile.handle in (t.handle for t in self.bottom)
            ),
        )

    def as_tiles(self) -> tuple[Tile | None, Tile | None]:
        """
        Return: (vertical, horizontal)
        """
        return (
            (
                Tile.from_cells(
                    itertools.chain(
                        *(tile.corner_cells()[0:3:2] for tile in self.right)
                    )
                )
                if self.right
                else None
            ),
            (
                Tile.from_cells(
                    itertools.chain(*(tile.corner_cells()[0:2] for tile in self.bottom))
                )
                if self.bottom
                else None
            ),
        )

    def union(self, other: "SharedBorders") -> "SharedBorders":
        # TODO: Make it respect only handles
        return SharedBorders(
            left=self.left.union(other.left),
            right=self.right.union(other.right),
            top=self.top.union(other.top),
            bottom=self.bottom.union(other.bottom),
        )

    def rotate(
        self, side: CardinalDirection, /, *, to: CardinalDirection
    ) -> "SharedBorders":
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

    def rotate_clockwise(self) -> "SharedBorders":
        return SharedBorders(
            left=frozenset(tile.rotate_clockwise() for tile in self.bottom),
            right=frozenset(tile.rotate_clockwise() for tile in self.top),
            top=frozenset(tile.rotate_clockwise() for tile in self.left),
            bottom=frozenset(tile.rotate_clockwise() for tile in self.right),
        )

    def rotate_counterclockwise(self) -> "SharedBorders":
        return SharedBorders(
            left=frozenset(tile.rotate_clockwise() for tile in self.top),
            right=frozenset(tile.rotate_clockwise() for tile in self.bottom),
            top=frozenset(tile.rotate_clockwise() for tile in self.right),
            bottom=frozenset(tile.rotate_clockwise() for tile in self.left),
        )


@dataclass(frozen=True, slots=True)
class TileGrid:
    tiles: tuple[Tile, ...]

    @staticmethod
    def from_(tiles: Iterable[Tile] | Tile, *tiles_: Tile) -> "TileGrid":
        if isinstance(tiles, Tile):
            tiles = (tiles,)

        return TileGrid(tuple(tiles) + tiles_)

    def get_box(self) -> Tile:
        return get_box(self.tiles)

    def centralize_origin(self) -> "TileGrid":
        return self.translate(delta=Cell(x=0, y=0) - self.tiles[0].as_corners().c1)

    def try_get_tile_by_handle(self, handle: IntHandle) -> Tile | None:
        for tile in self.tiles:
            if tile.handle == handle:
                return tile
        return None

    def get_tile_by_handle(self, handle: IntHandle) -> Tile:
        return_ = self.try_get_tile_by_handle(handle)
        if return_ is None:
            raise ValueError
        return return_

    def try_get_tile_by_cell(self, cell: Cell) -> Tile | None:
        for tile in self.tiles:
            if tile.contains_cell(cell):
                return tile

        return None

    def replace_tiles(self, new: Iterable[Tile]) -> "TileGrid":
        new_ = {t.handle: t for t in new}
        return TileGrid.from_(new_.get(tile.handle, tile) for tile in self.tiles)

    def count_handles(self) -> Counter[IntHandle]:
        return Counter(t.handle for t in self.tiles)

    def get_handle_errors(self) -> dict[IntHandle, int]:
        return {
            handle: count
            for handle, count in self.count_handles().items()
            if count != 1
        }

    def get_overlapping_tile_pairs(self) -> tuple[tuple[Tile, Tile], ...]:
        return_: list[tuple[Tile, Tile]] = []
        for a, b in itertools.combinations(self.tiles, 2):
            if a.intersects_with(b):
                return_.append((a, b))

        return tuple(return_)

    def get_area_mismatch(self) -> int:
        box_area = self.get_box().area()

        tiles_area = 0
        for tile in self.tiles:
            tiles_area += tile.area()

        return box_area - tiles_area

    def get_invariant_errors(self) -> TileGridInvariantErrorContainer:
        return TileGridInvariantErrorContainer(
            handles=self.get_handle_errors(),
            overlapping_tiles=self.get_overlapping_tile_pairs(),
            area_mismatch=self.get_area_mismatch(),
        )

    def assert_invariants(self) -> None:
        invariant_errors = self.get_invariant_errors()
        if invariant_errors.has_errors():
            raise InvariantViolation(f"{invariant_errors=}")

    def rotate_clockwise(self) -> "TileGrid":
        return TileGrid.from_(x.rotate_clockwise() for x in self.tiles)

    def rotate_counterclockwise(self) -> "TileGrid":
        return TileGrid.from_(x.rotate_counterclockwise() for x in self.tiles)

    def rotate(
        self, side: CardinalDirection, /, *, to: CardinalDirection
    ) -> "TileGrid":
        return TileGrid.from_(t.rotate(side, to=to) for t in self.tiles)

    def mirror_horizontally(self) -> "TileGrid":
        return TileGrid.from_(t.mirror_horizontally() for t in self.tiles)

    def mirror_vertically(self) -> "TileGrid":
        return TileGrid.from_(t.mirror_vertically() for t in self.tiles)

    def delete_by_handle(self, handle: IntHandle) -> "TileGrid":
        if self.tiles[0].handle == handle:
            # Origin must not be deleted
            return self

        return TileGrid.from_(t for t in self.tiles if t.handle != handle)

    def compact(self) -> "TileGrid":
        current_grid = self

        box = self.get_box()

        for line in itertools.chain(
            sorted(
                box.shred_horizontally(), key=lambda ln: ln.coordinate, reverse=True
            ),
            sorted(box.shred_vertically(), key=lambda ln: ln.coordinate, reverse=True),
        ):
            delta = {
                Orientation.HORIZONTAL: Cell(x=0, y=-1),
                Orientation.VERTICAL: Cell(x=-1, y=0),
            }[line.orientation]

            new_tiles: list[Tile] = []
            for tile in current_grid.tiles:
                if line.fully_contains_tile(tile):
                    break
                elif not line.intersects_tile(tile):
                    if line.on_positive_side_of_tile(tile):
                        new_tiles.append(tile)
                    elif line.on_negative_side_of_tile(tile):
                        new_tiles.append(
                            tile.replace_tile(
                                TileAsCorners(
                                    c1=tile.as_corners().c1 + delta,
                                    c2=tile.as_corners().c2 + delta,
                                )
                            )
                        )
                else:
                    new_tiles.append(
                        tile.replace_tile(
                            TileAsCorners(
                                c1=tile.as_corners().c1,
                                c2=tile.as_corners().c2 + delta,
                            )
                        )
                    )

            else:  # only executed if the loop did NOT break
                current_grid = TileGrid.from_(new_tiles)

        return current_grid

    def expand(self) -> "TileGrid":
        tiles = tuple(self.tiles)
        box = get_box(tiles)
        new_tiles = list(tiles)
        for i, tile in enumerate(tiles):
            current_tiles = new_tiles[:i] + new_tiles[i + 1 :]

            for new_tile in (
                # Right
                tile.replace_tile(
                    TileAsCorners(
                        c1=tile.as_corners().c1,
                        c2=tile.as_corners().c2 + Cell(x=1, y=0),
                    )
                ),
                # Down
                tile.replace_tile(
                    TileAsCorners(
                        c1=tile.as_corners().c1,
                        c2=tile.as_corners().c2 + Cell(x=0, y=1),
                    )
                ),
                # Left
                tile.replace_tile(
                    TileAsCorners(
                        c1=tile.as_corners().c1 + Cell(x=-1, y=0),
                        c2=tile.as_corners().c2,
                    )
                ),
                # Up
                tile.replace_tile(
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

        return TileGrid.from_(new_tiles)

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
        anchor_tile = self.try_get_tile_by_handle(anchor_handle)
        if anchor_tile is None:
            return self
        # }}}

        new_tiles: list[Tile] = []
        line = Line(
            coordinate=anchor_tile.as_corners().c2.x,
            orientation=Orientation.VERTICAL,
        )
        # Make space (to the RIGHT) {{{
        for tile in self.tiles:
            if tile.handle == anchor_handle:
                new_tiles.append(tile)

            elif (not line.intersects_tile(tile)) and line.on_positive_side_of_tile(
                tile
            ):
                new_tiles.append(tile)
            elif line.intersects_tile(tile):
                new_tiles.append(
                    tile.replace_tile(
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
                    tile.replace_tile(
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

        return TileGrid.from_(new_tiles)

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
        tile = self.try_get_tile_by_handle(tile_handle)
        if tile is None:
            return self
        # }}}

        new_tiles: list[Tile] = []
        for tile in self.tiles:
            corners = tile.as_corners()
            width = corners.c2.x - corners.c1.x

            if (tile.handle != tile_handle) or (width < 2):
                new_tiles.append(tile)
                continue

            c2 = Cell(x=corners.c1.x + (width // 2), y=corners.c2.y)
            c1 = Cell(x=c2.x + 1, y=corners.c1.y)

            new_tiles.extend(
                (
                    tile.replace_tile(
                        TileAsCorners(c1=corners.c1, c2=c2),
                    ),
                    Tile.build(
                        TileAsCorners(c1=c1, c2=corners.c2),
                        handle=new_tile_handle,
                    ),
                )
            )

        return TileGrid.from_(new_tiles)

    def translate(self, *, delta: Cell) -> "TileGrid":
        return TileGrid.from_(tile.translate(delta=delta) for tile in self.tiles)

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

        self.assert_invariants()

        @dataclass(frozen=True, slots=True, kw_only=True)
        class TileVar:
            cell_x: Variable
            span_x: Variable

            cell_y: int
            span_y: int

            handle: IntHandle

        tiles_sorted = tuple(
            sorted(self.tiles, key=lambda tile: tile.as_corners().c1.x)
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
            line = Line(coordinate=y, orientation=Orientation.HORIZONTAL)
            for tile in tiles_sorted:
                if line.intersects_tile(tile):
                    tile_vars_groups[y].append(tile_vars[tile.handle])

        max_tiles = max(len(tiles) for tiles in tile_vars_groups.values())
        # }}}

        solver = Solver()

        for tile_var in tile_vars.values():
            solver.addConstraint(tile_var.span_x >= 1)
            solver.addConstraint(tile_var.span_x <= x_length_new)

            match mode:
                case "scale":
                    # Scaling {{{

                    # span_x_new   x_length_new
                    # ---------- = ------------
                    # span_x_old   x_length_old

                    # span_x_new = (span_x_old * x_length_new) / x_length_old

                    a = self.try_get_tile_by_handle(tile_var.handle)
                    if a is None:
                        raise Unreachable

                    solver.addConstraint(
                        tile_var.span_x
                        >= (
                            (a.as_span().span.x * x_length_new)
                            // self.get_box().as_span().span.x
                        )
                    )
                    # }}}
                case "balance":
                    # Balancing {{{
                    solver.addConstraint(tile_var.span_x >= (x_length_new // max_tiles))
                    # }}}

        # Position constraints {{{
        for tile_vars_group in tile_vars_groups.values():
            # Span constraints {{{
            expression: Expression | Variable = tile_vars_group[0].span_x
            for tile_var in tile_vars_group[1:]:
                expression += tile_var.span_x

            solver.addConstraint(expression == x_length_new)
            # }}}

            # Cell constraints {{{
            if len(tile_vars_group) > 0:
                # Don't let rows of tiles slide out of the box
                solver.addConstraint(tile_vars_group[0].cell_x == 0)

            for i in range(1, len(tile_vars_group)):
                previous_tile, tile_var = tile_vars_group[i - 1], tile_vars_group[i]
                solver.addConstraint(
                    tile_var.cell_x == (previous_tile.cell_x + previous_tile.span_x)
                )
            # }}}

        # }}}

        solver.updateVariables()
        return TileGrid.from_(
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
            for tile_var in (tile_vars[tile.handle] for tile in self.tiles)
        )

    def get_ys(self) -> set[int]:
        return get_ys(self.tiles)

    def un_occupy(self, area: "Tile", /, *, prefer: "Orientation") -> "TileGrid | None":
        tiles: list[Tile] = []
        for tile in self.tiles:
            processed_tile = tile.un_occupy(area, prefer=prefer)
            if processed_tile is None:
                return None
            tiles.append(processed_tile)

        return TileGrid.from_(tiles)

    def align_borders(self, *, proximity: int = 1) -> "TileGrid":
        assert proximity >= 0, f"{proximity=}, expected `proximity >= 0`"

        return (
            self.align_right_borders_to_right(proximity=proximity)
            .mirror_horizontally()
            .align_right_borders_to_right(proximity=proximity)
            .mirror_vertically()
            .align_right_borders_to_right(proximity=proximity)
            .mirror_horizontally()
            .align_right_borders_to_right(proximity=proximity)
            .mirror_vertically()
            .rotate_clockwise()
            .align_right_borders_to_right(proximity=proximity)
            .mirror_horizontally()
            .align_right_borders_to_right(proximity=proximity)
            .mirror_vertically()
            .align_right_borders_to_right(proximity=proximity)
            .mirror_horizontally()
            .align_right_borders_to_right(proximity=proximity)
            .mirror_vertically()
            .rotate_counterclockwise()
        )

    def align_right_borders_to_right(self, *, proximity: int = 1) -> "TileGrid":
        assert proximity >= 0, f"{proximity=}, expected `proximity >= 0`"

        curr = self
        for tile in self.tiles:
            curr = curr.align_below_tile_right_border_to_right(
                handle=tile.handle, proximity=proximity
            )

        return curr

    def align_below_tile_right_border_to_right(
        self, *, handle: IntHandle, proximity: int = 1
    ) -> "TileGrid":
        assert proximity >= 0, f"{proximity=}, expected `proximity >= 0`"

        tile = self.get_tile_by_handle(handle)
        tc = tile.as_corners()

        max_x: int | None = None
        tile_2: Tile | None = None
        for t2 in self.tiles:
            tc2 = t2.as_corners()
            if (
                (tc2.c1.y == tc.c2.y + 1)
                and (tc.c2.x >= tc2.c2.x)
                and (tc.c1.x <= tc2.c2.x)
                and ((tc.c2.x - tc2.c2.x) <= proximity)
                and ((max_x is None) or (tc2.c2.x > max_x))
            ):
                max_x = tc2.c2.x
                tile_2 = t2

        if tile_2 is None:
            return self

        delta_x = tc.c2.x - tile_2.as_corners().c2.x
        shared_borders = self.get_longest_vertical_right_border(tile_2.handle)
        return self.replace_tiles(
            itertools.chain(
                (t.corners_c2_add(Cell(delta_x, 0)) for t in shared_borders.left),
                (t.corners_c1_add(Cell(delta_x, 0)) for t in shared_borders.right),
            )
        )

    def get_vertical_right_border(
        self, handle: IntHandle, *, mode: BorderMode
    ) -> SharedBorders:
        match mode:
            case BorderMode.SHORTEST:
                return self.get_shortest_vertical_right_border(handle)
            case BorderMode.LONGEST:
                return self.get_longest_vertical_right_border(handle)

    def get_shortest_vertical_right_border(self, handle: IntHandle) -> SharedBorders:
        tile = self.get_tile_by_handle(handle)
        tc = tile.as_corners()
        tiles = self.tiles

        possible_left = [t for t in tiles if tc.c2.x == t.as_corners().c2.x]
        possible_right = [t for t in tiles if tc.c2.x + 1 == t.as_corners().c1.x]

        if not possible_right:
            return SharedBorders(left=frozenset(possible_left), right=frozenset())

        y_min: int = tc.c1.y
        y_max: int = tc.c2.y

        left_and_right_swapped: bool = False
        tiles_left: set[Tile] = {tile}
        tiles_right: set[Tile] = set()
        while True:
            detector = Tile.build(
                TileAsCorners(
                    Cell(x=tc.c2.x, y=y_min),
                    Cell(x=tc.c2.x + 1, y=y_max),
                )
            )
            for tile_right in possible_right:
                if tile_right.intersection(detector) is not None:
                    tiles_right.add(tile_right)

            new_y_min = min(t.as_corners().c1.y for t in tiles_right)
            new_y_max = max(t.as_corners().c2.y for t in tiles_right)

            if (new_y_min, new_y_max) == (y_min, y_max):
                break

            y_min, y_max = new_y_min, new_y_max

            tiles_left, tiles_right = tiles_right, tiles_left
            possible_left, possible_right = possible_right, possible_left
            left_and_right_swapped = not left_and_right_swapped

        if left_and_right_swapped:
            tiles_left, tiles_right = tiles_right, tiles_left

        return SharedBorders(left=frozenset(tiles_left), right=frozenset(tiles_right))

    def get_longest_vertical_right_border(self, handle: IntHandle) -> SharedBorders:
        shared_borders = self.get_shortest_vertical_right_border(handle)

        while True:
            a = min(shared_borders.left, key=lambda t: t.as_corners().c1.y)
            b = max(shared_borders.left, key=lambda t: t.as_corners().c2.y)

            break_ = True
            for tile in self.tiles:
                if (tile.corner_cells()[3] == (a.corner_cells()[1] + Cell(0, -1))) or (
                    tile.corner_cells()[1] == (b.corner_cells()[3] + Cell(0, 1))
                ):
                    break_ = False
                    left_right = self.get_shortest_vertical_right_border(tile.handle)
                    shared_borders = SharedBorders(
                        left=shared_borders.left | left_right.left,
                        right=shared_borders.right | left_right.right,
                    )

            if break_:
                break

        return SharedBorders(left=shared_borders.left, right=shared_borders.right)

    def get_shared_borders_near(
        self,
        cell: Cell,
        *,
        proximity: int = 1,
        mode: BorderMode,
        ignore_plus: bool = False,
    ) -> SharedBorders:
        tile = self.try_get_tile_by_cell(cell)
        if tile is None:
            return SharedBorders.empty()

        grid = self
        cc = tile.corner_cells()

        closest_edge = closest(
            to=cell.x, out_of=(cc[0].x, cc[1].x + 1), proximity=proximity
        )
        if closest_edge is None:
            vertical_borders = SharedBorders.empty()
        elif cell.x < closest_edge:
            vertical_borders = grid.get_vertical_right_border(tile.handle, mode=mode)
        else:
            new_tile = grid.try_get_tile_by_cell(Cell(cc[0].x - 1, cell.y))
            if new_tile is None:
                vertical_borders = SharedBorders.empty()
            else:
                vertical_borders = grid.get_vertical_right_border(
                    new_tile.handle, mode=mode
                )

        cell = cell.rotate_counterclockwise()
        tile = tile.rotate_counterclockwise()
        grid = grid.rotate_counterclockwise()
        cc = tile.corner_cells()

        closest_edge = closest(
            to=cell.x, out_of=(cc[0].x, cc[1].x + 1), proximity=proximity
        )
        if closest_edge is None:
            horizontal_borders = SharedBorders.empty()
        elif cell.x < closest_edge:
            horizontal_borders = grid.get_vertical_right_border(tile.handle, mode=mode)
        else:
            new_tile = grid.try_get_tile_by_cell(Cell(cc[0].x - 1, cell.y))
            if new_tile is None:
                horizontal_borders = SharedBorders.empty()
            else:
                horizontal_borders = grid.get_vertical_right_border(
                    new_tile.handle, mode=mode
                )

        shared_borders = SharedBorders(
            left=vertical_borders.left,
            right=vertical_borders.right,
            # Rotated counterclockwise before
            top=horizontal_borders.left,
            bottom=horizontal_borders.right,
        ).pull_coords(self)

        if ignore_plus or (mode == BorderMode.LONGEST):
            return shared_borders

        vertical, horizontal = shared_borders.as_tiles()
        if (vertical is None) or (horizontal is None):
            return shared_borders

        vertical = vertical.corners_c2_add(Cell(0, 1))
        horizontal = horizontal.corners_c2_add(Cell(1, 0))

        v1, v2 = vertical.corner_cells()[0:3:2]
        h1, h2 = horizontal.corner_cells()[0:2]

        if not (v1 == h1 or v1 == h2 or v2 == h1 or v2 == h2):
            return shared_borders

        delta = Cell(
            x=-1 if h1 in (v1, v2) else 1,
            y=-1 if v1 in (h1, h2) else 1,
        )

        intersection = vertical.intersection(horizontal)
        if intersection is None:
            raise Unreachable

        new_base_cell = intersection.as_corners().c1 + delta

        return self.get_shared_borders_near(
            new_base_cell,
            proximity=proximity,
            mode=BorderMode.SHORTEST,
            ignore_plus=True,
        ).union(shared_borders)


def closest(*, to: int, out_of: Iterable[int], proximity: int) -> int | None:
    number, distance = min(
        ((n, abs(n - to)) for n in out_of),
        key=lambda a: a[1],
    )

    return None if distance > proximity else number


# Line {{{


class Orientation(Enum):
    HORIZONTAL = auto()
    VERTICAL = auto()

    def invert(self) -> "Orientation":
        return (
            Orientation.VERTICAL
            if self == Orientation.HORIZONTAL
            else Orientation.HORIZONTAL
        )


@dataclass(frozen=True, slots=True, kw_only=True)
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
