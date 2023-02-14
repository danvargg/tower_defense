"""Game functionalities."""
import typing
from enum import Enum
from dataclasses import dataclass, field

import pygame as pg

from tower import SCREEN_RECT, DESIRED_FPS, IMAGE_SPRITES


class GameState(Enum):
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


class StateError(Exception):
    """
    Raised if the game is in an unexpected game state at a point where we expect it to be in a different state.
    For instance, to start the game loop we must be initialized.
    """


class GamEditing:
    pass


@dataclass
class GameLoop:
    """_summary_

    Attributes:
        game (TowerGame): The game engine.
    """
    game: 'TowerGame'

    def handle_events(self):
        """
        Sample event handler that ensures quit events and normal event loop processing takes place. Without this,
        the game will hang, and repaints by the operating system will not happen, causing the game window to hang.
        """
        for event in pg.event.get():
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE or event.type == pg.QUIT:
                self.set_state(GameState.QUITTING)

            # Delegate the event to a sub-event handler `handle_event`
            self.handle_event(event)

    def loop(self):
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
        screen (pg.Surface): The game's screen.
        screen_rect (pg.Rect): The game's screen's rect.
        full_screen (bool): Whether the game is in full screen mode.
        state (GameState): The game's state.
    """

    screen: pg.Surface
    screen_rect: pg.Rect
    full_screen: bool
    state: GameState
    game_menu: GameLoop = field(init=False, default=None)

    @classmethod  # TODO: how does this method work?
    def create(cls, full_screen: bool = False) -> 'TowerGame':  # TODO: double check this return type
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

    def loop(self):
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

    def initialize(self):
        """Initializes the game engine."""
        self.assert_state_is(GameState.INITIALIZING)
        pg.init()

        window_style = pg.FULLSCREEN if self.full_screen else 0

        # 32 bits of color depth  # TODO: args: mode_ok(size, flags=0, depth=0, display=0) -> depth
        bit_depth = pg.display.mode_ok(self.screen_rect.size, window_style, 32)
        screen = pg.display.set_mode(self.screen_rect.size, window_style, bit_depth)
        self.game_menu = GameMenu(game=self)
        self.set_state(GameState.INITIALIZED)

        pg.mixer.pre_init(
            frequency=44100,
            size=32,
            channels=2,  # 2 means stereo, not the number of channels to use in the mixer
            buffer=512,
        )

        pg.font.init()

        self.screen = screen

        self.set_state(GameState.INITIALIZED)


@dataclass
class GameMenu(GameLoop):
    def loop(self):
        clock = pg.time.Clock()  # TODO: should this be a constant?
        self.screen.blit(IMAGE_SPRITES[(False, False, 'backdrop')], (0, 0))
        while self.state == GameState.MAIN_MENU:
            self.handle_events()
            pg.display.flip()
            pg.display.set_caption(f'FPS: {clock.get_fps()}')
            clock.tick(DESIRED_FPS)
