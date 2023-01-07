import math

from dataclasses import dataclass, field


@dataclass
class Orders:
	__slots__ = {
		'HEX_EDGES': (
			(-1, 1, 0),
			(0, 1, -1),
			(1, 0, -1),
			(1, -1, 0),
			(0, -1, 1),
			(-1, 0, 1)
		)
	}
	HEX_EDGES: tuple


@dataclass
class Sizes:
	__slots__ = {
		'HEX_EDGE': 4.0,
		'HEX_WIDTH': None,
		'HEX_HEIGHT': None
	}
	HEX_EDGE: float
	HEX_WIDTH: float = field(init=False, repr=True)
	HEX_HEIGHT: float = field(init=False, repr=True)

	def __post_init__(self):
		self.HEX_HEIGHT = math.sqrt(3.0) * self.HEX_EDGE
		self.HEX_WIDTH = 2.0 * self.HEX_EDGE
