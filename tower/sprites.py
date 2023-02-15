"""Game sprites."""
from __future__ import annotations
import enum

from pygame import sprite, mask, transform
from pygame.math import Vector2 as Vector

from tower import IMAGE_SPRITES, CACHE

import enum
import operator
import random
from dataclasses import dataclass, field
from itertools import accumulate, chain, cycle, repeat, count
from typing import Generator, Optional, Dict
from structlog import get_logger
from pygame.math import Vector2 as Vector

from tower import (
    ALLOWED_BG_SPRITES,
    ALLOWED_SHRUBS,
    CACHE,
    FONT_NAME,
    IMAGE_SPRITES,
    ANIMATIONS,
    SOUND_FOOTSTEPS,
    SOUND_TURRET,
    SOUNDS,
    TILE_HEIGHT,
    TILE_WIDTH,
    VISION_RECT,
)
from tower.utils import create_surface, extend, interpolate

log = get_logger()


class AnimationState(enum.Enum):

    """
    Possible animation states for a sprite
    """

    stopped = "stopped"
    # for enemies
    walking = "walking"
    dying = "dying"
    # for projectiles
    exploding = "exploding"

    @classmethod
    def state_kills_sprite(cls, state):
        """
        Return True if, upon reaching the end of an animation for
        `state`, if the sprite should be killed.

        This is useful if you want to run an animation until it
        expires (like a dying animation) and then have the animation
        routine auto-kill the sprite.

        This, of course, will not trigger for animation generators
        that never cause a `StopIteration`, nor for sprites where this
        not desired, even if the animation is finite.
        """
        return state in (cls.exploding, cls.dying)


class SpriteState(enum.Enum):

    """
    Possible states for movable sprites (like enemies)
    """

    unknown = "unknown"
    moving = "moving"
    stopped = "stopped"


class Layer(enum.IntEnum):

    """
    Enum of all possible layers you can assign a sprite. Note the
    numbered ordering: lower numbers are drawn _before_ higher
    numbers.
    """

    background = 0
    decal = 10
    turret = 20
    turret_sights = 21
    shrub = 25
    enemy = 30
    projectile = 40
    hud = 60


