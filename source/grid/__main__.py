from .graphics import main


main()


# def temp() -> None:
#     from .model import Cell, TileCorners, TileSpan, get_box_corners

#     origin = TileSpan(
#         cell=Cell(x=0, y=0),
#         span=Cell(x=0, y=0),
#     )

#     tiles: list[TileSpan] = [
#         origin,
#         TileSpan(
#             cell=Cell(x=1, y=0),
#             span=Cell(x=1, y=0),
#         ),
#         TileSpan(
#             cell=Cell(x=-1, y=-1),
#             span=Cell(x=0, y=-1),
#         ),
#     ]

#     print(origin)

#     print(
#         get_box_corners(
#             tuple(tile.as_corners() for tile in tiles),
#         )
#     )

#     print(
#         TileCorners(
#             c1=Cell(x=2, y=3),
#             c2=Cell(x=4, y=-5),
#         ).normalize()
#     )
