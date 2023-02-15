"""Utility functions."""
from pygame import Surface, SRCALPHA

from tower import SCREEN_RECT


def create_surface(size=SCREEN_RECT.size, flags=SRCALPHA):
    """
    Creates a surface of `size`, which defaults to the screen
    rectangle size, with `flags`. Which by default includes alpha
    blending support.
    """
    return Surface(size, flags=flags)