class Sprite(sprite.Sprite):
    """
    Base class for sprites.
    """

    # The layer the sprite is drawn against. By default it's the background.
    _layer = Layer.background

    @classmethod
    def create_from_sprite(
        cls,
        index,
        groups,
        sounds=None,
        image_tiles=IMAGE_SPRITES,
        orientation=0,
        flipped_x=False,
        flipped_y=False,
        **kwargs,
    ):
        """
        Class method that creates a sprite from a tileset, by
        default `IMAGE_SPRITES`.
        """
        image = image_tiles[(flipped_x, flipped_y, index)]
        rect = image.get_rect()
        return cls(
            image=image,
            image_tiles=image_tiles,
            index=index,
            groups=groups,
            sounds=sounds,
            rect=rect,
            orientation=orientation,
            **kwargs,
        )

    @classmethod
    def create_from_surface(cls, groups, surface, sounds=None, orientation=0, **kwargs):
        """
        Class method that creates a sprite from surface.
        """
        rect = surface.get_rect()
        return cls(
            groups=groups,
            image=surface,
            index=None,
            sounds=sounds,
            rect=rect,
            orientation=orientation,
            **kwargs,
        )

    def __init__(
        self,
        groups,
        image_tiles=None,
        index=None,
        rect=None,
        sounds=None,
        channel=None,
        image=None,
        frames=None,
        animation_state=AnimationState.stopped,
        position=(0, 0),
        orientation=0,
        flipped_x=False,
        flipped_y=False,
    ):
        """
        Traditional constructor for the `pg.sprite.Sprite` class,
        as it does not (easily) support dataclasses.
        """
        super().__init__(groups)
        self.image = image
        self.image_tiles = image_tiles
        self.index = index
        self.rect = rect
        self.frames = frames
        self.sounds = sounds
        self.orientation = orientation
        self.channel = channel
        self.animation_state = animation_state
        self.sprite_offset = Vector(0, 0)
        self.angle = self.generate_rotation()
        self._last_angle = None
        self.flipped_x = flipped_x
        self.flipped_y = flipped_y
        if self.image is not None:
            self.mask = pg.mask.from_surface(self.image)
            self.surface = self.image.copy()
            self.rotate(self.orientation)
        if self.rect is not None and position is not None:
            self.move(position)

    def move(self, position, center: bool = True):
        """
        Moves the sprite by changing the position of the
        rectangle. By default it moves the center; otherwise, the top
        left.
        """
        assert self.rect is not None, "No rect!"
        if center:
            self.rect.center = position
        else:
            self.rect.topleft = position

    def rotate_cache_key(self):
        """
        Returns a tuple of fields used as a cache key to speed up rotations
        """
        return (self.flipped_x, self.flipped_y, self.index)

    def rotate(self, angle):
        """
        Rotates the sprite and regenerates its mask.
        """
        # Do not rotate if the desired angle is the same as the last
        # angle we rotated to.
        if angle == self._last_angle:
            return
        try:
            k = (self.rotate_cache_key(), angle)
            new_image = CACHE[k]
        except KeyError:
            new_image = pg.transform.rotate(self.surface, angle % 360)
            CACHE[k] = new_image
        new_rect = new_image.get_rect(center=self.rect.center)
        self.image = new_image
        self.rect = new_rect
        self.mask = pg.mask.from_surface(self.image)
        self._last_angle = angle

    def generate_rotation(self):
        """
        Repeats the sprite's default orientation forever.

        This is typically done only for sprites with a fixed
        orientation that never changes.
        """
        return repeat(self.orientation)

    def set_orientation(self, orientation):
        """
        Updates the orientation to `orientation`.
        """
        self.orientation = orientation
        self.angle = self.generate_rotation()
        self.rotate(next(self.angle))

    def update(self):
        """
        Called by the game loop every frame.
        """
        angle = next(self.angle)
        self.rotate(angle)
        self.animate()

    def animate(self):
        # If we're called upon to animate, we must have frames that we
        # can animate. If not, we do nothing.
        if self.frames is not None:
            # Given out animation state, determine the roll of
            # animation frames to use. For instance, dying is a
            # different set of animations than what we'd use when
            # we're moving
            roll = self.frames[self.animation_state]
            if roll is not None:
                try:
                    # Because roll is a generator, we request the next
                    # frame. But! It's possible there is no next
                    # frame: we may have a finite number of frames
                    # (like dying) as opposed to infinite frames (like
                    # a walking animation)
                    next_frame_index = next(roll)
                    if next_frame_index != self.index:
                        self.set_sprite_index(next_frame_index)
                except StopIteration:
                    # When you exhaust a generator it raises
                    # `StopIteration`. We catch the exception and ask
                    # the Animation system if our animation state, now
                    # that we've run out of animations to play,
                    # results in the sprite dying.
                    if AnimationState.state_kills_sprite(self.animation_state):
                        self.kill()
                    # Regardless, we stop our animation state at this point.
                    self.animation_state = AnimationState.stopped

    def play(self):
        """
        Plays a sound if there is a sound generator attached; the
        mixer is initialized; and a channel is assigned.
        """
        if self.sounds is not None and pg.mixer and self.channel is not None:
            effect_name = next(self.sounds)
            if effect_name is not None:
                effect = SOUNDS[effect_name]
                # Do not attempt to play if the channel is busy.
                if not self.channel.get_busy():
                    self.channel.play(effect, fade_ms=10)

    def set_sprite_index(self, index):
        """
        Sets the sprite to `index` and updates the image accordingly.
        """
        self.image = self.image_tiles[(self.flipped_x, self.flipped_y, index)]
        self.surface = self.image.copy()
        self.rect = self.image.get_rect(center=self.rect.center)
        self.mask = pg.mask.from_surface(self.image)
        self.index = index
        self.rotate(self.orientation)


class BackGround(Sprite):
    """
    Default background sprite. Unlike normal sprites, this one does not rotate.
    """

    _layer = Layer.background

    def update(self):
        pass
