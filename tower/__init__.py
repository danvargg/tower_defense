"""Game constants."""
from pygame import Rect as pg_rect

VERSION = '0.0.1'

WIDTH = 960
HEIGHT = 540
SCREEN_RECT = pg_rect(0, 0, WIDTH, HEIGHT)  # FIXME: (0, 0) magic numbers

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
