"""Game utilities."""
from importlib import resources  # TODO: confirm types

from pygame import image as pg_image, mixer as pg_mixer


def load(module_path: str, name: str) -> resources.Resource:
    """_summary_

    Args:
        module_path (str): Path to the module.
        name (str): Name of the resource.

    Returns:
        resources.Resource: Resource object.
    """
    return resources.path(module_path, name)


def import_sound(asset_name: str) -> pg_mixer.Sound:
    """Imports, as a sound effect, `asset_name`.

    Args:
        asset_name (str): Asset name.

    Returns:
        pygame.mixer.Sound: Sound effect.
    """
    with load("tower.assets.audio", asset_name) as resource:
        return pg_mixer.Sound(resource)


def import_image(asset_name: str) -> pg_image:
    """Imports, as an image, `asset_name`.

    Args:
        asset_name (str): Asset name.

    Returns:
        pygame.image: Image.
    """
    with load("tower.assets.gfx", asset_name) as resource:
        return pg_image.load(resource).convert_alpha()


def import_level(asset_name: str) -> resources.Resource:
    """Imports as level named `asset_name`.

    Args:
        asset_name (str): Asset name.

    Returns:
        resources.Resource: Resource object.
    """
    with load("tower.assets.levels", asset_name) as resource:
        return resource.open()
