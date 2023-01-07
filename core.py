import pygame
import esper
import sys

from dataclasses import dataclass as component, field
from shapes import Hexagon
from config.config import (
	CURRENT_ENEMY_UNIT_IMAGE_PATH,
	CURRENT_PLAYER_UNIT_IMAGE_PATH,
	PLAYER_UNIT_IMAGE_PATH,
	ENEMY_UNIT_IMAGE_PATH,
	OCCUPIED_HEX_IMAGE_PATH,
	WINDOW_BACKGROUND_COLOR,
	CURRENT_HEX_IMAGE_PATH,
	HEX_IMAGE_PATH,
	HEX_HEIGHT,
	PLAYER_ARMY,
	ENEMY_ARMY,
	GRID,
)


# Components:
# -----------

# components for UNITS:
@component(slots=True)
class Mobile:
	"""Component for mobile units only"""
	max_movement_points: int
	current_movement_points: int = field(init=False, repr=True)

	def __post_init__(self):
		self.current_movement_points = self.max_movement_points


@component(slots=True)
class Combatant:
	"""Component for units that can fight"""
	power: int
	is_fresh: bool = True


@component(slots=True)
class OccupiedHexagon:
	"""Component of a unit that stores the hexagon on which the unit stands"""
	hexagon: int    # entity


# components for hexagons (tiles, MAP):
@component(slots=True)
class Space:
	"""A component for place where unit can stand"""
	image: pygame.Surface
	is_occupied: bool = False


@component(slots=True)
class Occupied:
	"""Component for occupied hexagons (by units or terrain)"""


@component(slots=True)
class Reachable:
	"""Component for hexagon that reachable for selected unit"""


# ABSTRACT components:
@component(slots=True)
class Shape:
	"""Component for a game entity shape"""
	shape: ...


@component(slots=True)
class Renderable:
	"""A component for game entities that has an image on the game screen"""
	image: pygame.Surface
	_current_image: pygame.Surface
	pos_x: float
	pos_y: float

	@property
	def current_image(self):
		return self._current_image

	@current_image.setter
	def current_image(self, image):
		self._current_image = image

	def restore_image(self):
		self._current_image = self.image


@component(slots=True)
class Collidable:
	"""A component for game entities that can collide"""
	image: pygame.Surface


@component(slots=True)
class Selected:
	"""A component for selected unit"""


@component(slots=True)
class Current:
	"""A component for the current entity under mouse cursor, such as hexagon, unit or UI element"""
	...


@component(slots=True)
class Pressable:
	"""A component for UI elements like buttons"""
	...


# Processors / Systems:
# ---------------------
class RenderProcessor(esper.Processor):
	def __init__(self, window: pygame.Surface, clear_color=(0, 0, 0)):
		super().__init__()
		self.window = window
		self.clear_color = clear_color

	def process(self):
		self.window.fill(self.clear_color)

		# This will iterate over every Entity that has this Component, and blit it:
		for _, rend in self.world.get_component(Renderable):
			self.window.blit(rend.current_image, (rend.pos_x, rend.pos_y))

		pygame.display.flip()


class CollisionProcessor(esper.Processor):
	def __init__(self, point: tuple[int, int]):
		super().__init__()
		self.point = point

	def process(self):
		for entity, _ in self.world.get_component(Collidable):
			if not self._is_point_inside_collidable_entity(entity):
				if not self.world.has_component(entity, Current):
					continue
				self.world.remove_component(entity, Current)
				if not self.world.has_component(entity, Selected):
					self.world.component_for_entity(entity, Renderable).restore_image()
				continue
			image = self.world.component_for_entity(entity, Collidable).image
			self.world.component_for_entity(entity, Renderable).current_image = image
			self.world.add_component(entity, Current())

	def _is_point_inside_collidable_entity(self, entity: int) -> bool:
		if isinstance(self.world.component_for_entity(entity, Shape).shape, Hexagon):
			return self._is_point_inside_hexagon(entity)
		rectangle = self.world.component_for_entity(entity, Shape).shape
		return rectangle.collidepoint(self.point)

	def _is_point_inside_hexagon(self, entity):
		hexagon = self.world.component_for_entity(entity, Shape).shape
		dx = abs(hexagon.x - self.point[0]) / HEX_HEIGHT
		dy = abs(hexagon.y - self.point[1]) / HEX_HEIGHT
		return dy <= 0.55 and (0.55 * dx + 0.255 * dy) <= 0.2855


