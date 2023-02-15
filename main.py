"""Game main module.s"""
from tower.game import TowerGame


def start_game():
    game = TowerGame.create()
    game.start_game()


if __name__ == '__main__':
    start_game()


# TODO: check this:
# from structlog import get_logger
# import click
# from tower.game import start_game

# log = get_logger()


# @click.group()
# def main():
#     """
#     Entrypoint for the Tower Defense Game from the command line.
#     """


# @main.command(help="Launches the Tower Defense Game")
# def launch():
#     start_game()


# if __name__ == "__main__":
#     main()
