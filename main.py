"""Game main module.s"""
from tower.game import TowerGame


def start_game():
    """Start the game."""
    game = TowerGame.create()
    game.loop()


if __name__ == '__main__':
    start_game()
