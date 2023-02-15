"""Game functionalities."""
from __future__ import annotations  # TODO: use the typing module
import typing
import enum
from dataclasses import dataclass, field

from tower.utils import create_surface

from pygame import (
    event as pg_event, init as pg_init, display as pg_display, mixer as pg_mixer, font as pg_font,
    KEYDOWN, K_ESCAPE, QUIT, FULLSCREEN, Surface as pg_surface, Rect as pg_rect, time as pg_time, sprite
)

from tower import SCREEN_RECT, DESIRED_FPS, IMAGE_SPRITES
from tower.sprites import Sprite


class Layer(enum.IntEnum):  # TODO: update this
    # TODO: to init?
    """Enum for the game's layers."""
    BACKGROUND = 0
    """Background layer."""
    GROUND = 1
    """Ground layer."""
    TOWER = 2
    """Tower layer."""
    ENEMY = 3
    """Enemy layer."""
    BULLET = 4
    """Bullet layer."""
    UI = 5
    """UI layer."""


class GameState(enum.Enum):
    """
    Enum for the game's state machine. Every state represents ad knowm game state for the game engine.
    """
    UNKNOWN = 'unknown'
    """Unknown state, indicating possible error or misconfiguration."""
    INITIALIZING = 'initializing'
    """The state the game engine would rightly be set to before anything is initialized or configured."""
    INITIALIZED = 'initialized'
    """The game engine is initialized: pygame is configured, the sprite images are loaded, etc."""
    MAP_EDITING = 'map_editing'
    """The game engine is in map editing mode"""
    GAME_PLAYING = 'game_playing'
    """The game engine is in game playing mode"""
    MAIN_MENU = 'main_menu'
    """The game engine is in the main menu"""
    GAME_ENDED = 'game_ended'
    """The game engine is rendering the game ended screen."""
    QUITTING = 'quitting'
    """The game engine is exiting and is unwinding"""


class BackGround(Sprite):
    """
    Default background sprite. Unlike normal sprites, this one does not rotate.
    """

    _layer = Layer.BACKGROUND

    def update(self):
        pass


class StateError(Exception):
    """
    Raised if the game is in an unexpected game state at a point where we expect it to be in a different state.
    For instance, to start the game loop we must be initialized.
    """


class GamEditing:
    pass


@dataclass
class GameLoop:
    """Game main loop.

    Attributes:
        game (TowerGame): The game engine.
    """
    game: TowerGame

    def handle_events(self) -> None:
        """
        Sample event handler that ensures quit events and normal event loop processing takes place. Without this,
        the game will hang, and repaints by the operating system will not happen, causing the game window to hang.
        """
        for event in pg_event.get():
            if event.type == KEYDOWN and event.key == K_ESCAPE or event.type == QUIT:
                self.set_state(GameState.QUITTING)

            # Delegate the event to a sub-event handler `handle_event`
            self.handle_event(event)

    def loop(self) -> None:
        """_summary_
        """
        while self.state != GameState.QUITTING:
            self.handle_events()

    def handle_event(self, event):
        """
        Handles a singular event, `event`.
        """

    # Convenience shortcuts
    def set_state(self, new_state):
        self.game.set_state(new_state)

    @property
    def screen(self):
        return self.game.screen

    @property
    def state(self):
        return self.game.state


@dataclass
class TowerGame:
    """
    Game engine class.

    Attributes:
        screen (pygame.Surface): The game's screen.
        screen_rect (pygame.Rect): The game's screen's rect.
        full_screen (bool): Whether the game is in full screen mode.
        state (GameState): The game's state.
    """

    screen: pg_surface
    screen_rect: pg_rect
    full_screen: bool
    state: GameState
    game_menu: GameLoop = field(init=False, default=None)

    @classmethod  # TODO: how does this method work?
    def create(cls, full_screen: bool = False) -> TowerGame:
        """Creates the game instance.

        Args:
            fullscreen (bool, optional): _description_. Defaults to False.
        """
        game = cls(screen=None, screen_rect=SCREEN_RECT, full_screen=full_screen, state=GameState.INITIALIZING)
        game.initialize()

        return game

    def set_state(self, new_state: GameState) -> None:
        """Sets the game state.

        Args:
            new_state (GameState): Game's current state.
        """
        self.state = new_state

    def assert_state_is(self, *expected_states: typing.List[GameState]) -> None:
        """Asserts that the game engine is one of `expected_states`.

        Args:
            expected_states (list(GameState)): Game's possible states.

        Raises:
            StateError: If  the game engine is not in one of `expected_states`, raise `StateError`.
        """
        if self.state not in expected_states:
            raise StateError(f'Expected state to be {expected_states}, not {self.state}')

    def start_game(self) -> None:
        """Starts the game loop."""
        self.assert_state_is(GameState.INITIALIZED)
        self.set_state(GameState.MAIN_MENU)
        self.loop()

    def loop(self) -> None:
        """Game main loop."""
        while self.state != GameState.QUITTING:
            if self.state == GameState.MAIN_MENU:
                self.game_menu.loop()
            # elif self.state == GameState.map_editing:
            #     # ... etc ...
            #     pass
            # elif self.state == GameState.game_playing:
            #     # ... etc ...
            #     pass
        # self.quit()

    def initialize(self) -> None:
        """Initializes the game engine."""
        self.assert_state_is(GameState.INITIALIZING)
        pg_init()

        window_style = FULLSCREEN if self.full_screen else 0

        # 32 bits of color depth  # TODO: args: mode_ok(size, flags=0, depth=0, display=0) -> depth
        bit_depth = pg_display.mode_ok(self.screen_rect.size, window_style, 32)
        screen = pg_display.set_mode(self.screen_rect.size, window_style, bit_depth)
        self.game_menu = GameMenu(game=self)
        self.set_state(GameState.INITIALIZED)

        pg_mixer.pre_init(
            frequency=44100,
            size=32,
            channels=2,  # 2 means stereo, not the number of channels to use in the mixer
            buffer=512,
        )

        pg_font.init()

        self.screen = screen

        self.set_state(GameState.INITIALIZED)


@dataclass
class GameMenu(GameLoop):

    def loop(self):
        clock = pg_time.Clock()  # TODO: should clock be a constant?
        background = create_surface()
        background.blit(IMAGE_SPRITES[(False, False, "backdrop")], (0, 0))
        group = sprite.Group()
        logo = BackGround.create_from_tile(
            groups=[group],
            index="game_logo",
            orientation=0,
            position=self.game.screen_rect.center,
        )
        rotation = 0
        while self.state == GameState.MAIN_MENU:
            self.handle_events()
            # Repaint background
            self.screen.blit(background, (0, 0))
            rotation += 1
            logo.rotate(rotation % 360)
            # Instruct all sprites to update
            group.update()
            # Tell the group where to draw
            group.draw(self.screen)
            pg_display.flip()
            pg_display.set_caption(f"FPS {round(clock.get_fps())}")
            clock.tick(DESIRED_FPS)
