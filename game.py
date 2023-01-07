import pygame

from config.config import WINDOW_SIZE, WINDOW_NAME
from core import ECSCore


class Game:
	def __init__(self):
		if not pygame.image.get_extended():
			raise 'image format error'

		# pygame core init:
		pygame.init()
		pygame.fastevent.init()

		while not pygame.fastevent.get_init() or not pygame.get_init():
			pass

		# create pygame clock:
		self.clock = pygame.time.Clock()

		# create game window:
		pygame.display.set_caption(WINDOW_NAME)
		self.window = pygame.display.set_mode(WINDOW_SIZE)

		# create ECS core of the game
		self.ecs_core = ECSCore(self.window)

	def start(self):
		while True:
			self.ecs_core.game_loop()


if __name__ == '__main__':
	Game().start()
