"""Game constants."""
import pygame as pg  # TODO: move to constants to avoid import?

VERSION = '0.0.1'

WIDTH = 960
HEIGHT = 540
SCREEN_RECT = pg.Rect(0, 0, WIDTH, HEIGHT)  # FIXME: (0, 0) magic numbers

DESIRED_FPS = 60
IMAGE_SPRITES = {
    "game_logo": "game_logo.png",
    "land": "land.png",
    "road": "road.png",
}

CHANNELS = {
    "footsteps": None,
    "turrets": None,
    "score": None,
}
