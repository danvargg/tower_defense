"""Game functionalities."""
from __future__ import annotations  # TODO: use the typing module
import typing  # TODO: should clock be a constant?
import enum
from dataclasses import dataclass, field

from pygame.math import Vector2 as Vector

from tower.utils import create_surface
from tower.sprites import BackGround

from pygame import (
    event as pg_event, init as pg_init, display as pg_display, mixer as pg_mixer, font as pg_font,
    KEYDOWN, K_ESCAPE, QUIT, FULLSCREEN, Surface as pg_surface, Rect as pg_rect, time as pg_time, sprite
)

from tower import SCREEN_RECT, DESIRED_FPS, IMAGE_SPRITES
from tower.sprites import Sprite


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


class StateError(Exception):
    """
    Raised if the game is in an unexpected game state at a point where we expect it to be in a different state.
    For instance, to start the game loop we must be initialized.
    """


class GamEditing:
    pass


@dataclass
class GameLoop:
    """
    Base Game Loop class used by the main TowerGame engine to
    dispatch game states to specialized game loops that inherit from
    this class.

    Takes the source game as its only input.
    """

    game: TowerGame

    @classmethod
    def create(cls, game):
        """
        Create an instance of this game loop with common defaults.
        """
        return cls(game=game)

    @property
    def mouse_position(self):
        return pg.mouse.get_pos()

    def loop(self):
        while self.state != GameState.quitting:
            self.handle_events()

    def handle_events(self):
        """
        Sample event handler that ensures quit events and normal
        event loop processing takes place. Without this, the game will
        hang, and repaints by the operating system will not happen,
        causing the game window to hang.
        """
        for event in pg.event.get():
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                if self.state == GameState.main_menu:
                    self.set_state(GameState.quitting)
                else:
                    self.set_state(GameState.main_menu)
            if event.type == pg.QUIT:
                self.set_state(GameState.quitting)
            # Delegate the event to a sub-event handler `handle_event`
            self.handle_event(event)

    def handle_event(self, event):
        """
        Handles a singular event, `event`.
        """

    # Convenient shortcuts.
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
    Represents the Game Engine and the main entry point for the entire game.

    This is where we track global state that transcends individual game
    states and game play loops, and where we hold references to each
    unique game loop also.

    The `screen` represents the SDL screen surface we draw on. The
    `screen_rect` is the size of the screen.

    The `channels` variable holds a dictionary of known sound channels for the sound mixer.

    The `fullscreen` variable determines if we run the game full screen.

    The `state` variable is the current game state.

    Each of `game_edit`, `game_play`, `game_menu`, and `game_ended`
    represent each unique game loop (and requisite `state`) the game
    engine must loop.
    """

    screen: pg.Surface
    screen_rect: pg.Rect
    channels: dict
    fullscreen: bool
    state: GameState
    game_edit: "GameLoop" = field(init=False, default=None)
    game_play: "GameLoop" = field(init=False, default=None)
    game_menu: "GameLoop" = field(init=False, default=None)
    game_ended: "GameLoop" = field(init=False, default=None)

    @classmethod
    def create(cls, fullscreen=False):
        """
        Creates a TowerGame instance with sensible defaults.
        """

        channels = {
            "footsteps": None,
            "turrets": None,
            "score": None,
        }
        game = cls(
            state=GameState.starting,
            screen=None,
            channels=channels,
            fullscreen=fullscreen,
            # We define our screen rectable to be proportional to the
            # number of tiles and the defined height and width of the
            # tiles we are using.
            screen_rect=SCREENRECT,
        )
        game.init()
        return game

    def set_state(self, next_state: GameState):
        """
        Transitions the game state from one state to another.
        """
        log.debug(
            "Changing Game State", current_state=self.state, next_state=next_state
        )
        self.state = next_state

    def assert_state_is(self, *expected_states: GameState):
        """
        Asserts that the game engine is one of `expected_states`. If that assertions fails, raise `StateError`.
        """
        if self.state not in expected_states:
            raise StateError(
                f"Expected the game state to be one of {expected_states} not {self.state}"
            )

    def loop(self):
        """
        The main game loop that calls out to sub-loops depending on the game state.
        """
        # This is really the most important part of the state
        # machine. Depending on the value of `self.state`, the engine
        # switches to different parts of the game.
        while self.state != GameState.quitting:
            if self.state == GameState.main_menu:
                self.game_menu.loop()
            elif self.state == GameState.map_editing:
                self.game_edit.create_blank_level()
                self.game_edit.loop()
            elif self.state == GameState.game_playing:
                # Attempt to open a level -- by asking the player to
                # select a map with the open dialog -- and if that
                # succeeds, we enter the game play loop. If the player
                # exits, cancels or somehow chooses a level that is
                # not valid, we keep looping.
                if self.game_play.try_open_level():
                    self.game_play.loop()
            elif self.state == GameState.game_ended:
                self.game_ended.loop()
            else:
                assert False, f"Unknown game loop state {self.state}"
        self.quit()

    def quit(self):
        """
        Quits pygame and exits.
        """
        pg.quit()

    def start_game(self):
        """
        Starts the game engine. This is only meant to be called
        once, by whatever entrypoint is used to start the game, and only after the game is initialized.
        """
        self.assert_state_is(GameState.initialized)
        self.set_state(GameState.main_menu)
        self.loop()

    def init(self):
        """
        Initializes the game and configures pygame's SDL engine,
        the sound mixer, loads the images and creates the game state
        loops.
        """
        self.assert_state_is(GameState.starting)
        # Initialize and configure the display and mode for the game
        pg.init()
        # Configures fullscreen or windowed, the color depth (32 bits) and create the screen surface
        window_style = pg.FULLSCREEN if self.fullscreen else 0
        bit_depth = pg.display.mode_ok(self.screen_rect.size, window_style, 32)
        self.screen = pg.display.set_mode(
            self.screen_rect.size, window_style, bit_depth
        )
        # Load the image tiles into the module-level dictionary `IMAGE_SPRITES`
        for sprite_index, sprite_name in SPRITES.items():
            img = import_image(sprite_name)
            # Generate flipped versions of the sprites we load. We
            # want them flipped along the x and/or y-axis.
            for flipped_x in (True, False):
                for flipped_y in (True, False):
                    new_img = pg.transform.flip(img, flip_x=flipped_x, flip_y=flipped_y)
                    IMAGE_SPRITES[(flipped_x, flipped_y, sprite_index)] = new_img

        # Configure the sound mixer.
        pg.mixer.pre_init(
            frequency=44100,
            size=32,
            # N.B.: 2 here means stereo, not the number of channels to use in the mixer
            channels=2,
            buffer=512,
        )
        if pg.mixer.get_init() is None:
            pg.mixer = None
        else:
            # Load the sounds
            for sound_key, sound_name in SOUNDS.items():
                sound = import_sound(sound_name)
                SOUNDS[sound_key] = sound

            # Map the channels and channel names to a dedicated
            # `Channel` object sourced from pygame's sound mixer.
            for channel_id, channel_name in enumerate(self.channels):
                self.channels[channel_name] = pg.mixer.Channel(channel_id)
                # Configure the volume here.
                self.channels[channel_name].set_volume(1.0)
        # Load the font engine.
        pg.font.init()
        # Create the game loop state classes
        self.game_menu = GameMenu.create_with_level(self, level_name="demo.json")
        self.game_edit = GameEdit.create(self)
        self.game_play = GameEdit.create(self)
        self.game_ended = GameEnded.create(self)
        self.set_state(GameState.initialized)


@dataclass
class MenuGroup:

    """
    Menu Group UI class that keeps track of a selection of `Text` sprites.

    The menu group remembers the order in they were added in using a list called `items`.

    The position on the screen is determined by `which_position`, and
    the currently selected and not selected items are tracked with
    `selected_color` and `not_selected_color`.

    The selected item's index in the list is stored in `selected`.
    """

    render_position: Vector = Vector(0, 0)
    selected_color: str = "sienna2"
    not_selected_color: str = "seashell2"
    selected: Optional[int] = 0
    items: List[Text] = field(default_factory=list)

    def set_selected(self, index):
        """
        Sets the selected item to `index`. All menu group items
        are re-rendered and their selected colors changed to match the
        new index.
        """
        for idx, menu_item in enumerate(self.items):
            if idx == index:
                menu_item.color = self.selected_color
                self.selected = idx
            else:
                menu_item.color = self.not_selected_color
            menu_item.render_text()

    def move(self, direction):
        """
        Moves the selection in `direction`, which is either a
        positive or negative number, indicating down or up,
        respectively.
        """
        if self.selected is None:
            self.selected = 0
        self.selected += direction
        self.selected %= len(self.items)
        self.set_selected(self.selected)

    def forward(self):
        """
        Moves the selected menu item forward one position
        """
        self.move(1)

    def backward(self):
        """
        Moves the selected menu item backward one position
        """
        self.move(-1)

    def add_menu_item(self, *menu_items):
        """
        Adds `menu_items` to the end of the menu items list.
        """
        self.items.extend(menu_items)

    def get_menu_item_position(self):
        """
        Calculates a menu item's *center* position on the screen,
        taking into account all the other menu items' font sizes and
        line height spacing.
        """
        offset = Vector(
            0,
            sum(
                menu_item.font.get_height() + menu_item.font.get_linesize()
                for menu_item in self.items
            ),
        )
        return self.render_position + offset

    def clear(self):
        self.items.clear()

    def add(self, text, size, action):
        sprite = Text(
            groups=[],
            color=self.not_selected_color,
            text=text,
            size=size,
            action=action,
        )
        self.add_menu_item(sprite)
        v = self.get_menu_item_position()
        sprite.move(v)
        # Set the selected item to the top-most item.
        self.move(0)

    def execute(self):
        """
        Executes the action associated with the selected menu
        item. Requires that a callable is associated with the menu
        item's `action`.
        """
        assert self.selected is not None, "No menu item is selected"
        menu = self.items[self.selected]
        assert callable(
            menu.action
        ), f"Menu item {menu} does not have a callable action"
        menu.action()


@dataclass
class GameMenu(GameLoop):  # TODO: shoucl clock be a constant?

    """
    Main Menu loop for the game.

    The `menu_group` attribute holds the menu group configuration the
    loop renders to the screen.
    """

    background: pg.Surface
    menu_group: MenuGroup

    @classmethod
    def create(cls, game, background):
        return cls(game=game, background=background, menu_group=MenuGroup())

    def handle_event(self, event):
        # Pass up/down/return events to the menu group
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_UP:
                self.menu_group.backward()
            if event.key == pg.K_DOWN:
                self.menu_group.forward()
            if event.key == pg.K_RETURN:
                self.menu_group.execute()

    def make_text(self, text, color, size, path=None, position=(0, 0), **kwargs):
        """
        Shortcut that creates a `Text` sprite.
        """
        text = Text(
            text=text,
            path=path,
            groups=[],
            size=size,
            color=color,
            **kwargs,
        )
        text.move(position)
        return text

    def action_play(self):
        """
        Menu action for the Play menu item.
        """
        self.set_state(GameState.game_playing)

    def action_edit(self):
        """
        Menu action for the Edit menu item.
        """
        self.set_state(GameState.map_editing)

    def action_quit(self):
        """
        Menu action for the Quit menu item.
        """
        self.set_state(GameState.quitting)

    def loop(self):
        clock = pg.time.Clock()
        # Fill the screen with black color.
        self.screen.fill((0, 0, 0), self.game.screen_rect)
        # This determines where the menu is placed.
        menu_base_position = Vector(self.game.screen_rect.center)
        self.menu_group.render_position = menu_base_position
        self.menu_group.clear()
        self.menu_group.add(
            text="Play",
            size=50,
            action=self.action_play,
        )
        self.menu_group.add(
            text="Edit",
            size=30,
            action=self.action_edit,
        )
        self.menu_group.add(
            text="Quit",
            size=30,
            action=self.action_quit,
        )
        start = Vector(-100, 0)
        stop = menu_base_position + Vector(0, -300)
        menu = pg.sprite.Group(
            Sprite.create_from_sprite("game_logo", groups=[], position=stop),
            self.make_swirling_text(
                text="Make your own",
                color="steelblue",
                size=50,
                start=start,
                stop=stop + Vector(0, -150),
            ),
            self.make_swirling_text(
                text="PRESS ENTER TO PLAY",
                color="red1",
                size=50,
                start=start,
                stop=stop + Vector(0, 150),
            ),
            *self.menu_group.items,
        )
        # Create a semi-transparent backdrop for the menu
        r = self.screen.get_rect()
        r.width = r.width // 3
        r.move(150, 0)
        bg = create_surface(size=r.size)
        bg.fill((0, 0, 0, 128))

        # Loop as long as our game state remains main menu. When an
        # action is triggered by the player, the state is changed,
        # breaking the loop
        while self.state == GameState.main_menu:
            self.screen.blit(self.background, (0, 0))
            # Draw a blended black rectangle to make the menu and text
            # easier to read
            self.screen.blit(bg, r.topright)
            menu.draw(self.screen)
            self.handle_events()
            menu.update()
            pg.display.flip()
            pg.display.set_caption(f"FPS {round(clock.get_fps())}")
            clock.tick(DESIRED_FPS)
        log.info("Exited menu")
