import math


# Unit parameters:
PLAYER_UNIT_IMAGE_PATH = './assets/unit_player.png'
ENEMY_UNIT_IMAGE_PATH = './assets/unit_enemy.png'
CURRENT_PLAYER_UNIT_IMAGE_PATH = './assets/current_unit_player.png'
CURRENT_ENEMY_UNIT_IMAGE_PATH = './assets/current_unit_enemy.png'

# Hexagon parameters:
HEX_IMAGE_PATH = './assets/hexagon.png'
CURRENT_HEX_IMAGE_PATH = './assets/hexagon_current.png'
OCCUPIED_HEX_IMAGE_PATH = './assets/hexagon_occupied.png'
HEX_EDGE = 27
HEX_WIDTH = 2.0 * HEX_EDGE
HEX_HEIGHT = math.sqrt(3.0) * HEX_EDGE
HEX_EDGES = {
	1: (-1, 1, 0),
	2: (0, 1, -1),
	3: (1, 0, -1),
	4: (1, -1, 0),
	5: (0, -1, 1),
	6: (-1, 0, 1)
}

# Game window parameters:
WINDOW_HEIGHT = 600
WINDOW_WIDTH = 800
WINDOW_SIZE = (WINDOW_WIDTH, WINDOW_HEIGHT)
WINDOW_NAME = 'Necromancer'
WINDOW_BACKGROUND_COLOR = (50, 60, 57)

# Game configs:
from shapes import Hexagon

GRID = []
for col in range(19):
	for row in range(12):
		GRID.append(Hexagon(col, row))

PLAYER_ARMY = (
	(3, 2, (0, 1)),
	(3, 2, (0, 2)),
	(4, 1, (0, 3)),
	(4, 1, (0, 4)),
	(1, 3, (0, 5)),
)

ENEMY_ARMY = (
	(3, 2, (9, 1)),
	(3, 2, (9, 2)),
	(4, 1, (8, 4)),
	(4, 1, (9, 4)),
	(1, 3, (8, 5)),
)
