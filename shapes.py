from dataclasses import dataclass, field, InitVar

from config.config import HEX_EDGE, HEX_WIDTH, HEX_HEIGHT


@dataclass(slots=True)
class Hexagon:
	col: InitVar[int]
	row: InitVar[int]
	_x: float = field(init=False, repr=True)
	_y: float = field(init=False, repr=True)
	position: tuple[int, int] = field(init=False, repr=True)
	cube: tuple[int, int, int] = field(init=False, repr=True)

	def __post_init__(self, col: int, row: int):
		self.position = (col, row)

		x = col - (row - (row & 1)) // 2
		z = row
		y = -x - z
		self.cube = (x, y, z)

		self._x = self.x
		self._y = self.y

	@property
	def x(self):
		return self.position[0] * HEX_WIDTH * 3 / 4 + HEX_EDGE

	@property
	def y(self):
		return self.position[1] * HEX_HEIGHT + (self.position[0] & 1) * HEX_HEIGHT / 2 + HEX_EDGE