class SelectionProcessor(esper.Processor):
	def __init__(self):
		super().__init__()
		self.lkm_is_pressed: bool = False
		self.selected_unit = None
		self.selected_hexagon = None

	def process(self):
		self._entity_based_process(Combatant)
		self._entity_based_process(Space)

	def _entity_based_process(self, cmp):
		if not self.lkm_is_pressed:
			return

		is_unit = cmp == Combatant

		for entity, _ in self.world.get_component(Current):
			img = self.world.component_for_entity(entity, Collidable).image

			if self.world.has_component(entity, cmp):
				self.world.add_component(entity, Selected())
				self.world.component_for_entity(entity, Renderable).current_image = img
				if is_unit:
					if self.selected_unit and self.selected_unit != entity:
						self.world.remove_component(self.selected_unit, Selected)
						self.world.component_for_entity(self.selected_unit, Renderable).restore_image()
					self.selected_unit = entity
					self.unselect_hexagon()
				else:
					if self.selected_hexagon and self.selected_hexagon != entity:
						self.unselect_hexagon()
					self.selected_hexagon = entity

					position = self.world.component_for_entity(entity, Shape).shape.position
					cube = self.world.component_for_entity(entity, Shape).shape.cube
					print(f'hexagon position - {position}, cube - {cube}')

				self.lkm_is_pressed = False
				print(f'{entity} - {"unit" if is_unit else "hexagon"} are selected')

	def unselect_hexagon(self):
		if not self.selected_hexagon:
			return
		self.world.remove_component(self.selected_hexagon, Selected)
		self.world.component_for_entity(self.selected_hexagon, Renderable).restore_image()
		self.selected_hexagon = None


class OccupationProcess(esper.Processor):
	def __init__(self):
		super().__init__()

	def process(self):
		for entity, comp in self.world.get_component(Space):
			if comp.is_occupied:
				self.world.component_for_entity(entity, Renderable).image = comp.image
			else:
				self.world.component_for_entity(entity, Renderable).restore_image()


class MovementProcessor(esper.Processor):
	def __init__(self, unit_width, game_map):
		super().__init__()
		self.unit_width = unit_width
		self.map = game_map

	def process(self):
		unit = self.world.get_processor(SelectionProcessor).selected_unit
		hexagon = self.world.get_processor(SelectionProcessor).selected_hexagon

		if unit and hexagon and self.is_movement_possible(unit, hexagon):
			target_x = self.world.component_for_entity(hexagon, Renderable).pos_x - self.unit_width / 2.8
			target_y = self.world.component_for_entity(hexagon, Renderable).pos_y - self.unit_width / 2.1
			self.world.component_for_entity(unit, Renderable).pos_x = target_x
			self.world.component_for_entity(unit, Renderable).pos_y = target_y
			self.world.component_for_entity(unit, Shape).shape = pygame.Rect(
				(target_x, target_y), (self.unit_width, self.unit_width)
			)
			unit_hexagon = self.world.component_for_entity(unit, OccupiedHexagon).hexagon
			self.world.component_for_entity(unit_hexagon, Space).is_occupied = False
			self.world.component_for_entity(hexagon, Space).is_occupied = True

	def is_movement_possible(self, unit, hexagon) -> bool:
		# target hexagon is reachable
		unit_hex = self.world.component_for_entity(unit, OccupiedHexagon).hexagon
		mp = self.world.component_for_entity(unit, Mobile).current_movement_points
		return hexagon in self.reachable_hexagons(unit_hex, mp)

	def reachable_hexagons(self, start_hexagon: Hexagon, movement: int) -> list[Hexagon, ...]:
		hexagons = set()
		hexagons.add(start_hexagon)
		neighbors = [[start_hexagon]]

		for i in range(1, movement + 1):
			neighbors.append([])
			for hexagon in neighbors[i - 1]:
				for neighbor in self.get_adjacent_hexagons(hexagon):
					if neighbor not in hexagons and not self.world.component_for_entity(neighbor, Space).is_occupied:
						hexagons.add(neighbor)
						neighbors[i].append(neighbor)
		return list(hexagons)

	def get_adjacent_hexagons(self, hexagon):
		neighbors = []
		pos = self.world.component_for_entity(hexagon, Shape).shape.position
		offsets = ((-1, -1), (0, 1), (1, -1), (1, 0), (0, 1), (-1, 0))
		for offset in offsets:
			try:
				neighbor = self.map[(pos[0] - offset[0], pos[1] - offset[1])]
			except KeyError:
				continue
			neighbors.append(neighbor)
		return neighbors

	def get_distance_between_hexagons(self, hex_1, hex_2):
		pos_1 = self.world.component_for_entity(hex_1, Shape).shape.position
		pos_2 = self.world.component_for_entity(hex_2, Shape).shape.position
		coordinates = []
		for i in range(2):
			coordinates.append(abs(pos_1[i] - pos_2[i]))
		return max(*coordinates)

	def get_hexagons_line(self, hex_1, hex_2):
		length = self.get_distance_between_hexagons(hex_1, hex_2)
		line = []
		for i in range(length):
			line.append(self.map[(
				self.lerp_point(
					self.world.component_for_entity(hex_1, Shape).shape.position,
					self.world.component_for_entity(hex_2, Shape).shape.position,
					i
				)
			)])
		return line

	def lerp_point(self, p0, p1, t):
		return (
			self.lerp(p0.x, p1.x, t),
			self.lerp(p0.y, p1.y, t)
		)

	@staticmethod
	def lerp(start, end, t):
		return start * (1.0 - t) + t * end


