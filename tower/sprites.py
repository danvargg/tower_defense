"""Game sprites."""
from __future__ import annotations  # TODO: choose to keep or use string

from pygame import sprite, mask, transform

from tower import IMAGE_SPRITES


class Sprite(sprite.Sprite):

    @classmethod
    def create_from_file(
            cls,
            index: int,
            groups,
            image_tiles: dict = IMAGE_SPRITES,
            flipped_x: bool = False,
            flipped_y: bool = False,
            **kwargs
    ) -> Sprite:
        """_summary_

        Args:
            index (int): _description_
            groups (_type_): _description_
            image_tiles (dict, optional): _description_. Defaults to IMAGE_SPRITES.
            flipped_x (bool, optional): _description_. Defaults to False.
            flipped_y (bool, optional): _description_. Defaults to False.

        Returns:
            Sprite: _description_
        """
        image = image_tiles[(flipped_x, flipped_y, index)]
        rect = image.get_rect()

        return cls(groups=groups, image_tiles=image_tiles, rect=rect, image=image, **kwargs)

    @classmethod
    def create_from_surface(cls, groups, surface, **kwargs) -> Sprite:
        rect = surface.get_rect()

        return cls(groups=groups, image=surface, index=None, rect=rect, **kwargs)

    def __init__(
        self,
        groups,
        image_tiles=None,
        index=None,
        rect=None,
        image=None,
        orientation=None,
        position=(0, 0),
        flipped_x=False,
        flipped_y=False
    ) -> None:
        super().__init__(groups)
        self.image = image
        self.image_tiles = image_tiles
        self.index = index
        self.rect = rect
        self.orientation = orientation
        self.flipped_x = flipped_x
        self.flipped_y = flipped_y

        if self.image is not None:
            self.mask = mask.from_surface(self.image)
            self.surface = self.image.copy()
            self.rorate(self.orientation)
        if self.rect is not None and position is not None:
            self.move(position)

    def move(self, position, center: bool = True) -> None:
        if center:
            self.rect.center = position
        else:
            self.rect.topleft = position

    def rotate(self, angle: float) -> None:
        """
        Rotates the sprite and regenerates its mask.
        """
        # Do not rotate if the desired angle is the same as the last angle we rotated to.
        if angle == self._last_angle:
            return

        new_image = transform.rotate(self.surface, angle % 360)  # Rotate expects degrees, not radians.
        new_rect = new_image.get_rect(center=self.rect.center)
        self.image = new_image
        self.rect = new_rect
        self.mask = mask.from_surface(self.image)
        self._last_angle = angle

    def set_sprite_index(self, index: int) -> None:
        self.image = self.image_sprites[(self.flipped_x, self.flipped_y, index)]
        self.surface = self.image.copy()
        self.rect = self.image.get_rect(center=self.rect.center)
        self.mask = mask.from_surface(self.image)
        self.index = index
        self.rotate(self.orientation)