# Core of the game
class ECSCore:
	"""Core of the game"""
	def __init__(self, window: pygame.Surface):
		# ECS world init:
		self.world = esper.World()

		# Pygame images:
		self.images = {}
		self._fill_images_dict()

		self.unit_width = self.images['player_unit_image'].get_width()

		# Containers:
		self.player_army = []
		self.enemy_army = []
		self.map = {}

		# Entities:
		self._add_hexagons_to_map()
		self._add_map_components()
		self._add_units_to_army(
			self.player_army,
			PLAYER_ARMY,
			self.images['player_unit_image'],
			self.images['current_player_unit_image']
		)
		self._add_units_to_army(
			self.enemy_army,
			ENEMY_ARMY,
			self.images['enemy_unit_image'],
			self.images['current_enemy_unit_image']
		)

		# Processors:
		self.world.add_processor(OccupationProcess())
		self.world.add_processor(RenderProcessor(window=window, clear_color=WINDOW_BACKGROUND_COLOR))
		self.world.add_processor(CollisionProcessor(pygame.mouse.get_pos()))
		self.world.add_processor(SelectionProcessor())
		self.world.add_processor(MovementProcessor(self.unit_width, self.map))

	def _add_units_to_army(self, container: list, army: tuple, image: pygame.Surface, curr_img: pygame.Surface):
		for unit in army:
			x = self.world.component_for_entity(self.map[unit[2]], Shape).shape.x - self.unit_width / 2.8
			y = self.world.component_for_entity(self.map[unit[2]], Shape).shape.y - self.unit_width / 2.1

			container.append(
				self.world.create_entity(
					Shape(pygame.Rect((x, y), (self.unit_width, self.unit_width))),
					Renderable(
						image=image,
						_current_image=image,
						pos_x=x,
						pos_y=y
					),
					Collidable(curr_img),
					Mobile(unit[1]),
					Combatant(unit[0]),
					OccupiedHexagon(self.map[unit[2]])
				)
			)
			self.world.component_for_entity(self.map[unit[2]], Space).is_occupied = True

	def _add_map_components(self):
		for key in self.map.keys():
			self.world.add_component(
				self.map[key],
				Renderable(
					image=self.images['hex_image'],
					_current_image=self.images['hex_image'],
					pos_x=self.world.component_for_entity(self.map[key], Shape).shape.x,
					pos_y=self.world.component_for_entity(self.map[key], Shape).shape.y
				)
			)
			self.world.add_component(
				self.map[key],
				Collidable(image=self.images['current_hex_image'])
			)
			self.world.add_component(
				self.map[key],
				Space(self.images['occupied_hex_image'])
			)

	def _add_hexagons_to_map(self):
		for hexagon in GRID:
			self.map[hexagon.position] = self.world.create_entity(Shape(hexagon))

	def game_loop(self):
		self.world.process()
		self.pygame_events_loop()

	def pygame_events_loop(self):
		for event in pygame.fastevent.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit(0)
			elif event.type == pygame.MOUSEMOTION:
				self.world.get_processor(CollisionProcessor).point = pygame.mouse.get_pos()
			elif event.type == pygame.MOUSEBUTTONDOWN:
				self.world.get_processor(SelectionProcessor).lkm_is_pressed = pygame.mouse.get_pressed(3)[0]

	def _fill_images_dict(self):
		self.images['hex_image'] = pygame.image.load(HEX_IMAGE_PATH).convert_alpha()
		self.images['current_hex_image'] = pygame.image.load(CURRENT_HEX_IMAGE_PATH).convert_alpha()
		self.images['player_unit_image'] = pygame.image.load(PLAYER_UNIT_IMAGE_PATH).convert_alpha()
		self.images['current_player_unit_image'] = pygame.image.load(CURRENT_PLAYER_UNIT_IMAGE_PATH).convert_alpha()
		self.images['enemy_unit_image'] = pygame.image.load(ENEMY_UNIT_IMAGE_PATH).convert_alpha()
		self.images['current_enemy_unit_image'] = pygame.image.load(CURRENT_ENEMY_UNIT_IMAGE_PATH).convert_alpha()
		self.images['occupied_hex_image'] = pygame.image.load(OCCUPIED_HEX_IMAGE_PATH).convert_alpha()
